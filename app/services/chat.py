"""Диалог и расклады — единый путь для бота и Mini App.

Раньше проверка лимита, списание и сохранение сообщений были продублированы в
хендлерах бота и в роутерах API. Дубликат означал расхождение: в Mini App расклад
тратил вопрос дня, а в боте — нет. Теперь оба входа зовут этот модуль.

Порядок шагов важен и одинаков везде:
    проверить доступ → списать → сохранить вопрос → ответить → сохранить ответ.
Списание строго до генерации: сгенерировать и не списать — значит отдать платный
ответ бесплатно; списать и не ответить — вернуть списанное (см. `_refund`).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from ..core import agent as agent_core
from ..core import agents, safety, tarot
from ..repo import analytics as analytics_repo
from ..repo import billing as billing_repo
from ..repo import dialog, readings, users
from . import analytics, catalog, limits

log = logging.getLogger("oracle.chat")

MAX_QUESTION_LEN = 1000

# Фоновые задачи (экстракция памяти) держим за ссылки: сборщик мусора может
# уничтожить задачу, на которую никто не ссылается, и память не сохранится.
_background: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    task = asyncio.create_task(coro)
    _background.add(task)
    task.add_done_callback(_background.discard)


class ChatDenied(Exception):
    """Доступ к ответу не выдан. `verdict` объясняет причину."""

    def __init__(self, verdict):
        super().__init__(verdict.reason or "denied")
        self.verdict = verdict


async def _refund(db, user, verdict) -> None:
    """Возвращает списанное, если ответ так и не был получен."""
    if verdict.charge == limits.CRYSTALS:
        cost = verdict.allowance.emergency_cost if verdict.allowance else 20
        await billing_repo.add_crystals(db, user["tg_id"], cost,
                                        "refund_failed_answer")
    elif verdict.charge in (limits.ENT_QUESTION, limits.ENT_SPREAD):
        kind = "question" if verdict.charge == limits.ENT_QUESTION else "spread"
        await billing_repo.grant_entitlement(
            db, user["tg_id"], kind, verdict.code, qty=1, valid_days=7,
            source="refund")


# ────────────────────────────── вопрос агенту ─────────────────────────────────

async def ask(db, user, text: str, *, agent: str = agents.DEFAULT_AGENT,
              surface: str = "bot", allow_paid: bool = True,
              thread_id: int | None = None) -> dict:
    """Задаёт вопрос агенту. Поднимает `ChatDenied`, если доступа нет.

    `thread_id` — конкретная сессия (многочатовой режим Mini App). Без него —
    активный тред агента (один диалог на агента, как в боте).
    """
    question = (text or "").strip()[:MAX_QUESTION_LEN]
    if not question:
        raise ValueError("пустой вопрос")
    spec = agents.get(agent)
    if thread_id is not None:
        thread = await dialog.get_thread(db, thread_id, user["tg_id"])
        if not thread or thread["archived"] or thread["agent"] != spec.code:
            raise ValueError("нет такого чата")
    else:
        thread = await dialog.ensure_thread(db, user["tg_id"], spec.code,
                                            title=spec.title)

    # Кризисный протокол — до всего остального. Ответ собирает код, модель не
    # зовём вовсе, лимит не тратим: брать вопрос за деньги в такой момент нельзя.
    level, category = safety.classify(question)
    if level == safety.CRISIS:
        result = await _crisis_answer(db, user, question, category, agent, surface)
        await analytics.track_once(
            db, analytics.E_FIRST_QUESTION, user["tg_id"],
            props={"agent": agent, "safety": "crisis"}, surface=surface,
        )
        return result

    # Зона бюджета заперта на пользователя: два устройства не должны пройти
    # «право есть» одновременно — раньше, чем запись вопроса зафиксирует расход
    async with limits.user_lock(user["tg_id"]):
        verdict = await limits.check(db, user)
        if not verdict.allowed or (not allow_paid and verdict.charge in (
                limits.CRYSTALS, limits.ENT_QUESTION)):
            await analytics.track(db, analytics.E_LIMIT_HIT, user["tg_id"],
                                  props={"reason": verdict.reason, "agent": agent},
                                  surface=surface)
            raise ChatDenied(verdict)
        if not await limits.consume(db, user, verdict):
            raise ChatDenied(verdict)

        await dialog.save_message(
            db, user["tg_id"], "user", question,
            is_question=limits.counts_toward_limit(verdict),
            thread_id=thread["id"], agent=spec.code, surface=surface)

    allowance_line = _allowance_line(verdict)
    try:
        answer = await agent_core.ask_oracle(
            db, user, question, agent=spec.code, thread_id=thread["id"],
            allowance_line=allowance_line,
            extra_rules=safety.soften_rule(category) if level == safety.SOFTEN else "")
    except Exception:
        await _refund(db, user, verdict)
        raise
    if level == safety.SOFTEN:
        await safety.record(db, user["tg_id"], category, "soften", question)

    await dialog.save_message(db, user["tg_id"], "assistant", answer,
                              thread_id=thread["id"], agent=spec.code,
                              surface=surface)
    await analytics.track(db, analytics.E_QUESTION, user["tg_id"],
                          props={"agent": spec.code, "charge": verdict.charge},
                          surface=surface)
    await analytics.track_once(
        db, analytics.E_FIRST_QUESTION, user["tg_id"],
        props={"agent": spec.code}, surface=surface,
    )
    # Память растёт только со свежих вопросов: уточнение за минуту до этого уже
    # получило свой контекст, экстракт с него плодил бы шум и жёг lite-вызов (G23).
    if verdict.charge != limits.FOLLOWUP and bool(user["memory_enabled"]):
        _spawn(agent_core.extract_memory_llm(db, user, question, answer))

    fresh = await users.get(db, user["tg_id"])
    return {
        "answer": answer,
        "agent": spec.code,
        "thread_id": thread["id"],
        "charge": verdict.charge,
        "allowance": (await limits.allowance(db, fresh,
                                             check_followup=False)).as_dict(),
    }


async def _crisis_answer(db, user, question: str, category: str, agent: str,
                         surface: str) -> dict:
    """Кризисный ответ: поддержка и контакты помощи, без агента и без списания.

    Переписку всё равно сохраняем — иначе следующий вопрос придёт в пустоту, а
    поддержка не увидит контекста обращения.
    """
    spec = agents.get(agent)
    thread = await dialog.ensure_thread(db, user["tg_id"], spec.code,
                                        title=spec.title)
    await dialog.save_message(db, user["tg_id"], "user", question,
                              is_question=False, thread_id=thread["id"],
                              agent=spec.code, surface=surface)
    answer = await safety.crisis_reply(db, user, category)
    await dialog.save_message(db, user["tg_id"], "assistant", answer,
                              thread_id=thread["id"], agent=spec.code,
                              surface=surface)
    await safety.record(db, user["tg_id"], category, "support", question)
    await analytics.track(db, "safety_crisis", user["tg_id"],
                          props={"category": category}, surface=surface)
    log.warning("кризисное обращение от %s (%s)", user["tg_id"], category)
    return {
        "answer": answer,
        "agent": spec.code,
        "thread_id": thread["id"],
        "charge": "none",
        "safety": category,
        "allowance": (await limits.allowance(db, user,
                                             check_followup=False)).as_dict(),
    }


def _allowance_line(verdict) -> str:
    """Строка для промпта: агент должен знать про остаток, но не козырять им."""
    a = verdict.allowance
    if not a or a.period == "none":
        return "Не упоминай лимиты и подписку без прямого вопроса."
    unit = "сегодня" if a.period == "day" else "на этой неделе"
    return (f"У неё осталось вопросов {unit}: {a.left} из {a.limit}. "
            f"Не упоминай это без прямого вопроса.")


# ──────────────────────────────── расклады ────────────────────────────────────

async def draw(db, user, spread_code: str, *, surface: str = "bot",
               question: str | None = None) -> dict:
    """Тянет карты: проверяет доступ, списывает и сохраняет расклад без трактовки.

    Трактовка — вторым шагом (`interpret`), чтобы интерфейс успел показать
    анимацию переворота. Карты уже лежат в БД, подменить их нельзя.
    """
    item = await catalog.get_spread(db, spread_code)
    code = item["code"] if "code" in item else spread_code

    # Тот же пользовательский замок бюджета, что и в `ask`: расклад и вопрос
    # делят один тарифный лимит и должны списывать его атомарно между собой
    async with limits.user_lock(user["tg_id"]):
        verdict = await limits.spread_access(db, user, code)
        if not verdict.allowed:
            await analytics.track(db, analytics.E_LIMIT_HIT, user["tg_id"],
                                  props={"reason": verdict.reason, "spread": code},
                                  surface=surface)
            raise ChatDenied(verdict)
        if not await limits.consume(db, user, verdict):
            raise ChatDenied(verdict)

        positions = item["positions"]
        cards = tarot.draw(len(positions))
        title = item["title"]
        label = question or f"Расклад «{title}»"

        thread = await dialog.ensure_thread(db, user["tg_id"], "tarot",
                                            title=agents.get("tarot").title)
        await dialog.save_message(
            db, user["tg_id"], "user", label,
            is_question=limits.counts_toward_limit(verdict),
            thread_id=thread["id"], agent="tarot", surface=surface)
        reading_id = await readings.start_reading(
            db, user["tg_id"], code, label, cards, surface=surface,
            paid_with=limits.PAID_WITH.get(verdict.charge, "daily"))

    await analytics.track(db, analytics.E_TAROT, user["tg_id"],
                          props={"spread": code, "charge": verdict.charge},
                          surface=surface)
    return {"reading_id": reading_id, "title": title, "positions": positions,
            "cards": cards, "spread": code, "thread_id": thread["id"],
            "charge": verdict.charge}


async def interpret(db, user, reading_id: int, *, surface: str = "bot") -> str:
    """Трактовка уже вытянутых карт. Повторный вызов отдаёт сохранённый текст."""
    row = await readings.get_reading(db, reading_id, user["tg_id"])
    if not row:
        raise LookupError("расклад не найден")
    if row["answer"]:
        return row["answer"]

    import json
    try:
        cards = json.loads(row["cards_json"] or "[]")
    except ValueError:
        cards = []
    if not cards:
        raise LookupError("в раскладе нет карт")

    item = await catalog.get_spread(db, row["spread"] or "")
    if not row["spread"]:
        # исторические записи хранили только название расклада
        item = tarot.spread_by_title(
            (row["question"] or "").replace("Расклад «", "").rstrip("»"))
    positions = item["positions"][:len(cards)]

    answer = await agent_core.interpret_reading(db, user, item["title"], cards,
                                                positions,
                                                question=row["question"] or None)
    await readings.finish_reading(db, reading_id, answer)
    thread = await dialog.ensure_thread(db, user["tg_id"], "tarot")
    await dialog.save_message(db, user["tg_id"], "assistant", answer,
                              thread_id=thread["id"], agent="tarot",
                              surface=surface)
    return answer


# ──────────────────────────── история и треды ─────────────────────────────────

async def threads_view(db, user) -> list[dict]:
    """Список чатов для интерфейса: агент + превью последнего сообщения."""
    existing = {t["agent"]: t for t in await dialog.list_threads(db, user["tg_id"])}
    out = []
    for item in await agents.agent_list(db, user):
        thread = existing.get(item["code"])
        out.append({
            **item,
            "thread_id": thread["id"] if thread else None,
            "last_text": (thread["last_text"] if thread else None) or item["greeting"],
            "last_at": thread["last_at"] if thread else None,
            "msg_count": thread["msg_count"] if thread else 0,
        })
    out.sort(key=lambda t: (t["last_at"] is None, t["last_at"] or ""), reverse=True)
    return out


async def thread_history(db, user, agent: str, limit: int = 60) -> dict:
    spec = agents.get(agent)
    thread = await dialog.ensure_thread(db, user["tg_id"], spec.code,
                                        title=spec.title)
    messages = await dialog.thread_messages(db, thread["id"], limit=limit)
    return {"agent": spec.as_dict(user), "thread_id": thread["id"],
            "messages": messages}


async def track_open(db, user, surface: str = "miniapp") -> None:
    """Writes an open and one-time D1/D7 return milestones server-side."""
    tg_id = user["tg_id"]
    await analytics.track_now(db, analytics_repo.E_MINIAPP_OPEN, tg_id,
                              surface=surface)
    cur = await db.execute(
        "SELECT MIN(day) first_day FROM events WHERE tg_id=? AND name=?",
        (tg_id, analytics_repo.E_MINIAPP_OPEN),
    )
    row = await cur.fetchone()
    if not row or not row["first_day"]:
        return
    try:
        first_day = datetime.fromisoformat(row["first_day"]).date()
    except (TypeError, ValueError):
        return
    age_days = (datetime.now(timezone.utc).date() - first_day).days
    for milestone, threshold in (
        (analytics.E_RETURN_D1, 1),
        (analytics.E_RETURN_D7, 7),
    ):
        if age_days >= threshold:
            await analytics.track_once(
                db, milestone, tg_id, props={"cohort_day": threshold},
                surface=surface,
            )
