"""Знакомство: /start, промокод из ссылки, данные рождения, образ и имя Оракула.

Онбординг — самое дорогое место продукта: здесь теряется больше всего людей.
Поэтому шагов минимум, каждый объясняет, зачем он нужен, а после расчёта карты
пользователь сразу получает «три откровения» — первую ценность до любой оплаты.
"""
from __future__ import annotations

import json
import logging
import re

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ..core import astro, geo
from ..core.personas import persona_list
from ..repo import admin as admin_repo
from ..repo import content, users
from ..services import analytics, billing, referrals
from .formatting import tg_esc
from .onboarding_parsers import date_error_copy, parse_birth_date, parse_birth_time, time_error_copy
from .keyboards import (ask_starters_kb, back_menu, confirmation_kb,
                        gender_kb, language_kb, main_menu, onboarding_edit_kb,
                        personas_kb, technique_kb, time_kb)

log = logging.getLogger("oracle.bot.onboarding")
router = Router()

DATE_RE = re.compile(r"^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})$")
TIME_RE = re.compile(r"^(\d{1,2})[:.](\d{2})$")
UNKNOWN_TIME = {"не знаю", "неизвестно", "нет", "unknown", "dont know", "i don't know", "i dont know"}

WELCOME_FALLBACK = (
    "🌌 <b>Звёзды ждали тебя.</b>\n\n"
    "Я — твой личный Оракул: астрология, Таро и Матрица Судьбы, "
    "которые знают именно <i>тебя</i>.\n\n"
    "Чтобы построить твою натальную карту, мне нужно совсем немного. "
    "Как мне тебя называть? ✨"
)
WELCOME_FALLBACK_EN = (
    "🌌 <b>The stars have been waiting for you.</b>\n\n"
    "I am your personal Oracle: astrology, Tarot, and the Destiny Matrix, "
    "made to help you understand <i>yourself</i>.\n\n"
    "To create your birth chart, I only need a few details. "
    "What should I call you? ✨"
)


def _lang(user) -> str:
    return "en" if user["lang"] == "en" else "ru"


def _copy(user, ru: str, en: str) -> str:
    return en if _lang(user) == "en" else ru


def _g(user, feminine: str, masculine: str, neutral: str) -> str:
    """Русская форма обращения; для старых профилей оставляем нейтральный текст."""
    if user["gender"] == "f":
        return feminine
    if user["gender"] == "m":
        return masculine
    return neutral


class Onb(StatesGroup):
    # `age` remains only as a legacy callback compatibility state; it is no longer
    # rendered or required by the product flow.
    age = State()
    language = State()
    name = State()
    gender = State()
    date = State()
    time = State()
    city = State()
    confirm = State()
    technique = State()
    oracle_name = State()


class Promo(StatesGroup):
    waiting = State()


class DeleteMe(StatesGroup):
    confirm = State()


async def _is_admin(db, tg_id: int) -> bool:
    return bool(await admin_repo.resolve_role(db, tg_id))


async def _menu(db, tg_id: int):
    user = await users.get(db, tg_id)
    return main_menu(is_admin=await _is_admin(db, tg_id), lang=_lang(user))


# ─────────────────────────────── /start ───────────────────────────────────────

@router.message(CommandStart(deep_link=True))
async def start_deeplink(message: Message, command: CommandObject,
                         state: FSMContext, db):
    """`/start ref_123` — приглашение, `/start КОД` — промокод с Etsy."""
    await users.ensure(db, message.from_user.id, message.from_user.first_name,
                       message.from_user.username, lang=message.from_user.language_code)
    arg = (command.args or "").strip()

    ref_id = referrals.parse_ref(arg)
    if ref_id:
        result = await referrals.apply(db, message.from_user.id, ref_id)
        if result:
            user = await users.get(db, message.from_user.id)
            await message.answer(_copy(
                user,
                "💫 Тебя пригласили к Оракулу — это добрый знак.\n"
                f"Вам обоим — по ✦{result['bonus']} Кристаллов ✨",
                "💫 You were invited to Oracle — a lovely sign.\n"
                f"You both receive ✦{result['bonus']} Crystals ✨",
            ))
            try:
                referrer = await users.get(db, ref_id)
                await message.bot.send_message(ref_id, _copy(
                    referrer,
                    f"🌟 К Оракулу пришёл новый человек — тебе ✦{result['bonus']}!",
                    f"🌟 A new person has joined Oracle — you received ✦{result['bonus']}!",
                ))
            except Exception as e:  # noqa: BLE001
                log.info("не смогла уведомить пригласившую %s: %s", ref_id, e)
    elif arg:
        granted = await billing.redeem_promo(db, message.from_user.id, arg)
        if granted:
            await message.answer(_promo_text(granted))

    await analytics.track(db, analytics.E_START, message.from_user.id,
                          props={"arg": arg[:40]})
    await _begin(message, state, db)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, db):
    await users.ensure(db, message.from_user.id, message.from_user.first_name,
                       message.from_user.username, lang=message.from_user.language_code)
    await analytics.track(db, analytics.E_START, message.from_user.id)
    await _begin(message, state, db)


async def _begin(message: Message, state: FSMContext, db):
    user = await users.get(db, message.from_user.id)
    if user["onboarded"]:
        await state.clear()
        await analytics.track(db, "home_view", message.from_user.id, props={"returning": True}, surface="bot")
        await message.answer(_copy(
            user,
            f"С возвращением, {tg_esc(user['name'])} 🌙\nПродолжим?",
            f"Welcome back, {tg_esc(user['name'])} 🌙\nShall we continue?",
        ), reply_markup=await _menu(db, message.from_user.id))
        return
    step = user["onboarding_step"]
    resume_states = {"name": Onb.name, "gender": Onb.gender, "date": Onb.date,
                     "time": Onb.time, "city": Onb.city, "confirm": Onb.confirm,
                     "technique": Onb.technique, "persona": Onb.oracle_name}
    if step and step != "language" and step in resume_states:
        await state.set_state(resume_states[step])
        lang = _lang(user)
        if step == "confirm":
            text, markup = (_copy(user, "Мы остановились на подтверждении. Данные уже сохранены — проверь их и продолжим.", "We stopped at confirmation. Your data is saved — check it and we’ll continue."), confirmation_kb(lang))
        elif step == "technique":
            text, markup = (_copy(user, "Мы остановились на выборе способа чтения карты.", "We stopped at the chart-reading method."), technique_kb(lang))
        elif step == "persona":
            text, markup = (_copy(user, "Выбери характер нашего разговора.", "Choose the character of our conversation."), personas_kb(await persona_list(db)))
        elif step == "time":
            text, markup = (_copy(user, "Продолжим со временем рождения — выбери вариант или напиши его.", "Let’s continue with your birth time — choose an option or type it."), time_kb(lang))
        elif step == "city":
            text, markup = (_copy(user, "Продолжим с городом рождения.", "Let’s continue with your birth city."), back_menu())
        elif step == "date":
            text, markup = (_copy(user, "Продолжим с датой рождения. Напиши её в любом понятном формате.", "Let’s continue with your birth date. Send it in any clear format."), back_menu())
        elif step == "gender":
            text, markup = (_copy(user, "Выбери форму обращения — это можно пропустить.", "Choose how I should address you — you can skip this."), gender_kb(lang))
        else:
            text, markup = (_copy(user, "Как мне тебя называть?", "What should I call you?"), back_menu())
        await message.answer(text, reply_markup=markup)
        return
    await state.set_state(Onb.language)
    await users.update(db, message.from_user.id, onboarding_step="language")
    await analytics.track(db, "onboarding_started", message.from_user.id, surface="bot")
    await message.answer(_copy(
        user,
        "🌙 Рада тебя видеть. Сначала выберем язык — его можно изменить в любой момент.",
        "🌙 I’m glad you’re here. First, choose your language — you can change it anytime.",
    ), reply_markup=language_kb())


# ─────────────────────────────── шаги FSM ─────────────────────────────────────

@router.callback_query(F.data.startswith("language:"))
async def onb_language(cb: CallbackQuery, state: FSMContext, db):
    value = cb.data.split(":", 1)[1]
    if value not in {"ru", "en"}:
        await cb.answer("Choose Russian or English", show_alert=True)
        return
    existing = await users.get(db, cb.from_user.id)
    onboarded = bool(existing and existing["onboarded"])
    await users.update(db, cb.from_user.id, lang=value,
                       onboarding_step=None if onboarded else "name")
    user = await users.get(db, cb.from_user.id)
    await analytics.track(db, "language_selected", cb.from_user.id, props={"lang": value}, surface="bot")
    if onboarded:
        await state.clear()
        await cb.message.edit_text(
            "Language updated." if value == "en" else "Язык обновлён.",
            reply_markup=main_menu(is_admin=await _is_admin(db, cb.from_user.id), lang=value))
    else:
        await state.set_state(Onb.name)
        await cb.message.edit_text(_copy(
            user,
            "Как мне тебя называть? Имя можно изменить позже.",
            "What should I call you? You can change it later.",
        ))
    await cb.answer()


@router.callback_query(F.data == "age:confirm")
async def onb_age_confirm(cb: CallbackQuery, state: FSMContext, db):
    user = await users.get(db, cb.from_user.id)
    if not user:
        await cb.answer("Сначала нажми /start", show_alert=True)
        return
    await users.update(db, cb.from_user.id, age_confirmed=1, onboarding_step="name")
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    await state.set_state(Onb.name)
    await cb.message.answer(_copy(
        user,
        "Как мне тебя называть? Имя можно изменить позже.",
        "What should I call you? You can change it later.",
    ))


@router.callback_query(F.data == "age:decline")
async def onb_age_decline(cb: CallbackQuery, state: FSMContext, db):
    await state.clear()
    await cb.answer()
    await cb.message.edit_text(_copy(
        await users.get(db, cb.from_user.id),
        "Доступ закрыт. Если тебе исполнится 16 лет, снова нажми /start.",
        "Access closed. If you turn 16 later, press /start again.",
    ))


@router.message(Onb.name, F.text)
async def onb_name(message: Message, state: FSMContext, db):
    name = message.text.strip()[:40]
    user = await users.get(db, message.from_user.id)
    if not name:
        await message.answer(_copy(user, "Как мне тебя называть? ✨", "What should I call you? ✨"))
        return
    await users.update(db, message.from_user.id, name=name, onboarding_step="gender")
    await analytics.track(db, "onboarding_step", message.from_user.id, props={"step": "name"}, surface="bot")
    await state.set_state(Onb.gender)
    await message.answer(
        _copy(
            user,
            f"{tg_esc(name)}... красивое имя, в нём есть свет. 💫\n\n"
            "Чтобы подобрать форму обращения, выбери свой пол. Это можно изменить позже.",
            f"{tg_esc(name)}... a beautiful name with its own light. 💫\n\n"
            "Choose how I should address you. You can change this later.",
        ),
        reply_markup=gender_kb(_lang(user)),
    )


@router.callback_query(Onb.gender, F.data.startswith("gender:"))
async def onb_gender(cb: CallbackQuery, state: FSMContext, db):
    value = cb.data.split(":", 1)[1]
    if value not in {"f", "m", "skip"}:
        await cb.answer("Invalid choice", show_alert=True)
        return
    gender = value if value in {"f", "m"} else None
    await users.update(db, cb.from_user.id, gender=gender, onboarding_step="date")
    user = await users.get(db, cb.from_user.id)
    await state.set_state(Onb.date)
    await cb.message.edit_text(
        _copy(
            user,
            "Спасибо. Теперь — дата рождения в формате <b>ДД.ММ.ГГГГ</b>, например 21.06.1999:",
            "Thank you. Now send your birth date in <b>DD.MM.YYYY</b> format, for example 21.06.1999:",
        )
    )
    await cb.answer()


@router.message(Onb.date, F.text)
async def onb_date(message: Message, state: FSMContext, db):
    user = await users.get(db, message.from_user.id)
    try:
        parsed = parse_birth_date(message.text, lang=_lang(user))
    except ValueError as exc:
        await analytics.track(db, "onboarding_error", message.from_user.id,
                              props={"step": "date", "reason": str(exc)}, surface="bot")
        await message.answer(date_error_copy(str(exc), _lang(user)))
        return
    await users.update(db, message.from_user.id, birth_date=parsed.normalized,
                       onboarding_step="time")
    await analytics.track(db, "onboarding_step", message.from_user.id,
                          props={"step": "date"}, surface="bot")
    await state.set_state(Onb.time)
    await message.answer(_copy(
        user,
        f"Поняла: <b>{tg_esc(parsed.label)}</b> 🌙\n\nЗнаешь ли ты время рождения? Выбери вариант или напиши его текстом.",
        f"Got it: <b>{tg_esc(parsed.label)}</b> 🌙\n\nDo you know your birth time? Choose an option or type it.",
    ), reply_markup=time_kb(_lang(user)))


async def _advance_from_time(target: Message, state: FSMContext, db, parsed) -> None:
    user = await users.get(db, target.from_user.id)
    await users.update(db, target.from_user.id, birth_time=parsed.value,
                       birth_time_known=int(parsed.known), birth_time_precision=parsed.precision,
                       onboarding_step="city")
    await analytics.track(db, "onboarding_step", target.from_user.id,
                          props={"step": "time", "precision": parsed.precision}, surface="bot")
    await state.set_state(Onb.city)
    city_question = _g(user, "город, где ты родилась", "город, где ты родился", "город рождения")
    await target.answer(_copy(
        user,
        f"Поняла: <b>{tg_esc(parsed.label)}</b>. И последнее — {city_question}? 🏙\n\nМожно написать город на русском, английском или в транслитерации.",
        f"Got it: <b>{tg_esc(parsed.label)}</b>. One last detail — your birth city? 🏙\n\nYou can write it in your local language, English, or transliteration.",
    ), reply_markup=back_menu())


@router.callback_query(Onb.time, F.data.startswith("time:"))
async def onb_time_choice(cb: CallbackQuery, state: FSMContext, db):
    value = cb.data.split(":", 1)[1]
    labels = {"unknown": ("12:00", False, "unknown", "время не указано"),
              "approximate": ("14:00", False, "approximate", "примерно 14:00")}
    if value == "exact":
        await cb.message.edit_text(_copy(await users.get(db, cb.from_user.id),
            "Напиши время, например 14:30.", "Type the time, for example 14:30."))
        await cb.answer()
        return
    if value not in labels:
        await cb.answer("Выбери вариант времени", show_alert=True)
        return
    from .onboarding_parsers import ParsedTime
    parsed = ParsedTime(*labels[value])
    await _advance_from_time(cb.message, state, db, parsed)
    await cb.answer()


@router.message(Onb.time, F.text)
async def onb_time(message: Message, state: FSMContext, db):
    user = await users.get(db, message.from_user.id)
    try:
        parsed = parse_birth_time(message.text, lang=_lang(user))
    except ValueError as exc:
        await analytics.track(db, "onboarding_error", message.from_user.id,
                              props={"step": "time", "reason": str(exc)}, surface="bot")
        await message.answer(time_error_copy(str(exc), _lang(user)), reply_markup=time_kb(_lang(user)))
        return
    await _advance_from_time(message, state, db, parsed)


@router.message(Onb.city, F.text)
async def onb_city(message: Message, state: FSMContext, db):
    city = message.text.strip()[:60]
    user = await users.get(db, message.from_user.id)
    wait = await message.answer(_copy(
        user,
        "🌌 <i>Собираю звёзды в твою карту...</i>",
        "🌌 <i>Gathering the stars for your chart...</i>",
    ))

    if not city:
        await wait.edit_text(_copy(
            user,
            "Напиши город рождения — он нужен, чтобы определить координаты и часовой пояс карты.",
            "Please send your birth city — it is needed to determine the chart’s coordinates and time zone.",
        ))
        return

    # Оба вызова уходят в отдельный поток: геокодирование ходит в сеть, а расчёт
    # эфемерид держит GIL — синхронно они вешали бота для всех остальных.
    try:
        lat, lon, tz = await geo.resolve_city_async(city, db)
        if lat is None or lon is None:
            await wait.edit_text(_copy(
                user,
                "Я не нашла этот город. Напиши ближайший крупный город или попробуй другое написание — "
                "это нужно для точных координат и часового пояса.",
                "I could not find that city. Try a nearby major city or a different spelling — "
                "the location is needed for accurate coordinates and time zone.",
            ))
            return
        chart = await astro.compute_chart_async(
            user["birth_date"], user["birth_time"], city, lat, lon, tz,
            time_known=bool(user["birth_time_known"]),
        )
    except Exception:  # noqa: BLE001
        log.exception("onboarding chart build failed for %s", message.from_user.id)
        await wait.edit_text(_copy(
            user,
            "Не получилось собрать карту сейчас. Данные не потерялись — попробуй ещё раз через минуту "
            "или укажи ближайший крупный город.",
            "I could not build the chart right now. Your data is safe — try again in a minute "
            "or enter a nearby major city.",
        ))
        return

    await users.update(db, message.from_user.id, birth_city=city, birth_lat=lat,
                       birth_lon=lon, tz=tz,
                       chart_json=json.dumps(chart, ensure_ascii=False),
                       onboarding_step="confirm")

    sun = chart["sun"]
    moon = next((item for item in chart.get("planets", [])
                 if item.get("name") in {"Луна", "Moon"}), None)
    precision_value = user["birth_time_precision"] or "exact"
    precision_ru = ("Время точное" if precision_value == "exact"
                    else "Время приблизительное — дома и Асцендент не используются")
    precision_en = ("Exact birth time" if precision_value == "exact"
                    else "Approximate time — houses and Ascendant are not used")
    summary = _copy(
        user,
        "🌌 <b>Твои данные</b>\n\n"
        f"Имя: <b>{tg_esc(user['name'] or '—')}</b>\n"
        f"Дата: <b>{tg_esc(user['birth_date'] or '—')}</b>\n"
        f"Время: <b>{tg_esc(user['birth_time'] or '—')}</b> · {precision_ru}\n"
        f"Город: <b>{tg_esc(city)}</b>\n\n"
        f"Солнце в <b>{tg_esc(sun['sign'])}</b> · {tg_esc(sun['element'])}\n"
        f"Луна: <b>{tg_esc((moon or {}).get('sign', '—'))}</b>\n\n"
        "Всё верно? После подтверждения выберем способ чтения карты.",
        "🌌 <b>Your details</b>\n\n"
        f"Name: <b>{tg_esc(user['name'] or '—')}</b>\n"
        f"Date: <b>{tg_esc(user['birth_date'] or '—')}</b>\n"
        f"Time: <b>{tg_esc(user['birth_time'] or '—')}</b> · {precision_en}\n"
        f"City: <b>{tg_esc(city)}</b>\n\n"
        f"Sun in <b>{tg_esc(sun['sign'])}</b> · {tg_esc(sun['element'])}\n"
        f"Moon: <b>{tg_esc((moon or {}).get('sign', '—'))}</b>\n\n"
        "Does this look right? We will choose how to read your chart next.",
    )
    await wait.edit_text(summary, reply_markup=confirmation_kb(_lang(user)))
    await state.set_state(Onb.confirm)
    await analytics.track(db, "onboarding_step", message.from_user.id,
                          props={"step": "confirm"}, surface="bot")


@router.callback_query(Onb.confirm, F.data == "onb:confirm")
async def onb_confirm(cb: CallbackQuery, state: FSMContext, db):
    user = await users.get(db, cb.from_user.id)
    await users.update(db, cb.from_user.id, onboarding_step="technique")
    await state.set_state(Onb.technique)
    await cb.message.edit_text(_copy(
        user,
        "✨ Как ты хочешь исследовать карту?\n\n<b>Астрологический разбор</b> — факты карты → аспекты → интерпретация.\n\n<b>Натальная история Ленорман</b> — карта рождения → символы → narrative exploration.",
        "✨ How would you like to explore your chart?\n\n<b>Astrology reading</b> — chart facts → aspects → interpretation.\n\n<b>Lenormand natal story</b> — birth chart → symbols → narrative exploration.",
    ), reply_markup=technique_kb(_lang(user)))
    await cb.answer()


@router.callback_query(Onb.confirm, F.data == "onb:edit")
async def onb_edit_prompt(cb: CallbackQuery, state: FSMContext, db):
    user = await users.get(db, cb.from_user.id)
    await cb.message.edit_text(_copy(user, "Что изменить?", "What would you like to change?"),
                               reply_markup=onboarding_edit_kb(_lang(user)))
    await cb.answer()


@router.callback_query(F.data.startswith("onb:edit:"))
async def onb_edit_field(cb: CallbackQuery, state: FSMContext, db):
    field = cb.data.split(":", 2)[2]
    user = await users.get(db, cb.from_user.id)
    state_map = {"name": Onb.name, "date": Onb.date, "time": Onb.time, "city": Onb.city}
    if field not in state_map:
        await cb.answer("Этот шаг уже закрыт", show_alert=True)
        return
    await state.set_state(state_map[field])
    await users.update(db, cb.from_user.id, onboarding_step=field)
    prompts = {
        "name": ("Как тебя называть?", "What should I call you?"),
        "date": ("Напиши дату рождения — например 21 июня 1999.", "Send your birth date — for example June 21 1999."),
        "time": ("Выбери или напиши время рождения.", "Choose or type your birth time."),
        "city": ("Напиши город рождения.", "Send your birth city."),
    }
    text = _copy(user, *prompts[field])
    await cb.message.edit_text(text, reply_markup=time_kb(_lang(user)) if field == "time" else back_menu())
    await cb.answer()


@router.callback_query(F.data == "onb:back")
async def onb_back(cb: CallbackQuery, state: FSMContext, db):
    user = await users.get(db, cb.from_user.id)
    current = await state.get_state()
    if current == Onb.time.state:
        await state.set_state(Onb.date)
        await users.update(db, cb.from_user.id, onboarding_step="date")
        text = _copy(user, "Вернёмся к дате рождения. Напиши её в любом понятном формате.", "Let’s return to your birth date. Send it in any clear format.")
    elif current == Onb.city.state:
        await state.set_state(Onb.time)
        await users.update(db, cb.from_user.id, onboarding_step="time")
        text = _copy(user, "Вернёмся ко времени рождения.", "Let’s return to your birth time.")
    elif current == Onb.confirm.state:
        await state.set_state(Onb.city)
        await users.update(db, cb.from_user.id, onboarding_step="city")
        text = _copy(user, "Напиши город рождения ещё раз.", "Send your birth city again.")
    else:
        await state.clear()
        text = _copy(user, "Пауза сохранена. Нажми /start, когда захочешь продолжить.", "Paused here. Press /start when you want to continue.")
    await cb.message.edit_text(text, reply_markup=back_menu())
    await cb.answer()


@router.callback_query(Onb.technique, F.data.startswith("technique:"))
async def onb_technique(cb: CallbackQuery, state: FSMContext, db):
    technique = cb.data.split(":", 1)[1]
    if technique not in {"astrology", "lenormand"}:
        await cb.answer("Unknown technique", show_alert=True)
        return
    await users.update(db, cb.from_user.id, natal_technique=technique,
                       natal_technique_version="v1", onboarding_step="persona")
    user = await users.get(db, cb.from_user.id)
    await analytics.track(db, "technique_selected", cb.from_user.id,
                          props={"technique": technique}, surface="bot")
    await state.set_state(Onb.oracle_name)
    await cb.message.edit_text(_copy(
        user,
        "Теперь выберем характер нашего разговора. Можно оставить вариант по умолчанию.",
        "Now choose the character of our conversation. You can keep the default.",
    ), reply_markup=personas_kb(await persona_list(db)))
    await cb.answer()


@router.callback_query(F.data.startswith("persona:"))
async def onb_persona(cb: CallbackQuery, state: FSMContext, db):
    code = cb.data.split(":", 1)[1]
    known = {p["code"] for p in await persona_list(db)}
    if code not in known:
        code = "friend"
    await users.update(db, cb.from_user.id, persona=code)

    user = await users.get(db, cb.from_user.id)
    if user["onboarded"]:
        # смена образа из профиля — онбординг проходить заново не нужно
        await cb.message.edit_text(_copy(
            user,
            "Хорошо. Теперь я буду говорить с тобой иначе 🌙",
            "All right. I will speak to you differently now 🌙",
        ), reply_markup=back_menu())
        await cb.answer(_copy(user, "Образ изменён", "Persona updated"))
        return

    await state.set_state(Onb.oracle_name)
    persona = next(p for p in await persona_list(db) if p["code"] == code)
    await cb.message.edit_text(_copy(
        user,
        f"{persona['emoji']} Я — {persona['title'].lower()}.\n"
        "Дай мне имя (или напиши «сама» — выберу из древних):",
        f"{persona['emoji']} I am {persona['title']}.\n"
        "Give me a name (or write ‘myself’ and I will choose an ancient one):",
    ))
    await cb.answer()


ANCIENT_NAMES = ("Лилит", "Селена", "Аврора", "Веда", "Итара", "Нимуэ", "Кассандра")


@router.message(Onb.oracle_name, F.text)
async def onb_oracle_name(message: Message, state: FSMContext, db):
    name = message.text.strip()[:30]
    if name.lower() in ("сама", "сам", "выбери", "не знаю", "myself"):
        from ..core.stable import stable_seed
        name = ANCIENT_NAMES[stable_seed(message.from_user.id) % len(ANCIENT_NAMES)]
    await users.update(db, message.from_user.id, oracle_name=name, onboarded=1, onboarding_step=None)
    await state.clear()

    user = await users.get(db, message.from_user.id)
    from ..services import limits
    allowance = await limits.allowance(db, user, check_followup=False)
    await analytics.track(db, analytics.E_ONBOARD_DONE, message.from_user.id, surface="bot")
    unit = {"day": "вопросов сегодня", "week": "вопросов за 7 дней", "month": "сообщений AI в месяц"}.get(allowance.period, "доступных вопросов")
    unit_en = {"day": "questions today", "week": "questions in 7 days", "month": "AI messages this month"}.get(allowance.period, "available questions")
    await analytics.track(db, "onboarding_completed", message.from_user.id, props={"technique": user["natal_technique"]}, surface="bot")
    await message.answer(_copy(
        user,
        f"✨ Я — <b>{tg_esc(name)}</b>, и я знаю твою карту, {tg_esc(user['name'])}.\n\n"
        f"У тебя {f'<b>{allowance.limit}</b> {unit}' if allowance.limit else 'свободный доступ к превью и сохранённым результатам'}.\n\n"
        "Что хочется понять яснее? Просто напиши вопрос — я сама выберу нужный путь.",
        f"✨ I am <b>{tg_esc(name)}</b>, and I know your chart, {tg_esc(user['name'])}.\n\n"
        f"You have {f'<b>{allowance.limit}</b> {unit_en}' if allowance.limit else 'free access to previews and saved results'}.\n\n"
        "What would you like to understand more clearly? Just ask — I will choose the right path.",
    ), reply_markup=await _menu(db, message.from_user.id))
    chart = users.chart_of(user)
    sun = (chart or {}).get("sun") or {}
    moon = next((p for p in (chart or {}).get("planets", []) if p.get("name") in {"Луна", "Moon"}), None)
    if sun:
        await message.answer(_copy(
            user,
            f"🔎 <b>Первое наблюдение</b>\nТвоё Солнце в {tg_esc(sun.get('sign', '—'))} — отправная точка карты, а Луна в {tg_esc((moon or {}).get('sign', '—'))} показывает, как ты проживаешь чувства.\n\nСпроси меня о том, что сейчас действительно важно.",
            f"🔎 <b>First insight</b>\nYour Sun in {tg_esc(sun.get('sign', '—'))} is the starting point of the chart, while the Moon in {tg_esc((moon or {}).get('sign', '—'))} describes how you process feelings.\n\nAsk me about what actually matters to you right now.",
        ), reply_markup=ask_starters_kb("en" if user["lang"] == "en" else "ru"))


# ─────────────────────────────── промокод ─────────────────────────────────────

def _promo_text(granted: dict) -> str:
    """Что именно получил пользователь — говорим конкретно, а не «код принят»."""
    item = granted.get("granted") or {}
    kind = item.get("kind")
    if kind == "plan":
        return (f"🎟 <b>Золотой билет принят!</b>\n"
                f"Тебе открыто {item.get('days', 0)} дней доступа "
                f"«{item.get('title', 'VIP')}». ✨")
    if kind == "crystals":
        return f"🎟 Принято! +✦{item.get('amount', 0)} Кристаллов ✨"
    if kind in ("spread", "report", "question"):
        return f"🎟 Принято! Открыто: {item.get('title', 'подарок')} ✨"
    return "🎟 Код принят ✨"


@router.message(Command("promo"))
async def promo_cmd(message: Message, state: FSMContext):
    await state.set_state(Promo.waiting)
    await message.answer("Введи промокод — золотой билет: 🎟")


@router.callback_query(F.data == "promo")
async def promo_cb(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Promo.waiting)
    await cb.message.answer("Введи промокод — золотой билет: 🎟")
    await cb.answer()


@router.message(Promo.waiting, F.text)
async def promo_enter(message: Message, state: FSMContext, db):
    await state.clear()
    granted = await billing.redeem_promo(db, message.from_user.id,
                                         message.text.strip())
    menu = await _menu(db, message.from_user.id)
    if granted:
        await message.answer(_promo_text(granted), reply_markup=menu)
    else:
        await message.answer(
            "Этот код не отзывается... Проверь написание — возможно, он уже "
            "активирован или истёк 🌙", reply_markup=menu)


# ─────────────────────────────── помощь ───────────────────────────────────────

@router.message(Command("help"))
async def help_cmd(message: Message, db):
    disclaimer = await content.get_setting(
        db, "disclaimer",
        "Оракул создан для самопознания и вдохновения.")
    faq = await content.list_content(db, "faq", active_only=True)
    lines = ["🔮 <b>Как я работаю</b>", ""]
    for item in faq[:4]:
        lines.append(f"<b>{item['title']}</b>\n{item['body']}\n")
    lines += [
        "<b>Команды</b>",
        "/start — начать заново · /today — прогноз дня",
        "/promo — промокод · /help — эта справка",
        "/delete_me — удалить мои данные",
        "",
        f"<i>{disclaimer}</i>",
    ]
    await message.answer("\n".join(lines),
                         reply_markup=await _menu(db, message.from_user.id))


@router.message(Command("delete_me"))
async def delete_me(message: Message, state: FSMContext, db):
    """Право на удаление данных — обязательное для сервиса с датами рождения."""
    await state.clear()
    await message.answer(
        "Если ты хочешь, чтобы я забыла тебя — я забуду: сотру дату рождения, "
        "карту, дневник, память и переписку.\n\n"
        "Напиши <b>УДАЛИТЬ</b> заглавными буквами, чтобы подтвердить.")
    await state.set_state(DeleteMe.confirm)


@router.message(DeleteMe.confirm, F.text)
async def delete_me_confirm(message: Message, state: FSMContext, db):
    await state.clear()
    if message.text.strip().upper() != "УДАЛИТЬ":
        await message.answer("Отменила. Я остаюсь с тобой 🌙",
                             reply_markup=await _menu(db, message.from_user.id))
        return
    await users.anonymize(db, message.from_user.id)
    await analytics.track(db, "self_delete", message.from_user.id)
    await message.answer(
        "Готово. Я стёрла всё, что о тебе знала.\n"
        "Если однажды захочешь начать заново — просто напиши /start 🕯")
