"""Cross-tool archive endpoint for the authenticated Mini App."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...repo import history as history_repo
from ..deps import current_user, get_db, rate_limit

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", dependencies=[Depends(rate_limit("read"))])
async def history(
    limit: int = Query(default=50, ge=1, le=history_repo.MAX_LIMIT),
    user=Depends(current_user),
    db=Depends(get_db),
):
    """Return one owner-scoped archive across all supported product surfaces."""
    return {
        "items": await history_repo.list_history(db, user["tg_id"], limit=limit),
        "limit": limit,
    }
