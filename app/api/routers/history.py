"""Unified, owner-scoped archive read model for all reflective surfaces."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..deps import current_user, get_db
from ...repo import dialog, readings

router = APIRouter(prefix="/api", tags=["history"])


def _entry(kind: str, entry_id: int, title: str, created_at: str | None,
           *, preview: str = "", deep_link: str = "") -> dict:
    return {
        "kind": kind,
        "entry_id": int(entry_id),
        "source_id": f"{kind}:{int(entry_id)}",
        "title": title,
        "created_at": created_at,
        "preview": (preview or "")[:160],
        "deep_link": deep_link,
        "deletion": "use the source surface to delete or archive this item",
    }


@router.get("/history")
async def unified_history(
    limit: int = Query(default=30, ge=1, le=100),
    user=Depends(current_user),
    db=Depends(get_db),
):
    """Return a normalized archive without crossing the authenticated owner scope.

    Entries deliberately expose previews only for the authenticated owner and do
    not include memory facts, full diary text, birth data or raw report bodies.
    Deletion remains owned by each source surface so one archive read cannot
    accidentally broaden destructive permissions.
    """
    tg_id = int(user["tg_id"])
    entries: list[dict] = []

    for item in await readings.list_reports(db, tg_id):
        record = _entry(
            "report", item["id"], item.get("title") or item.get("kind") or "Report",
            item.get("created_at"),
            deep_link=f"/api/reports/{item['kind']}?report_id={item['id']}",
        )
        record["source_kind"] = item.get("kind") or "report"
        entries.append(record)

    for item in await readings.recent_readings(db, tg_id, limit=limit):
        cards = item.get("cards") or []
        card_names = ", ".join(str(card.get("name", "")) for card in cards[:3] if isinstance(card, dict))
        entries.append(_entry(
            "tarot", item["id"], item.get("spread") or "Tarot reading",
            item.get("created_at"), preview=card_names,
            deep_link=f"/api/tarot/history/{item['id']}",
        ))

    for item in await dialog.list_threads(db, tg_id, limit=limit):
        if item.get("archived"):
            continue
        record = _entry(
            "chat", item["id"], item.get("title") or item.get("agent") or "Conversation",
            item.get("last_at") or item.get("created_at"),
            preview=item.get("last_text") or "",
            deep_link=f"/api/chat/{item['agent']}/sessions/{item['id']}",
        )
        record["source_kind"] = item.get("agent") or "oracle"
        entries.append(record)

    cur = await db.execute(
        "SELECT id, created_at FROM diary WHERE tg_id=? ORDER BY id DESC LIMIT ?",
        (tg_id, limit),
    )
    for row in await cur.fetchall():
        item = dict(row)
        entries.append(_entry(
            "diary", item["id"], "Diary entry", item.get("created_at"),
            deep_link=f"/api/diary/{item['id']}",
        ))

    entries.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return {
        "items": entries[:limit],
        "limit": limit,
        "owner_scoped": True,
        "raw_content_included": False,
    }
