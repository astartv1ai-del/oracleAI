"""Расклады Таро, партнёры и синастрия, отчёты, прогнозы дня, практики."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from ..data.session import transaction, utcnow

# ─────────────────────────────── Таро ─────────────────────────────────────────


async def start_reading(db, tg_id: int, spread: str, question: str, cards: list,
                        *, surface: str = "bot", paid_with: str = "daily") -> int:
    """Кладёт расклад без трактовки и отдаёт id.

    Разделение на два шага нужно клиенту: Mini App сначала показывает анимацию
    переворота карт, и только потом просит трактовку. Карты при этом уже лежат в
    БД — подменить их запросом с клиента нельзя.
    """
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO tarot_readings(tg_id, spread, question, cards_json, answer, "
            "surface, paid_with, created_at) VALUES(?,?,?,?,'',?,?,?)",
            (tg_id, spread, question, json.dumps(cards, ensure_ascii=False),
             surface, paid_with, utcnow()))
        reading_id = cur.lastrowid
    return reading_id


async def save_reading(db, tg_id: int, spread: str, question: str, cards: list,
                       answer: str, *, surface: str = "bot",
                       paid_with: str = "daily") -> int:
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO tarot_readings(tg_id, spread, question, cards_json, answer, "
            "surface, paid_with, created_at) VALUES(?,?,?,?,?,?,?,?)",
            (tg_id, spread, question, json.dumps(cards, ensure_ascii=False), answer,
             surface, paid_with, utcnow()))
        reading_id = cur.lastrowid
    return reading_id


async def get_reading(db, reading_id: int, tg_id: int):
    cur = await db.execute(
        "SELECT * FROM tarot_readings WHERE id=? AND tg_id=?", (reading_id, tg_id))
    return await cur.fetchone()


async def finish_reading(db, reading_id: int, answer: str) -> None:
    async with transaction(db):
        await db.execute("UPDATE tarot_readings SET answer=? WHERE id=?",
                         (answer, reading_id))


async def set_outcome(db, reading_id: int, tg_id: int, outcome: str) -> bool:
    """Отметка клиентки «сбылось / частично / нет» — обратная связь и доказательство."""
    if outcome not in ("came_true", "partly", "no"):
        return False
    async with transaction(db):
        cur = await db.execute(
            "UPDATE tarot_readings SET outcome=?, outcome_at=? WHERE id=? AND tg_id=?",
            (outcome, utcnow(), reading_id, tg_id))
    return bool(cur.rowcount)


async def recent_readings(db, tg_id: int, limit: int = 20) -> list[dict]:
    cur = await db.execute(
        "SELECT id, spread, question, cards_json, answer, outcome, created_at "
        "FROM tarot_readings WHERE tg_id=? AND answer<>'' ORDER BY id DESC LIMIT ?",
        (tg_id, limit))
    return [{"id": r["id"], "spread": r["spread"], "question": r["question"],
             "answer": r["answer"], "outcome": r["outcome"],
             "created_at": r["created_at"],
             "cards": json.loads(r["cards_json"] or "[]")}
            for r in await cur.fetchall()]


async def readings_count_since(db, tg_id: int, days: int) -> int:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cur = await db.execute(
        "SELECT COUNT(*) c FROM tarot_readings WHERE tg_id=? AND created_at>=?",
        (tg_id, since))
    return (await cur.fetchone())["c"]


async def outcome_stats(db, tg_id: int) -> dict:
    """Сводка отметок «сбылось»: доказательство ценности без схемы БД.

    Агрегат по уже существующей колонке `outcome` — никаких миграций.
    """
    cur = await db.execute(
        "SELECT outcome, COUNT(*) c FROM tarot_readings "
        "WHERE tg_id=? AND outcome IS NOT NULL GROUP BY outcome", (tg_id,))
    stats = {"came_true": 0, "partly": 0, "no": 0}
    for r in await cur.fetchall():
        if r["outcome"] in stats:
            stats[r["outcome"]] = r["c"]
    cur = await db.execute(
        "SELECT COUNT(*) c FROM tarot_readings "
        "WHERE tg_id=? AND outcome IS NOT NULL", (tg_id,))
    stats["marked"] = (await cur.fetchone())["c"]
    return stats


# ───────────────────────── партнёры и синастрия ───────────────────────────────

async def add_partner(db, tg_id: int, name: str, birth_date: str, *,
                      relation: str = "partner", birth_time: str | None = None,
                      birth_city: str | None = None, lat: float | None = None,
                      lon: float | None = None, tz: str | None = None,
                      chart: dict | None = None) -> int:
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO partners(tg_id, name, relation, birth_date, birth_time, "
            "birth_city, birth_lat, birth_lon, tz, chart_json, created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (tg_id, name, relation, birth_date, birth_time, birth_city, lat, lon, tz,
             json.dumps(chart, ensure_ascii=False) if chart else None, utcnow()))
        partner_id = cur.lastrowid
    return partner_id


async def list_partners(db, tg_id: int) -> list[dict]:
    cur = await db.execute(
        "SELECT id, name, relation, birth_date, birth_city FROM partners "
        "WHERE tg_id=? ORDER BY id DESC", (tg_id,))
    return [dict(r) for r in await cur.fetchall()]


async def get_partner(db, partner_id: int, tg_id: int):
    cur = await db.execute("SELECT * FROM partners WHERE id=? AND tg_id=?",
                           (partner_id, tg_id))
    return await cur.fetchone()


async def find_partner_by_date(db, tg_id: int, birth_date: str):
    """Сохранённый человек с этой датой рождения — чтобы взять его карту."""
    cur = await db.execute(
        "SELECT * FROM partners WHERE tg_id=? AND birth_date=? "
        "ORDER BY id DESC LIMIT 1", (tg_id, birth_date))
    return await cur.fetchone()


async def delete_partner(db, partner_id: int, tg_id: int) -> None:
    async with transaction(db):
        await db.execute("DELETE FROM partners WHERE id=? AND tg_id=?",
                         (partner_id, tg_id))


async def cache_synastry(db, tg_id: int, partner_key: str, score: int,
                         breakdown: dict, answer: str = "") -> None:
    """Кеш разбора пары: генерация дорогая, а пара за день не меняется."""
    async with transaction(db):
        await db.execute("DELETE FROM synastry_cache WHERE tg_id=? AND partner_key=?",
                         (tg_id, partner_key))
        await db.execute(
            "INSERT INTO synastry_cache(tg_id, partner_key, score, breakdown_json, "
            "answer, created_at) VALUES(?,?,?,?,?,?)",
            (tg_id, partner_key, score, json.dumps(breakdown, ensure_ascii=False),
             answer, utcnow()))


async def get_synastry(db, tg_id: int, partner_key: str):
    cur = await db.execute(
        "SELECT * FROM synastry_cache WHERE tg_id=? AND partner_key=? "
        "ORDER BY id DESC LIMIT 1", (tg_id, partner_key))
    return await cur.fetchone()


# ─────────────────────────── прогнозы и отчёты ───────────────────────────────

async def get_forecast(db, tg_id: int, day: str, *, lang: str = "ru") -> str | None:
    """Возвращает прогноз только на запрошенном языке.

    У старых строк ``lang`` после миграции равен ``ru``. Когда пользователь меняет
    язык, несовпадающая запись не выдаётся — прогноз будет пересобран в новой
    локали и перезапишет персональный дневной кэш.
    """
    cur = await db.execute(
        "SELECT text FROM forecasts WHERE tg_id=? AND day=? AND lang=?",
        (tg_id, day, lang))
    row = await cur.fetchone()
    return row["text"] if row else None


async def save_forecast(db, tg_id: int, day: str, text: str, *, lang: str = "ru") -> None:
    async with transaction(db):
        await db.execute(
            "INSERT OR REPLACE INTO forecasts(tg_id, day, text, lang, created_at) "
            "VALUES(?,?,?,?,?)", (tg_id, day, text, lang, utcnow()))


async def save_report(db, tg_id: int, kind: str, title: str, body: str, *,
                      period: str | None = None, meta: dict | None = None) -> None:
    async with transaction(db):
        await db.execute(
            "INSERT OR REPLACE INTO reports(tg_id, kind, period, title, body, "
            "meta_json, created_at) VALUES(?,?,?,?,?,?,?)",
            (tg_id, kind, period, title, body,
             json.dumps(meta, ensure_ascii=False) if meta else None, utcnow()))


async def get_report(db, tg_id: int, kind: str, period: str | None = None):
    cur = await db.execute(
        "SELECT * FROM reports WHERE tg_id=? AND kind=? AND COALESCE(period,'')=? "
        "ORDER BY id DESC LIMIT 1", (tg_id, kind, period or ""))
    return await cur.fetchone()


async def list_reports(db, tg_id: int) -> list[dict]:
    cur = await db.execute(
        "SELECT id, kind, period, title, created_at FROM reports WHERE tg_id=? "
        "ORDER BY id DESC LIMIT 50", (tg_id,))
    return [dict(r) for r in await cur.fetchall()]


# ──────────────────────────────── практики ───────────────────────────────────

async def start_practice(db, tg_id: int, code: str) -> int:
    """Начинает практику. Повторный старт возвращает уже идущую — программа одна."""
    cur = await db.execute(
        "SELECT id FROM practices WHERE tg_id=? AND code=? AND finished_at IS NULL",
        (tg_id, code))
    row = await cur.fetchone()
    if row:
        return row["id"]
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO practices(tg_id, code, started_at) VALUES(?,?,?)",
            (tg_id, code, utcnow()))
        practice_id = cur.lastrowid
    return practice_id


async def active_practice(db, tg_id: int, code: str):
    cur = await db.execute(
        "SELECT * FROM practices WHERE tg_id=? AND code=? AND finished_at IS NULL "
        "ORDER BY id DESC LIMIT 1", (tg_id, code))
    return await cur.fetchone()


async def stop_practice(db, tg_id: int, code: str) -> bool:
    """Завершает программу досрочно. История дней остаётся."""
    async with transaction(db):
        cur = await db.execute(
            "UPDATE practices SET finished_at=? WHERE tg_id=? AND code=? "
            "AND finished_at IS NULL", (utcnow(), tg_id, code))
    return bool(cur.rowcount)


async def mark_practice_done(db, tg_id: int, code: str, *,
                             total_days: int | None = None,
                             tz_today: str | None = None) -> dict:
    """Отмечает день практики.

    Повторная отметка за сутки стрик не двигает: практика — это день, а не
    количество нажатий. День считаем по таймзоне клиентки (`tz_today`), иначе
    для Владивостока «сегодня» наступало бы на сутки позже серверного.

    Когда пройдено `total_days`, программа закрывается: без этого стрик рос
    бесконечно и «21 день» ничего не значил.
    """
    row = await active_practice(db, tg_id, code)
    if not row:
        await start_practice(db, tg_id, code)
        row = await active_practice(db, tg_id, code)

    today = tz_today or datetime.now(timezone.utc).date().isoformat()
    last = (row["last_done"] or "")[:10]
    if last == today:
        return {"day_index": row["day_index"], "streak": row["streak"],
                "already": True, "finished": False}

    yesterday = (datetime.fromisoformat(today).date() - timedelta(days=1)).isoformat()
    streak = (row["streak"] or 0) + 1 if last == yesterday else 1
    day_index = (row["day_index"] or 0) + 1
    finished = bool(total_days and day_index >= total_days)

    async with transaction(db):
        await db.execute(
            "UPDATE practices SET day_index=?, streak=?, last_done=?, finished_at=? "
            "WHERE id=?",
            (day_index, streak, today, utcnow() if finished else None, row["id"]))
    return {"day_index": day_index, "streak": streak, "already": False,
            "finished": finished}


async def list_practices(db, tg_id: int, *, active_only: bool = False) -> list[dict]:
    sql = "SELECT * FROM practices WHERE tg_id=?"
    if active_only:
        sql += " AND finished_at IS NULL"
    sql += " ORDER BY id DESC LIMIT 40"
    cur = await db.execute(sql, (tg_id,))
    return [dict(r) for r in await cur.fetchall()]


async def practice_reminder_targets(db, today: str) -> list[dict]:
    """Идущие практики, которые сегодня ещё не отмечены — для напоминаний."""
    cur = await db.execute(
        "SELECT p.tg_id, p.code, p.day_index, p.streak FROM practices p "
        "JOIN users u ON u.tg_id = p.tg_id "
        "WHERE p.finished_at IS NULL AND u.status='active' AND u.morning_push=1 "
        "AND COALESCE(substr(p.last_done,1,10),'') <> ?", (today,))
    return [dict(r) for r in await cur.fetchall()]
