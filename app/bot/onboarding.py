"""Знакомство: /start, промокод из ссылки, данные рождения, образ и имя Оракула.

Онбординг — самое дорогое место продукта: здесь теряется больше всего людей.
Поэтому шагов минимум, каждый объясняет, зачем он нужен, а после расчёта карты
пользователь сразу получает «три откровения» — первую ценность до любой оплаты.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date

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
from .keyboards import back_menu, gender_kb, main_menu, personas_kb

log = logging.getLogger("oracle.bot.onboarding")
router = Router()

DATE_RE = re.compile(r"^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})$")
TIME_RE = re.compile(r"^(\d{1,2})[:.](\d{2})$")

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
    name = State()
    gender = State()
    date = State()
    time = State()
    city = State()
    oracle_name = State()


class Promo(StatesGroup):
    waiting = State()


class DeleteMe(StatesGroup):
    confirm = State()


async def _is_admin(db, tg_id: int) -> bool:
    return bool(await admin_repo.resolve_role(db, tg_id))


async def _menu(db, tg_id: int):
    return main_menu(is_admin=await _is_admin(db, tg_id))


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
        await message.answer(_copy(
            user,
            f"С возвращением, {user['name']} 🌙\nЯ здесь. О чём поговорим?",
            f"Welcome back, {user['name']} 🌙\nI’m here. What would you like to explore?",
        ), reply_markup=await _menu(db, message.from_user.id))
        return
    await state.set_state(Onb.name)
    text = (WELCOME_FALLBACK_EN if _lang(user) == "en"
            else await content.get_text(db, "copy", "welcome", WELCOME_FALLBACK))
    await message.answer(text)


# ─────────────────────────────── шаги FSM ─────────────────────────────────────

@router.message(Onb.name, F.text)
async def onb_name(message: Message, state: FSMContext, db):
    name = message.text.strip()[:40]
    user = await users.get(db, message.from_user.id)
    if not name:
        await message.answer(_copy(user, "Как мне тебя называть? ✨", "What should I call you? ✨"))
        return
    await users.update(db, message.from_user.id, name=name)
    await state.set_state(Onb.gender)
    await message.answer(
        _copy(
            user,
            f"{name}... красивое имя, в нём есть свет. 💫\n\n"
            "Чтобы подобрать форму обращения, выбери свой пол. Это можно изменить позже.",
            f"{name}... a beautiful name with its own light. 💫\n\n"
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
    await users.update(db, cb.from_user.id, gender=gender)
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
    match = DATE_RE.match(message.text.strip())
    if not match:
        await message.answer(_copy(user, "Напиши дату как <b>ДД.ММ.ГГГГ</b> 🙏", "Please use <b>DD.MM.YYYY</b> format 🙏"))
        return
    day, month, year = (int(match.group(i)) for i in (1, 2, 3))
    try:
        birth = date(year, month, day)
    except ValueError:
        await message.answer(_copy(user, "Такой даты не существует... проверь, пожалуйста 🌙", "That date does not exist — please check it 🌙"))
        return
    if not 1900 <= year <= date.today().year:
        await message.answer(_copy(user, "Проверь год рождения 🌙", "Please check the birth year 🌙"))
        return
    await users.update(db, message.from_user.id, birth_date=birth.isoformat())
    await state.set_state(Onb.time)
    await message.answer(_copy(
        user,
        "Знаешь ли ты <b>время</b> рождения? (например 14:30)\n"
        "Если не знаешь точно — напиши «не знаю», я справлюсь. 🌙\n\n"
        "<i>Время нужно для домов и асцендента — без него карта тоже получится, просто чуть менее подробной.</i>",
        "Do you know your <b>birth time</b>? (for example, 14:30)\n"
        "If you do not know it exactly, write ‘I don’t know’ — I can still continue. 🌙\n\n"
        "<i>Time is used for houses and the ascendant. Your chart will still work without it, just with less detail.</i>",
    ))


@router.message(Onb.time, F.text)
async def onb_time(message: Message, state: FSMContext, db):
    user = await users.get(db, message.from_user.id)
    match = TIME_RE.match(message.text.strip().lower())
    if match and 0 <= int(match.group(1)) < 24 and 0 <= int(match.group(2)) < 60:
        await users.update(db, message.from_user.id,
                           birth_time=f"{int(match.group(1)):02d}:{match.group(2)}",
                           birth_time_known=1)
    else:
        # полдень — нейтральная середина суток: ошибка по домам минимальна
        await users.update(db, message.from_user.id, birth_time="12:00",
                           birth_time_known=0)
    await state.set_state(Onb.city)
    city_question = _g(user, "город, где ты родилась", "город, где ты родился", "город рождения")
    await message.answer(_copy(
        user,
        f"И последнее: <b>{city_question}</b>? 🏙",
        "And one last detail: your <b>birth city</b>? 🏙",
    ))


@router.message(Onb.city, F.text)
async def onb_city(message: Message, state: FSMContext, db):
    city = message.text.strip()[:60]
    user = await users.get(db, message.from_user.id)
    wait = await message.answer(_copy(
        user,
        "🌌 <i>Собираю звёзды в твою карту...</i>",
        "🌌 <i>Gathering the stars for your chart...</i>",
    ))

    # оба вызова уходят в отдельный поток: геокодирование ходит в сеть, а расчёт
    # эфемерид держит GIL — синхронно они вешали бота для всех остальных
    lat, lon, tz = await geo.resolve_city_async(city, db)
    chart = await astro.compute_chart_async(
        user["birth_date"], user["birth_time"], city, lat, lon, tz,
        time_known=bool(user["birth_time_known"]),
    )
    await users.update(db, message.from_user.id, birth_city=city, birth_lat=lat,
                       birth_lon=lon, tz=tz,
                       chart_json=json.dumps(chart, ensure_ascii=False))

    sun = chart["sun"]
    asc = chart.get("ascendant")
    reveal = _copy(
        user,
        "\n".join([
            "⭐ <b>Твоя карта построена.</b>",
            "",
            f"{sun['symbol']} Солнце в <b>{sun['sign']}</b> — стихия {sun['element']}.",
        ]),
        "\n".join([
            "⭐ <b>Your chart is ready.</b>",
            "",
            f"{sun['symbol']} Your Sun is in <b>{sun['sign']}</b> — {sun['element']} element.",
        ]),
    ).split("\n")
    if asc:
        reveal.append(_copy(
            user,
            f"↗️ Асцендент в <b>{asc['sign']}</b> — каким тебя видят с первого взгляда.",
            f"↗️ Ascendant in <b>{asc['sign']}</b> — how people see you at first glance.",
        ))
    reveal += _copy(
        user,
        "\n".join([
            "", "Уже вижу три вещи о тебе:",
            "1️⃣ Ты сильнее, чем позволяешь себе казаться.",
            f"2️⃣ Твоя стихия ({sun['element']}) подсказывает, как тебе принимать решения.",
            "3️⃣ Один вопрос ты носишь в себе прямо сейчас — задашь его мне первым. 😉",
            "", "Теперь выбери, <b>кем я буду для тебя</b>:",
        ]),
        "\n".join([
            "", "I can already see three things about you:",
            "1️⃣ You are stronger than you allow yourself to appear.",
            f"2️⃣ Your element ({sun['element']}) hints at how you make decisions.",
            "3️⃣ One question lives within you right now — let it be the first one you ask. 😉",
            "", "Now choose <b>who I will be for you</b>:",
        ]),
    ).split("\n")
    await wait.edit_text("\n".join(reveal))
    await message.answer("🔮", reply_markup=personas_kb(await persona_list(db)))


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
    await users.update(db, message.from_user.id, oracle_name=name, onboarded=1)
    await state.clear()

    user = await users.get(db, message.from_user.id)
    from ..services import limits
    allowance = await limits.allowance(db, user, check_followup=False)
    await analytics.track(db, analytics.E_ONBOARD_DONE, message.from_user.id)
    await message.answer(_copy(
        user,
        f"✨ Теперь я — <b>{name}</b>, и я знаю твою карту, {user['name']}.\n\n"
        f"У тебя есть <b>{allowance.limit} вопроса в день</b> и "
        f"{users.sub_days_left(user)} дней полного доступа. "
        "Просто напиши мне свой первый вопрос — о любви, деньгах, пути... "
        "Я отвечу по твоим звёздам. 🌙",
        f"✨ I am now <b>{name}</b>, and I know your chart, {user['name']}.\n\n"
        f"You have <b>{allowance.limit} questions per day</b> and "
        f"{users.sub_days_left(user)} days of full access. "
        "Simply send me your first question — about love, money, or your path... "
        "I will answer through your stars. 🌙",
    ), reply_markup=await _menu(db, message.from_user.id))


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
