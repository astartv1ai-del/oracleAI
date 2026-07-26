"""Дневник: записи, стрик, вечерний вопрос от Оракула.

Практики живут в отдельном роутере (`practices.py`) — это самостоятельный
раздел продукта с программой по дням, а не придаток дневника.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ...core import memory
from ...repo import dialog, users
from ...services import analytics
from ..deps import current_user, get_db, rate_limit

router = APIRouter(prefix="/api", tags=["diary"])


class DiaryIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    mood: str | None = Field(default=None, max_length=20)


@router.get("/diary")
async def diary_list(user=Depends(current_user), db=Depends(get_db)):
    entries = await dialog.get_diary(db, user["tg_id"], limit=60)
    return {"entries": entries,
            "streak": await dialog.diary_streak(db, user["tg_id"])}


@router.post("/diary", dependencies=[Depends(rate_limit("write"))])
async def diary_add(item: DiaryIn, user=Depends(current_user), db=Depends(get_db)):
    """Запись в дневник. Первые 150 символов уходят в память агента."""
    text = item.text.strip()[:1000]
    await dialog.add_diary(db, user["tg_id"], text, mood=item.mood)
    await memory.remember(db, user["tg_id"], f"Из дневника: {text[:150]}",
                          kind="event")
    await analytics.track(db, "diary_write", user["tg_id"], surface="miniapp")
    return {"ok": True, "streak": await dialog.diary_streak(db, user["tg_id"])}


@router.get("/diary/prompt")
async def diary_prompt(user=Depends(current_user), db=Depends(get_db)):
    """Вечерний вопрос от Оракула — чтобы дневник не был пустым полем.

    Вопрос зависит от того, писала ли она сегодня и есть ли у неё стрик:
    пустое поле «расскажи, как день» люди не заполняют, а конкретный вопрос —
    заполняют.
    """
    entries = await dialog.get_diary(db, user["tg_id"], limit=1)
    streak = await dialog.diary_streak(db, user["tg_id"])
    today = users.user_today(user)
    written_today = bool(entries and (entries[0]["created_at"] or "")[:10] == today)
    return {
        "written_today": written_today,
        "streak": streak,
        "prompt": _prompt_for(streak, written_today),
    }


_PROMPTS_FIRST = [
    "С чего начнём? Расскажи, что сегодня было самым важным.",
    "Что сегодня отняло больше всего сил — и что вернуло?",
    "Если бы у сегодняшнего дня было одно слово, какое?",
]
_PROMPTS_REGULAR = [
    "Что сегодня получилось лучше, чем ты ожидала?",
    "О чём ты думала сегодня чаще всего?",
    "Что тебя сегодня задело — и почему именно это?",
    "Кому сегодня хотелось написать, но ты не стала?",
    "За что сегодня можешь сказать себе спасибо?",
]
_PROMPTS_STREAK = [
    "Ты пишешь уже который день. Что изменилось с первой записи?",
    "Что повторяется в твоих днях последнюю неделю?",
    "Если посмотреть на неделю целиком — куда она тебя ведёт?",
]


def _prompt_for(streak: int, written_today: bool) -> str:
    """Детерминированный выбор: вопрос не должен меняться при каждом обновлении."""
    from ...core.stable import stable_seed
    if written_today:
        return "Сегодня уже записано ✨ Хочешь добавить ещё что-то?"
    pool = (_PROMPTS_STREAK if streak >= 5 else
            _PROMPTS_REGULAR if streak >= 1 else _PROMPTS_FIRST)
    return pool[stable_seed(str(streak), "diary") % len(pool)]
