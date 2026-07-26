"""Контент и конфигурация, управляемые из админки: настройки, тексты, флаги.

Всё, что здесь лежит, правится без деплоя — это требование ТЗ («все тексты и
промпты в конфигах, не в коде»). Код всегда имеет значение по умолчанию, а БД
его перекрывает: пустая база и упавший запрос не должны ломать продукт.
"""
from __future__ import annotations

import json
import zlib

from ..data.session import transaction, utcnow

# ─────────────────────────────── настройки ────────────────────────────────────


async def get_setting(db, key: str, default=None):
    cur = await db.execute("SELECT value_json FROM settings WHERE key=?", (key,))
    row = await cur.fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value_json"])
    except (TypeError, ValueError):
        return default


async def set_setting(db, key: str, value, admin_id: int | None = None) -> None:
    async with transaction(db):
        await db.execute(
            "INSERT OR REPLACE INTO settings(key, value_json, updated_at, updated_by) "
            "VALUES(?,?,?,?)",
            (key, json.dumps(value, ensure_ascii=False), utcnow(), admin_id))


async def all_settings(db) -> dict:
    cur = await db.execute("SELECT key, value_json FROM settings ORDER BY key")
    out = {}
    for row in await cur.fetchall():
        try:
            out[row["key"]] = json.loads(row["value_json"])
        except (TypeError, ValueError):
            out[row["key"]] = None
    return out


# ─────────────────────────── тексты и промпты ─────────────────────────────────

async def get_content(db, kind: str, code: str) -> dict | None:
    cur = await db.execute(
        "SELECT * FROM content_items WHERE kind=? AND code=? AND is_active=1",
        (kind, code))
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_text(db, kind: str, code: str, default: str = "") -> str:
    item = await get_content(db, kind, code)
    return (item or {}).get("body") or default


async def list_content(db, kind: str | None = None, *,
                       active_only: bool = False) -> list[dict]:
    sql = ["SELECT * FROM content_items WHERE 1=1"]
    params: list = []
    if kind:
        sql.append("AND kind=?")
        params.append(kind)
    if active_only:
        sql.append("AND is_active=1")
    sql.append("ORDER BY kind, sort, code")
    cur = await db.execute(" ".join(sql), params)
    return [dict(r) for r in await cur.fetchall()]


async def upsert_content(db, kind: str, code: str, *, title: str | None = None,
                         body: str | None = None, meta: dict | None = None,
                         is_active: int | None = None, sort: int | None = None,
                         admin_id: int | None = None) -> None:
    async with transaction(db):
        await db.execute(
            "INSERT OR IGNORE INTO content_items(kind, code, title, body, is_active, "
            "sort, created_at, updated_at) VALUES(?,?,?,?,1,100,?,?)",
            (kind, code, title or code, body or "", utcnow(), utcnow()))
        fields: dict = {}
        if title is not None:
            fields["title"] = title
        if body is not None:
            fields["body"] = body
        if meta is not None:
            fields["meta_json"] = json.dumps(meta, ensure_ascii=False)
        if is_active is not None:
            fields["is_active"] = int(is_active)
        if sort is not None:
            fields["sort"] = sort
        if fields:
            keys = ", ".join(f"{k}=?" for k in fields)
            await db.execute(
                f"UPDATE content_items SET {keys}, updated_at=?, updated_by=? "
                f"WHERE kind=? AND code=?",
                (*fields.values(), utcnow(), admin_id, kind, code))


async def delete_content(db, kind: str, code: str) -> None:
    async with transaction(db):
        await db.execute("DELETE FROM content_items WHERE kind=? AND code=?",
                         (kind, code))


def content_meta(item: dict | None) -> dict:
    if not item:
        return {}
    try:
        return json.loads(item.get("meta_json") or "{}")
    except (TypeError, ValueError):
        return {}


# ─────────────────────────────── фиче-флаги ───────────────────────────────────

async def flag_row(db, code: str):
    cur = await db.execute("SELECT * FROM feature_flags WHERE code=?", (code,))
    return await cur.fetchone()


async def is_on(db, code: str, tg_id: int | None = None, *,
                default: bool = False) -> bool:
    """Включена ли фича. При `rollout_pct < 100` — стабильный процент аудитории.

    Попадание в процент считается от хеша (код фичи + id), а не от случайного
    числа: иначе одна и та же клиентка при каждом запросе то видела бы фичу, то
    нет, и это выглядело бы как поломка.
    """
    row = await flag_row(db, code)
    if row is None:
        return default
    if not row["is_on"]:
        return False
    pct = row["rollout_pct"] if row["rollout_pct"] is not None else 100
    if pct >= 100 or tg_id is None:
        return True          # без id раскатку не посчитать — считаем включённой
    bucket = zlib.crc32(f"{code}:{tg_id}".encode()) % 100
    return bucket < pct


async def list_flags(db) -> list[dict]:
    cur = await db.execute("SELECT * FROM feature_flags ORDER BY code")
    return [dict(r) for r in await cur.fetchall()]


async def set_flag(db, code: str, *, is_on: bool | None = None,
                   rollout_pct: int | None = None, description: str | None = None,
                   admin_id: int | None = None) -> None:
    async with transaction(db):
        await db.execute(
            "INSERT OR IGNORE INTO feature_flags(code, is_on, rollout_pct, updated_at) "
            "VALUES(?,0,100,?)", (code, utcnow()))
        fields: dict = {}
        if is_on is not None:
            fields["is_on"] = int(is_on)
        if rollout_pct is not None:
            fields["rollout_pct"] = max(0, min(100, int(rollout_pct)))
        if description is not None:
            fields["description"] = description
        if fields:
            keys = ", ".join(f"{k}=?" for k in fields)
            await db.execute(
                f"UPDATE feature_flags SET {keys}, updated_at=?, updated_by=? "
                f"WHERE code=?", (*fields.values(), utcnow(), admin_id, code))
