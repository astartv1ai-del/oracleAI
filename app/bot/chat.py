"""Диалог с агентами: вопросы, выбор собеседника, голосовые, экстренный доступ.

Вся логика лимитов и списаний — в `services.chat`, здесь только Telegram:
показать «печатает», разбить длинный ответ, предложить выход при отказе.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ..core import agents
from ..repo import admin as admin_repo
from ..repo import billing, content, users
from ..services import analytics, chat as chat_svc, limits
from .keyboards import agents_kb, back_menu, limit_kb, main_menu

log = logging.getLogger("oracle.bot.chat")
router = Router()

# Telegram не принимает сообщения длиннее 4096 символов. Режем по абзацам,
# иначе длинный разбор пары просто не доходил до клиентки.
TG_LIMIT = 3900

TRIAL_OVER_FALLBACK = (
    "💫 Наша связь истончилась — твой доступ завершился.\n"
    "Я сохранила всё, что знаю о тебе. Продли связь со Вселенной 🎟"
)


class Ask(StatesGroup):
    """Состояние «жду вопрос»: помнит, какому агенту адресован следующий текст."""

    waiting = State()


def split_message(text: str, limit: int = TG_LIMIT) -> list[str]:
    """Делит длинный текст по абзацам, не разрывая слова."""
    if len(text) <= limit:
        return [text]
    parts, chunk = [], ""
    for paragraph in text.split("\n\n"):
        if len(chunk) + len(paragraph) + 2 > limit and chunk:
            parts.append(chunk.strip())
            chunk = ""
        if len(paragraph) > limit:            # один гигантский абзац — режем жёстко
            for i in range(0, len(paragraph), limit):
                parts.append(paragraph[i:i + limit])
            continue
        chunk += paragraph + "\n\n"
    if chunk.strip():
        parts.append(chunk.strip())
    return parts


async def _menu(db, tg_id: int):
    return main_menu(is_admin=bool(await admin_repo.resolve_role(db, tg_id)))


async def _send_long(message: Message, text: str, reply_markup=None) -> None:
    chunks = split_message(text)
    for i, chunk in enumerate(chunks):
        await message.answer(chunk,
                             reply_markup=reply_markup if i == len(chunks) - 1 else None)


async def _deny(message: Message, db, verdict) -> None:
    """Отказ — это тоже сценарий продажи: объясняем и даём выходы."""
    if verdict.reason == "sub_over":
        text = await content.get_text(db, "copy", "sub_over", TRIAL_OVER_FALLBACK)
        await message.answer(text, reply_markup=limit_kb(0, has_crystals=False))
        return
    allowance = verdict.allowance
    cost = allowance.emergency_cost if allowance else 20
    has = bool(allowance and allowance.crystals >= cost)
    text = await content.get_text(
        db, "copy", "limit_reached",
        "🌙 <i>Звёзды утомлены...</i>\n\nВопросы на сегодня исчерпаны, милая.")
    await message.answer(text, reply_markup=limit_kb(cost, has_crystals=has))


# ─────────────────────────── выбор собеседника ────────────────────────────────

@router.callback_query(F.data == "ask")
async def ask_menu(cb: CallbackQuery, state: FSMContext, db):
    """Кнопка «Спросить»: сразу к Оракулу, но с возможностью сменить агента."""
    user = await users.get(db, cb.from_user.id)
    allowance = await limits.allowance(db, user, check_followup=False)
    await state.set_state(Ask.waiting)
    await state.update_data(agent=agents.DEFAULT_AGENT)

    unit = "сегодня" if allowance.period == "day" else "на этой неделе"
    left = (f"осталось вопросов {unit}: {allowance.left}" if allowance.limit
            else "вопросы по подписке закончились")
    extra = (f" · купленных: {allowance.extra_questions}"
             if allowance.extra_questions else "")
    await cb.message.answer(
        f"Я слушаю тебя... ✨ ({left}{extra})\n"
        f"Напиши свой вопрос — о любви, деньгах, пути.\n\n"
        f"<i>Можно спросить и других: 🎴 Таролога, 🌌 Астролога, "
        f"🔢 Нумеролога, 📖 Хранителя дневника.</i>",
        reply_markup=agents_kb(await agents.agent_list(db, user)))
    await cb.answer()


@router.callback_query(F.data.startswith("agent:"))
async def pick_agent(cb: CallbackQuery, state: FSMContext, db):
    code = cb.data.split(":", 1)[1]
    if code not in agents.codes():
        await cb.answer("Такого собеседника нет")
        return
    user = await users.get(db, cb.from_user.id)
    spec = agents.get(code)
    await state.set_state(Ask.waiting)
    await state.update_data(agent=code)
    hints = "\n".join(f"• {s}" for s in spec.suggestions)
    await cb.message.answer(
        f"{spec.emoji} <b>{spec.display_name(user)}</b> — {spec.title.lower()}\n"
        f"<i>{spec.tagline}</i>\n\n{spec.greeting}\n\n{hints}",
        reply_markup=back_menu())
    await cb.answer()


# ─────────────────────────────── вопрос ───────────────────────────────────────

async def _answer(message: Message, db, user, text: str, agent: str) -> None:
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        result = await chat_svc.ask(db, user, text, agent=agent, surface="bot")
    except chat_svc.ChatDenied as e:
        await _deny(message, db, e.verdict)
        return
    except ValueError:
        await message.answer("Напиши вопрос словами, милая 🌙")
        return
    except Exception as e:  # noqa: BLE001
        log.exception("вопрос не обработан: %s", e)
        await message.answer("Звёзды сейчас молчат... задай вопрос ещё раз чуть позже 🌙")
        return
    await _send_long(message, result["answer"], reply_markup=back_menu())


@router.message(F.voice)
async def voice_msg(message: Message, state: FSMContext, db):
    """Голосовое = вопрос: расшифровываем Whisper'ом (нужен ключ OpenAI)."""
    from io import BytesIO

    from ..core import llm

    if not await content.is_on(db, "voice_questions", message.from_user.id,
                               default=True):
        await message.answer("Голосовые пока отключены — напиши текстом 🌙")
        return
    if message.voice.duration > 120:
        await message.answer("Такое длинное послание звёзды не удержат... "
                             "запиши покороче, до 2 минут 🙏")
        return
    buf = BytesIO()
    try:
        await message.bot.download(message.voice.file_id, destination=buf)
    except Exception as e:  # noqa: BLE001
        log.warning("голосовое не скачалось: %s", e)
        await message.answer("Не расслышала... напиши словами, милая 🌙")
        return
    text = await llm.transcribe(buf.getvalue())
    if not text:
        await message.answer("Я пока не слышу голоса — напиши свой вопрос текстом 🌙")
        return
    await message.answer(f"🎙 <i>Я услышала: «{text[:200]}»</i>")
    await _handle_text(message, state, db, text)


@router.message(F.text & ~F.text.startswith("/"))
async def any_text(message: Message, state: FSMContext, db):
    """Свободный текст = вопрос выбранному агенту."""
    await _handle_text(message, state, db, message.text)


async def _handle_text(message: Message, state: FSMContext, db, text: str) -> None:
    user = await users.get(db, message.from_user.id)
    if not user or not user["onboarded"]:
        await message.answer("Сначала познакомимся — нажми /start 🌙")
        return
    if user["status"] == "blocked":
        await message.answer("Доступ приостановлен. Напиши в поддержку 🌙")
        return
    await users.touch(db, user["tg_id"])

    data = await state.get_data()
    agent = data.get("agent") or agents.DEFAULT_AGENT
    await _answer(message, db, user, text, agent)


# ─────────────────────── экстренный доступ за Кристаллы ───────────────────────

@router.callback_query(F.data == "emergency")
async def emergency(cb: CallbackQuery, state: FSMContext, db):
    """Один вопрос вне лимита за Кристаллы.

    Списываем сразу и выдаём право на один вопрос: так покупка не «повисает»
    между списанием и вопросом, а если клиентка не спросит сегодня — право
    останется за ней на неделю.
    """
    user = await users.get(db, cb.from_user.id)
    cost = int(await content.get_setting(db, "limits.emergency_cost", 20) or 20)
    if (user["crystals"] or 0) < cost:
        await cb.answer("Не хватает Кристаллов ✦", show_alert=True)
        await cb.message.answer("💎 Пополни запас Кристаллов:",
                                reply_markup=limit_kb(cost, has_crystals=False))
        return
    if not await billing.spend_crystals(db, user["tg_id"], cost, "emergency_question"):
        await cb.answer("Не хватает Кристаллов ✦", show_alert=True)
        return
    await billing.grant_entitlement(db, user["tg_id"], "question", "*", qty=1,
                                    valid_days=7, source="crystals")
    await analytics.track(db, "emergency_unlock", user["tg_id"],
                          props={"cost": cost})
    await state.set_state(Ask.waiting)
    await state.update_data(agent=agents.DEFAULT_AGENT)
    await cb.message.answer(
        f"🔮 <i>Я раздвинула завесу силой ✦{cost}...</i>\n"
        f"Задай свой вопрос — прямо сейчас.")
    await cb.answer()


@router.callback_query(F.data == "menu")
async def menu(cb: CallbackQuery, state: FSMContext, db):
    await state.clear()
    user = await users.get(db, cb.from_user.id)
    await cb.message.answer(f"Я здесь, {user['name']} 🌙",
                            reply_markup=await _menu(db, cb.from_user.id))
    await cb.answer()
