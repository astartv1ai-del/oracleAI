"""Таро: каталог раскладов, раздача, трактовка, история, отметка «сбылось»."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...repo import readings
from ...services import catalog
from ...services import chat as chat_svc
from ..deps import current_user, get_db, rate_limit
from .chat import _deny

router = APIRouter(prefix="/api/tarot", tags=["tarot"])


@router.get("/spreads")
async def spreads(user=Depends(current_user), db=Depends(get_db)):
    """Витрина раскладов: что входит в тариф, что куплено, что стоит денег."""
    return await catalog.spread_list(db, user)


@router.post("/draw", dependencies=[Depends(rate_limit("write"))])
async def draw(spread: str = Query(default="three"), user=Depends(current_user),
               db=Depends(get_db)):
    """Тянет карты. Трактовка — вторым запросом, после анимации переворота."""
    try:
        return await chat_svc.draw(db, user, spread, surface="miniapp")
    except chat_svc.ChatDenied as e:
        raise _deny(e.verdict) from e


@router.post("/interpret/{reading_id}", dependencies=[Depends(rate_limit("llm"))])
async def interpret(reading_id: int, user=Depends(current_user), db=Depends(get_db)):
    try:
        answer = await chat_svc.interpret(db, user, reading_id, surface="miniapp")
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    return {"answer": answer}


@router.get("/history")
async def history(user=Depends(current_user), db=Depends(get_db)):
    return await readings.recent_readings(db, user["tg_id"], limit=30)


class OutcomeIn(BaseModel):
    outcome: str          # came_true | partly | no


@router.post("/outcome/{reading_id}", dependencies=[Depends(rate_limit("write"))])
async def set_outcome(reading_id: int, item: OutcomeIn, user=Depends(current_user),
                      db=Depends(get_db)):
    """Отметка «сбылось». Это и обратная связь, и доказательство ценности."""
    if not await readings.set_outcome(db, reading_id, user["tg_id"], item.outcome):
        raise HTTPException(400, "не удалось отметить расклад")
    return {"ok": True}
