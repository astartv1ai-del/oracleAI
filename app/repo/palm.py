from __future__ import annotations

import json

from ..data.session import transaction, utcnow


async def save_reading(db, tg_id: int, analysis: dict, *, image_sha256: str,
                       image_size: int, hand_side: str = "unknown",
                       status: str = "complete", surface: str = "miniapp") -> int:
    now = utcnow()
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO palm_readings(tg_id, status, hand_side, image_sha256, "
            "image_size, analysis_json, surface, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (tg_id, status, hand_side, image_sha256, image_size,
             json.dumps(analysis, ensure_ascii=False), surface, now, now),
        )
        return cur.lastrowid


async def get_reading(db, reading_id: int, tg_id: int):
    cur = await db.execute(
        "SELECT * FROM palm_readings WHERE id=? AND tg_id=? AND deleted_at IS NULL",
        (reading_id, tg_id),
    )
    return await cur.fetchone()


async def latest_reading(db, tg_id: int):
    cur = await db.execute(
        "SELECT * FROM palm_readings WHERE tg_id=? AND deleted_at IS NULL "
        "ORDER BY id DESC LIMIT 1",
        (tg_id,),
    )
    return await cur.fetchone()


async def list_readings(db, tg_id: int, limit: int = 20) -> list[dict]:
    limit = max(1, min(int(limit or 20), 50))
    cur = await db.execute(
        "SELECT id, status, hand_side, image_size, created_at, updated_at "
        "FROM palm_readings WHERE tg_id=? AND deleted_at IS NULL "
        "ORDER BY id DESC LIMIT ?",
        (tg_id, limit),
    )
    return [dict(row) for row in await cur.fetchall()]


async def decode_row(row) -> dict | None:
    if not row or row["status"] != "complete":
        return None
    try:
        data = json.loads(row["analysis_json"] or "{}")
    except (TypeError, ValueError):
        data = {}
    data["id"] = row["id"]
    data["status"] = row["status"]
    data["created_at"] = row["created_at"]
    data["hand_side"] = row["hand_side"] or data.get("hand_side", "unknown")
    return data


async def delete_reading(db, reading_id: int, tg_id: int) -> bool:
    async with transaction(db):
        cur = await db.execute(
            "UPDATE palm_readings SET status='deleted', hand_side='unknown', "
            "image_sha256=NULL, image_size=NULL, analysis_json=NULL, "
            "deleted_at=?, updated_at=? "
            "WHERE id=? AND tg_id=? AND deleted_at IS NULL",
            (utcnow(), utcnow(), reading_id, tg_id),
        )
    return bool(cur.rowcount)
