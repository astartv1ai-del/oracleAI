"""Таро: каталог раскладов, раздача, трактовка, история, отметка «сбылось»."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core import tarot
from ...repo import readings
from ...services import catalog
from ...services import chat as chat_svc
from ..common.errors import access_denied
from ..deps import current_user, get_db, rate_limit

router = APIRouter(prefix="/api/tarot", tags=["tarot"])


@router.get("/spreads")
async def spreads(deck_id: str | None = Query(default=None),
                  user=Depends(current_user), db=Depends(get_db)):
    """Витрина раскладов выбранной tradition: доступ, позиции и tier."""
    requested_id = deck_id or (user["tarot_deck_id"] if "tarot_deck_id" in user.keys() else None)
    try:
        selected_id = tarot.deck_metadata(requested_id)["deck_id"]
    except ValueError as exc:
        raise HTTPException(400, "неизвестная колода") from exc
    return await catalog.spread_list(db, user, selected_id)


@router.get("/decks")
async def decks(user=Depends(current_user)):
    """Selectable traditions/decks with count, image namespace and provenance."""
    return tarot.available_decks()


@router.get("/spreads/full")
async def spreads_full(deck_id: str | None = Query(default=None),
                       user=Depends(current_user)):
    """Все встроенные расклады с `guide` — пояснения для страницы выбора.

    `/spreads` (витрина) не несёт `guide`, а здесь он нужен фронту, чтобы
    показать клиентке, что именно покажет расклад, до того как она заплатит.
    """
    fields = ("title", "positions", "tier", "emoji", "hint", "guide")
    requested_id = deck_id or (user["tarot_deck_id"] if "tarot_deck_id" in user.keys() else None)
    try:
        selected_id = tarot.deck_metadata(requested_id)["deck_id"]
    except ValueError as exc:
        raise HTTPException(400, "неизвестная колода") from exc
    return [{"code": code, **{f: item.get(f) for f in fields}}
            for code, item in tarot.spreads_for(selected_id).items()]


class DrawIn(BaseModel):
    question: str | None = None
    deck_id: str | None = None


@router.post("/draw", dependencies=[Depends(rate_limit("write"))])
async def draw(spread: str = Query(default="three"), item: DrawIn | None = None,
               question: str = Query(default=""),
               deck_id: str | None = Query(default=None),
               user=Depends(current_user), db=Depends(get_db)):
    """Тянет карты. Трактовка — вторым запросом, после анимации переворота.

    `question` — формулировка клиентки «что спросить у карт»: сохраняется в
    раскладе и на трактовке читается моделью (карты отвечают на конкретное).
    Принимаем и из query, и из тела — фронтенд шлёт в теле, старые вызовы в query.
    """
    q = (item.question if item and item.question else question or "").strip() or None
    selected_deck = item.deck_id if item and item.deck_id else deck_id
    try:
        result = await chat_svc.draw(db, user, spread, surface="miniapp", question=q,
                                     deck_id=selected_deck)
    except chat_svc.ChatDenied as e:
        raise access_denied(e.verdict) from e
    # короткое описание расклада для страницы выбора / карточки результата
    result["guide"] = tarot.spread_for(result["spread"], result["deck_id"]).get("guide", "")
    result["decks"] = tarot.available_decks()
    return result


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


@router.get("/stats")
async def stats(user=Depends(current_user), db=Depends(get_db)):
    """Что сбывалось: счётчик отметок «сбылось / частично / нет»."""
    return await readings.outcome_stats(db, user["tg_id"])


class OutcomeIn(BaseModel):
    outcome: str          # came_true | partly | no


@router.post("/outcome/{reading_id}", dependencies=[Depends(rate_limit("write"))])
async def set_outcome(reading_id: int, item: OutcomeIn, user=Depends(current_user),
                      db=Depends(get_db)):
    """Отметка «сбылось». Это и обратная связь, и доказательство ценности."""
    if not await readings.set_outcome(db, reading_id, user["tg_id"], item.outcome):
        raise HTTPException(400, "не удалось отметить расклад")
    return {"ok": True}
