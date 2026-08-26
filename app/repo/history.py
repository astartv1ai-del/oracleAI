"""Unified, privacy-safe history read model across OracleAI surfaces.

The product stores each surface in its own domain table. This module deliberately
keeps those write models independent and exposes one small read model for the
Mini App archive. It contains labels and action metadata, never message bodies,
report bodies, card answers, birth data, or internal embedding payloads.
"""
from __future__ import annotations

from typing import Any

MAX_LIMIT = 100


def _limit(value: int) -> int:
    return min(MAX_LIMIT, max(1, int(value)))


async def list_history(db, tg_id: int, *, limit: int = 50) -> list[dict[str, Any]]:
    """Return newest owner-scoped items with stable client actions.

    `evidence_id` is the source row ID for surfaces that have an immutable or
    inspectable artifact. Chat sessions intentionally expose no evidence ID:
    their content remains behind the authenticated session endpoint.
    """
    size = _limit(limit)
    cur = await db.execute(
        """
        SELECT kind, item_id, title, created_at, status, evidence_id,
               action, action_kind, action_id
        FROM (
            SELECT 'report' AS kind, id AS item_id,
                   COALESCE(title, 'Разбор') AS title, created_at,
                   'ready' AS status, id AS evidence_id,
                   'report' AS action, kind AS action_kind, id AS action_id
            FROM reports
            WHERE tg_id=?

            UNION ALL

            SELECT 'tarot' AS kind, id AS item_id,
                   COALESCE(NULLIF(question, ''), 'Расклад') AS title,
                   created_at, CASE WHEN COALESCE(answer, '')<>''
                                    THEN 'ready' ELSE 'pending' END AS status,
                   id AS evidence_id, 'reading' AS action,
                   spread AS action_kind, id AS action_id
            FROM tarot_readings
            WHERE tg_id=?

            UNION ALL

            SELECT 'palm' AS kind, id AS item_id,
                   'Сканер ладони' AS title, created_at, status,
                   id AS evidence_id, 'palm' AS action,
                   status AS action_kind, id AS action_id
            FROM palm_readings
            WHERE tg_id=? AND deleted_at IS NULL

            UNION ALL

            SELECT 'chat' AS kind, id AS item_id,
                   COALESCE(NULLIF(title, ''), 'Разговор') AS title,
                   COALESCE(last_at, created_at) AS created_at,
                   CASE WHEN archived=1 THEN 'archived' ELSE 'active' END AS status,
                   NULL AS evidence_id, 'chat' AS action,
                   agent AS action_kind, id AS action_id
            FROM threads
            WHERE tg_id=? AND msg_count > 0
        )
        ORDER BY created_at DESC, item_id DESC
        LIMIT ?
        """,
        (tg_id, tg_id, tg_id, tg_id, size),
    )
    rows = await cur.fetchall()
    return [
        {
            "kind": row["kind"],
            "item_id": row["item_id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "status": row["status"],
            "evidence_id": row["evidence_id"],
            "action": {
                "type": row["action"],
                "kind": row["action_kind"],
                "id": row["action_id"],
            },
            "deep_link": f"app://{row['action']}/{row['action_kind']}/{row['action_id']}",
            "deletion": "archive" if row["kind"] == "chat" else "delete" if row["kind"] == "palm" else "not_supported",
        }
        for row in rows
    ]
