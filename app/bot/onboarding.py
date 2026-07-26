"""Знакомство: /start, промокод из ссылки, данные рождения, образ и имя Оракула.

Онбординг — самое дорогое место продукта: здесь теряется больше всего людей.
Поэтому шагов минимум, каждый объясняет, зачем он нужен, а после расчёта карты
клиентка сразу получает «три откровения» — первую ценность до любой оплаты.
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
from .keyboards import back_menu, main_menu, personas_kb

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


class Onb(StatesGroup):
    name = State()
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
                       message.from_user.username)
    arg = (command.args or "").strip()

    ref_id = referrals.parse_ref(arg)
    if ref_id:
        result = await referrals.apply(db, message.from_user.id, ref_id)
        if result:
            await message.answer(
                f"💫 Подруга привела тебя ко мне — это добрый знак.\n"
                f"Вам обеим — по ✦{result['bonus']} Кристаллов ✨")
            try:
                await message.bot.send_message(
                    ref_id, f"🌟 Твоя подруга пришла к Оракулу — тебе ✦{result['bonus']}!")
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
                       message.from_user.username)
    await analytics.track(db, analytics.E_START, message.from_user.id)
    await _begin(message, state, db)


async def _begin(message: Message, state: FSMContext, db):
    user = await users.get(db, message.from_user.id)
    if user["onboarded"]:
        await state.clear()
        await message.answer(
            f"С возвращением, {user['name']} 🌙\nЯ здесь. О чём поговорим?",
            reply_markup=await _menu(db, message.from_user.id))
        return
    await state.set_state(Onb.name)
    text = await content.get_text(db, "copy", "welcome", WELCOME_FALLBACK)
    await message.answer(text)


# ─────────────────────────────── шаги FSM ─────────────────────────────────────

@router.message(Onb.name, F.text)
async def onb_name(message: Message, state: FSMContext, db):
    name = message.text.strip()[:40]
    if not name:
        await message.answer("Как мне тебя называть? ✨")
        return
    await users.update(db, message.from_user.id, name=name)
    await state.set_state(Onb.date)
    await message.answer(
        f"{name}... красивое имя, в нём есть свет. 💫\n\n"
        "Теперь — дата твоего рождения (в формате <b>ДД.ММ.ГГГГ</b>, "
        "например 21.06.1999):")


@router.message(Onb.date, F.text)
async def onb_date(message: Message, state: FSMContext, db):
    match = DATE_RE.match(message.text.strip())
    if not match:
        await message.answer("Напиши дату как <b>ДД.ММ.ГГГГ</b> 🙏")
        return
    day, month, year = (int(match.group(i)) for i in (1, 2, 3))
    try:
        birth = date(year, month, day)
    except ValueError:
        await message.answer("Такой даты не существует... проверь, пожалуйста 🌙")
        return
    if not 1900 <= year <= date.today().year:
        await message.answer("Проверь год рождения 🌙")
        return
    await users.update(db, message.from_user.id, birth_date=birth.isoformat())
    await state.set_state(Onb.time)
    await message.answer(
        "Знаешь ли ты <b>время</b> рождения? (например 14:30)\n"
        "Если не знаешь точно — напиши «не знаю», я справлюсь. 🌙\n\n"
        "<i>Время нужно для домов и асцендента — без него карта тоже "
        "получится, просто чуть менее подробной.</i>")


@router.message(Onb.time, F.text)
async def onb_time(message: Message, state: FSMContext, db):
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
    await message.answer("И последнее: <b>город</b>, где ты родилась? 🏙")


@router.message(Onb.city, F.text)
async def onb_city(message: Message, state: FSMContext, db):
    city = message.text.strip()[:60]
    wait = await message.answer("🌌 <i>Собираю звёзды в твою карту...</i>")

    # оба вызова уходят в отдельный поток: геокодирование ходит в сеть, а расчёт
    # эфемерид держит GIL — синхронно они вешали бота для всех остальных
    lat, lon, tz = await geo.resolve_city_async(city, db)
    user = await users.get(db, message.from_user.id)
    chart = await astro.compute_chart_async(user["birth_date"], user["birth_time"],
                                            city, lat, lon, tz)
    await users.update(db, message.from_user.id, birth_city=city, birth_lat=lat,
                       birth_lon=lon, tz=tz,
                       chart_json=json.dumps(chart, ensure_ascii=False))

    sun = chart["sun"]
    asc = chart.get("ascendant")
    reveal = [
        f"⭐ <b>Твоя карта построена.</b>",
        "",
        f"{sun['symbol']} Солнце в <b>{sun['sign']}</b> — стихия {sun['element']}.",
    ]
    if asc:
        reveal.append(f"↗️ Асцендент в <b>{asc['sign']}</b> — "
                      f"каким тебя видят с первого взгляда.")
    reveal += [
        "",
        "Уже вижу три вещи о тебе:",
        "1️⃣ Ты сильнее, чем позволяешь себе казаться.",
        f"2️⃣ Твоя стихия ({sun['element']}) подсказывает, как тебе принимать решения.",
        "3️⃣ Один вопрос ты носишь в себе прямо сейчас — задашь его мне первым. 😉",
        "",
        "Теперь выбери, <b>кем я буду для тебя</b>:",
    ]
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
        await cb.message.edit_text("Хорошо. Теперь я буду говорить с тобой иначе 🌙",
                                   reply_markup=back_menu())
        await cb.answer("Образ изменён")
        return

    await state.set_state(Onb.oracle_name)
    persona = next(p for p in await persona_list(db) if p["code"] == code)
    await cb.message.edit_text(
        f"{persona['emoji']} Я — {persona['title'].lower()}.\n"
        "Дай мне имя (или напиши «сама» — выберу из древних):")
    await cb.answer()


ANCIENT_NAMES = ("Лилит", "Селена", "Аврора", "Веда", "Итара", "Нимуэ", "Кассандра")


@router.message(Onb.oracle_name, F.text)
async def onb_oracle_name(message: Message, state: FSMContext, db):
    name = message.text.strip()[:30]
    if name.lower() in ("сама", "сам", "выбери", "не знаю"):
        from ..core.stable import stable_seed
        name = ANCIENT_NAMES[stable_seed(message.from_user.id) % len(ANCIENT_NAMES)]
    await users.update(db, message.from_user.id, oracle_name=name, onboarded=1)
    await state.clear()

    user = await users.get(db, message.from_user.id)
    from ..services import limits
    allowance = await limits.allowance(db, user, check_followup=False)
    await analytics.track(db, analytics.E_ONBOARD_DONE, message.from_user.id)
    await message.answer(
        f"✨ Теперь я — <b>{name}</b>, и я знаю твою карту, {user['name']}.\n\n"
        f"У тебя есть <b>{allowance.limit} вопроса в день</b> и "
        f"{users.sub_days_left(user)} дней полного доступа. "
        f"Просто напиши мне свой первый вопрос — о любви, деньгах, пути... "
        f"Я отвечу по твоим звёздам. 🌙",
        reply_markup=await _menu(db, message.from_user.id))


# ─────────────────────────────── промокод ─────────────────────────────────────

def _promo_text(granted: dict) -> str:
    """Что именно получила клиентка — говорим конкретно, а не «код принят»."""
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
