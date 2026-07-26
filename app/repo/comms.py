"""Исходящие коммуникации: журнал доставок и рассылки.

`deliveries` — защита от повторной отправки. Планировщик раньше держал отметки
об отправленном в множестве внутри процесса, поэтому после каждого рестарта
утренний прогноз уходил клиентке второй раз. Отметка в БД живёт дольше процесса.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from ..data.session import transaction, utcnow

# ─────────────────────────── журнал доставок ─────────────────────────────────


async def already_sent(db, tg_id: int, kind: str, key: str) -> bool:
    cur = await db.execute(
        "SELECT 1 FROM deliveries WHERE tg_id=? AND kind=? AND key=?",
        (tg_id, kind, key))
    return await cur.fetchone() is not None


async def mark_sent(db, tg_id: int, kind: str, key: str) -> bool:
    """Ставит отметку. False — отметка уже была (кто-то отправил параллельно)."""
    async with transaction(db):
        cur = await db.execute(
            "INSERT OR IGNORE INTO deliveries(tg_id, kind, key, created_at) "
            "VALUES(?,?,?,?)", (tg_id, kind, key, utcnow()))
        return bool(cur.rowcount)


async def claim(db, tg_id: int, kind: str, key: str) -> bool:
    """Атомарно занимает право на отправку: True — отправляем, False — уже ушло.

    Отметка ставится ДО отправки. Дубль в мессенджере клиентка воспринимает как
    сбой продукта, а не пришедший прогноз — как «сегодня тихо»; поэтому из двух
    рисков выбираем пропуск, а не повтор.
    """
    return await mark_sent(db, tg_id, kind, key)


async def unclaim(db, tg_id: int, kind: str, key: str) -> None:
    """Снимает отметку — если отправка сорвалась по временной причине."""
    async with transaction(db):
        await db.execute("DELETE FROM deliveries WHERE tg_id=? AND kind=? AND key=?",
                         (tg_id, kind, key))


async def prune(db, days: int = 120) -> int:
    """Журнал нужен только пока актуален повод — старое удаляем."""
    before = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    async with transaction(db):
        cur = await db.execute("DELETE FROM deliveries WHERE created_at < ?", (before,))
        return cur.rowcount or 0


# ─────────────────────────────── рассылки ─────────────────────────────────────

async def create_broadcast(db, title: str, body: str, *, segment: str = "all",
                           button_text: str | None = None,
                           button_url: str | None = None,
                           scheduled_at: str | None = None,
                           created_by: int | None = None) -> int:
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO broadcasts(title, body, button_text, button_url, segment_json, "
            "status, scheduled_at, created_by, created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (title, body, button_text, button_url,
             json.dumps({"segment": segment}, ensure_ascii=False),
             "scheduled" if scheduled_at else "draft", scheduled_at,
             created_by, utcnow()))
        return cur.lastrowid


async def get_broadcast(db, broadcast_id: int):
    cur = await db.execute("SELECT * FROM broadcasts WHERE id=?", (broadcast_id,))
    return await cur.fetchone()


async def list_broadcasts(db, limit: int = 50) -> list[dict]:
    cur = await db.execute(
        "SELECT * FROM broadcasts ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in await cur.fetchall()]


async def set_broadcast_status(db, broadcast_id: int, status: str, **fields) -> None:
    allowed = {"total", "sent", "failed", "started_at", "finished_at", "scheduled_at"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    keys = "".join(f", {k}=?" for k in fields)
    async with transaction(db):
        await db.execute(
            f"UPDATE broadcasts SET status=?{keys} WHERE id=?",
            (status, *fields.values(), broadcast_id))


async def enqueue_targets(db, broadcast_id: int, ids: list[int]) -> int:
    if not ids:
        return 0
    async with transaction(db):
        await db.executemany(
            "INSERT OR IGNORE INTO broadcast_targets(broadcast_id, tg_id, status) "
            "VALUES(?,?,'pending')", [(broadcast_id, uid) for uid in ids])
        await db.execute("UPDATE broadcasts SET total=? WHERE id=?",
                         (len(ids), broadcast_id))
    return len(ids)


async def next_targets(db, broadcast_id: int, limit: int = 100) -> list[int]:
    cur = await db.execute(
        "SELECT tg_id FROM broadcast_targets WHERE broadcast_id=? AND status='pending' "
        "LIMIT ?", (broadcast_id, limit))
    return [r["tg_id"] for r in await cur.fetchall()]


async def mark_target(db, broadcast_id: int, tg_id: int, status: str,
                      error: str | None = None) -> None:
    async with transaction(db):
        await db.execute(
            "UPDATE broadcast_targets SET status=?, error=?, sent_at=? "
            "WHERE broadcast_id=? AND tg_id=?",
            (status, error, utcnow(), broadcast_id, tg_id))
        column = "sent" if status == "sent" else "failed"
        await db.execute(
            f"UPDATE broadcasts SET {column} = COALESCE({column},0) + 1 WHERE id=?",
            (broadcast_id,))


async def broadcast_progress(db, broadcast_id: int) -> dict:
    cur = await db.execute(
        "SELECT status, COUNT(*) n FROM broadcast_targets WHERE broadcast_id=? "
        "GROUP BY status", (broadcast_id,))
    rows = {r["status"]: r["n"] for r in await cur.fetchall()}
    return {"pending": rows.get("pending", 0), "sent": rows.get("sent", 0),
            "failed": rows.get("failed", 0), "skipped": rows.get("skipped", 0)}


async def due_broadcasts(db) -> list[dict]:
    """Рассылки, которым пора уйти (запланированные и незавершённые running)."""
    cur = await db.execute(
        "SELECT * FROM broadcasts WHERE (status='scheduled' AND scheduled_at<=?) "
        "OR status='running' ORDER BY id", (utcnow(),))
    return [dict(r) for r in await cur.fetchall()]
