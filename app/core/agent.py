"""Готовые сценарии генерации: прогноз дня, трактовки, разборы, отчёты.

Свободный диалог живёт в `core/agents/` — там агент сам решает, какие инструменты
позвать. Здесь наоборот: сценарии с фиксированной структурой, где карты, планеты
и арканы уже выбраны кодом, а модель только пишет текст. Такое разделение
экономит токены (не нужен tool-use цикл) и делает результат предсказуемым.

Публичное API (используется ботом, Mini App и планировщиком):
    ask_oracle, interpret_reading, daily_forecast_cached, interpret_compat,
    build_report, monthly_report, extract_memory_llm
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import date, datetime, timezone

from ..repo import dialog as dialog_repo
from ..repo import readings as readings_repo
from ..repo import users as users_repo
from . import agents, astro, llm, memory, skills, tarot
from . import matrix as mx
from .stable import stable_seed

log = logging.getLogger("oracle.agent")


# ---------------------------------------------------------------- вопрос

async def ask_oracle(db, user, question: str, *, agent: str = "oracle",
                     thread_id: int | None = None,
                     allowance_line: str = "",
                     extra_rules: str = "") -> str:
    """Свободный вопрос агенту. Совместимая точка входа для бота и API."""
    return await agents.answer(db, user, question, agent=agent,
                               thread_id=thread_id, allowance_line=allowance_line,
                               extra_rules=extra_rules)


# ---------------------------------------------------------------- таро

async def interpret_reading(db, user, title: str, cards: list[dict],
                            positions: list[str]) -> str:
    """Трактовка КОНКРЕТНЫХ вытянутых карт (карты выбрал код, не модель)."""
    cards_block = tarot.cards_text(cards, positions)
    if llm.enabled():
        try:
            system = await agents.system_for(db, user, agents.get("oracle"))
            user_msg = (f"{await skills.guide(db, 'tarot')}\n\n"
                        f"Я сделала расклад «{title}». Выпали карты:\n{cards_block}\n\n"
                        f"Дай глубокую тёплую трактовку именно этих карт для меня: "
                        f"разбери по позициям, свяжи в один сюжет и закончи одним "
                        f"практическим шагом.")
            text = await llm.complete(system, user_msg, tier="main",
                                      max_tokens=min(1400, 220 * max(3, len(cards))),
                                      purpose="tarot", tg_id=user["tg_id"], db=db)
            if len(text.strip()) >= 120:
                return text
        except Exception as e:  # noqa: BLE001
            log.warning("трактовка расклада ушла в офлайн: %s", e)
    return _reading_offline(user, title, cards, cards_block)


def _reading_offline(user, title: str, cards: list[dict], cards_block: str) -> str:
    name = user["name"] or "милая"
    key = cards[len(cards) // 2]
    reversed_note = ("Перевёрнутые карты просят не торопиться. "
                     if any(c["reversed"] for c in cards) else "")
    return (
        f"🎴 <b>{title}</b>\n\n{cards_block}\n\n"
        f"{name}, сердце этого расклада — {key['emoji']} <b>{key['name']}</b>: "
        f"{key['meaning']}. Карты легли так, что прошлое уже отпускает тебя, "
        f"а будущее ждёт твоего шага. {reversed_note}"
        f"Прислушайся к центральной карте — она про то, что происходит прямо сейчас. 🌙"
    )


# ---------------------------------------------------------------- прогноз дня

#: Генерация прогноза — LLM-вызов; Mini App и бот могут спросить прогноз на
#: одно утро одновременно. Замок по (клиентка, день): второй ждущий после замка
#: перепроверяет кеш и берёт готовый текст, а не генерирует свой.
_forecast_locks: dict[tuple[int, str], asyncio.Lock] = {}


async def daily_forecast_cached(db, user, chart: dict | None = None) -> str:
    """Прогноз дня — один раз в сутки на клиентку.

    Без кеша каждое открытие Mini App заново оплачивало бы генерацию и показывало
    другой прогноз на тот же день; бот и приложение обязаны говорить одно и то же.
    """
    day = users_repo.user_today(user)
    cached = await readings_repo.get_forecast(db, user["tg_id"], day)
    if cached:
        return cached
    if len(_forecast_locks) > 5000:
        _forecast_locks.clear()   # ключи прошлых дней не нужны
    lock = _forecast_locks.setdefault((user["tg_id"], day), asyncio.Lock())
    async with lock:
        cached = await readings_repo.get_forecast(db, user["tg_id"], day)
        if cached:
            return cached
        text = await daily_forecast(db, user, chart if chart is not None
                                   else users_repo.chart_of(user))
        await readings_repo.save_forecast(db, user["tg_id"], day, text)
        return text


async def daily_forecast(db, user, chart: dict) -> str:
    sky = astro.today_sky()
    if llm.enabled():
        try:
            brief = (astro.chart_brief(chart, time_known=bool(user["birth_time_known"]))
                     if chart else "-")
            memories = await dialog_repo.get_memories(db, user["tg_id"], limit=5)
            oracle_name = user["oracle_name"] or "Лилит"
            system = (f"Ты — {oracle_name}, личный оракул клиентки {user['name']}. "
                      f"Её карта: {brief}. Память о ней: "
                      f"{'; '.join(memories) or '-'}.\n"
                      f"{await skills.guide(db, 'transit')}")
            card = card_of_day(user)
            user_msg = (f"Небо сегодня: Луна {sky['moon']['emoji']} "
                        f"{sky['moon']['name']} ({sky['moon']['advice']}), "
                        f"лунный день ~{sky['moon']['day']}, Солнце в "
                        f"{sky['sun_season']['sign']}.\n"
                        f"Карта дня: {card['emoji']} {card['name']}"
                        f"{' (перевёрнутая)' if card['reversed'] else ''} — "
                        f"{card['meaning']}.\n"
                        f"Напиши мой персональный прогноз на сегодня: 4-6 строк, "
                        f"тепло, 1 конкретный совет, обыграй карту дня. Начни с 🌅.")
            text = await llm.complete(system, user_msg, tier="lite", max_tokens=400,
                                      purpose="forecast", tg_id=user["tg_id"], db=db)
            if text.strip():
                return text
        except Exception as e:  # noqa: BLE001
            log.warning("прогноз дня ушёл в офлайн: %s", e)
    return _forecast_offline(user, chart, sky)


def _forecast_offline(user, chart: dict, sky: dict) -> str:
    rnd = random.Random(stable_seed(date.today().isoformat(), user["tg_id"]))
    sun = (chart or {}).get("sun") or {}
    sign = sun.get("sign", "твоего знака")
    moon = sky["moon"]
    card = card_of_day(user)
    moods = ["день ясности", "день тихой силы", "день знаков", "день выбора",
             "день отдачи"]
    return (
        f"🌅 Доброе утро! Сегодня для {sign} — {rnd.choice(moods)}.\n"
        f"{moon['emoji']} Луна: {moon['name']} — {moon['advice']}.\n"
        f"Карта дня: {card['emoji']} <b>{card['name']}</b> — {card['meaning']}.\n"
        f"Совет: "
        f"{'не торопи события' if card['reversed'] else 'действуй в первой половине дня'}. ✨"
    )


def card_of_day(user) -> dict:
    """Карта дня: детерминирована датой и клиенткой — одна в боте и в Mini App.

    Перевёрнутость тоже имитирует честную тасовку (~50/50), но сохраняет
    стабильность для одного дня: клиентка видит ту же карту утром и вечером.
    """
    rnd = random.Random(stable_seed(users_repo.user_today(user), user["tg_id"]))
    card = dict(tarot.DECK[rnd.randrange(len(tarot.DECK))])
    card["reversed"] = bool(rnd.getrandbits(1))
    return card


# ---------------------------------------------------------------- совместимость

async def _synastry_data(db, user, partner_date: str) -> str | None:
    """Блок настоящей синастрии: карты обеих + аспекты пары.

    None — если хотя бы одна карта не полная (тогда остаётся только базовый
    разбор по датам). Карта партнёра берётся из сохранённых людей по дате,
    полную мы строим, когда клиентка указывала город/время.
    """
    try:
        chart = json.loads(user["chart_json"] or "{}")
        if chart.get("mode") != "full" or not chart.get("planets"):
            return None
        partner = await readings_repo.find_partner_by_date(
            db, user["tg_id"], partner_date)
        if not partner:
            return None
        pchart = json.loads(partner["chart_json"] or "{}") if partner["chart_json"] else {}
        if pchart.get("mode") != "full" or not pchart.get("planets"):
            return None
        aspects = astro.synastry_aspects(chart["planets"], pchart["planets"])
        lines = [
            "Её карта:",
            astro.chart_brief(chart, time_known=bool(user["birth_time_known"])),
            "",
            f"Карта {partner['name'] or 'партнёра'}:",
            astro.chart_brief(pchart,
                              time_known=bool(partner["birth_time"])),
            "",
            "Синастрические аспекты пары:",
        ]
        if aspects:
            lines.append(astro.synastry_aspects_text(aspects))
            bonus = skills.synastry_bonus(aspects)
            if bonus:
                lines.append(f"Вклад аспектов в балл пары: {bonus:+d}")
        else:
            lines.append("(орбных аспектов между картами не найдено)")
        return "\n".join(lines)
    except (TypeError, ValueError):
        return None


async def interpret_compat(db, user, partner_date: str,
                           partner_name: str = "") -> str:
    """Полный разбор пары. Настоящая синастрия берётся из сохранённых карт,
    если они есть; иначе — разбор по датам (Солнце/Луна/Венера)."""
    key = f"syn:{partner_date}:{partner_name}"
    cached = await readings_repo.get_synastry(db, user["tg_id"], key)
    if cached and cached["answer"]:
        return cached["answer"]

    data = skills._compat(user["birth_date"], partner_date)
    who = partner_name or "он"
    brief = (f"я — {data['you']['sign']} ({data['you']['element']}), "
             f"{who} — {data['partner']['sign']} ({data['partner']['element']}), "
             f"балл {data['score']}/100")
    block = await _synastry_data(db, user, partner_date)
    synast = f"\n\nДанные синастрии (считает код):\n{block}" if block else ""
    text = ""
    if llm.enabled():
        try:
            system = await agents.system_for(db, user, agents.get("astro"))
            user_msg = (f"{await skills.guide(db, 'compat')}\n\nРазбор совместимости: "
                        f"{brief}.{synast}\n"
                        f"Расскажи, что нас соединяет, где будет трение и что укрепит "
                        f"союз. Опирайся на данные расчёта, не выдумывай аспекты."
                        f" Тепло, конкретно, 5-7 абзацев.")
            text = await llm.complete(system, user_msg, tier="main", max_tokens=1000,
                                      purpose="compat", tg_id=user["tg_id"], db=db)
        except Exception as e:  # noqa: BLE001
            log.warning("разбор пары ушёл в офлайн: %s", e)
    if len(text.strip()) < 120:
        text = (
            f"💞 <b>Совместимость</b>\n\n"
            f"Ты — {data['you']['sign']} ({data['you']['element']}), "
            f"{who} — {data['partner']['sign']} ({data['partner']['element']}).\n"
            f"Балл пары: <b>{data['score']}/100</b> — {data['verdict']}.\n\n"
            f"Стихии подсказывают: не переделывай его, а используй разность как "
            f"опору. Спроси меня про конкретную ситуацию между вами — разложу "
            f"карты. 🌙")
    await readings_repo.cache_synastry(db, user["tg_id"], key, data["score"],
                                       data["breakdown"], text)
    return text


# ---------------------------------------------------------------- отчёты

#: Купленные разборы. Каждый — длинный структурированный текст, который остаётся
#: в профиле навсегда (в отличие от ответа в чате).
REPORTS = {
    "natal": {
        "title": "Полный разбор натальной карты",
        "agent": "astro",
        "guide": "natal",
        "sections": ["Кто ты по своей карте (Солнце, Луна, Асцендент)",
                     "Твои сильные стороны и таланты",
                     "Личность и характер: планеты в знаках",
                     "Сферы жизни: планеты по домам",
                     "Ключевые аспекты и что они дают",
                     "Задачи и точки роста",
                     "Как тебе принимать решения"],
    },
    "matrix": {
        "title": "Матрица Судьбы — полный разбор",
        "agent": "numero",
        "guide": "matrix",
        "sections": ["Личный аркан: твой характер",
                     "Духовный аркан: внутренняя опора",
                     "Родовой аркан: что пришло из семьи",
                     "Аркан судьбы: главный вектор жизни",
                     "Центр матрицы: зона комфорта",
                     "Линия любви", "Линия денег",
                     "Как выходить в плюс каждого аркана"],
    },
    "synastry": {
        "title": "Синастрия: совместимость пары",
        "agent": "astro",
        "guide": "compat",
        "sections": ["Что вас притянуло", "Как вы говорите друг с другом",
                     "Где будет трение", "Чувства и близость",
                     "Быт и деньги", "Перспектива союза",
                     "Что укрепит вас двоих"],
    },
    "solar": {
        # честно про метод: это прогноз года по карте и текущему небу, а не
        # астрономический соляр (момент возврата Солнца в натальный градус)
        "title": "Годовой прогноз по картам",
        "agent": "astro",
        "guide": "transit",
        "sections": ["Главная тема года", "Первые три месяца",
                     "Середина года", "Финал года",
                     "Лучшие месяцы для решений", "Что стоит отпустить",
                     "Один совет на весь год"],
    },
    "career": {
        "title": "Карьера и предназначение",
        "agent": "astro",
        "guide": "career",
        "sections": ["Твоё предназначение: к чему ты предрасположена",
                     "Как ты работаешь: сильные стороны и режим",
                     "Что тебя тормозит в профессии",
                     "Среда и люди: с кем тебе легко, с кем тяжело",
                     "Деньги и самооценка: как ты назначаешь себе цену",
                     "Когда действовать: периоды роста и периоды паузы",
                     "Ближайший шаг: что сделать в этом месяце"],
    },
}


async def build_report(db, user, kind: str, *, partner_date: str | None = None,
                       partner_name: str = "", force: bool = False) -> dict:
    """Собирает купленный разбор и сохраняет его в профиль.

    Готовый отчёт переиспользуется: разбор натальной карты не меняется, и
    генерировать его заново значит платить за токены дважды. Соляр и месячный
    отчёт привязаны к периоду и потому пересобираются на новый период.
    """
    spec = REPORTS.get(kind)
    if not spec:
        raise ValueError(f"неизвестный разбор: {kind}")
    period = None
    if kind == "solar":
        period = str(date.today().year)
    if kind == "synastry" and partner_date:
        period = partner_date

    if not force:
        existing = await readings_repo.get_report(db, user["tg_id"], kind, period)
        if existing and existing["body"]:
            return {"title": existing["title"], "body": existing["body"],
                     "kind": kind, "period": period, "cached": True}

    data_block = await _report_data(db, user, kind, partner_date, partner_name)
    body = ""
    if llm.enabled():
        try:
            system = await agents.system_for(db, user, agents.get(spec["agent"]))
            sections = "\n".join(f"{i}. {s}" for i, s in enumerate(spec["sections"], 1))
            user_msg = (
                f"{await skills.guide(db, spec['guide'])}\n\n"
                f"Данные расчёта:\n{data_block}\n\n"
                f"Напиши для меня «{spec['title']}» строго по этим разделам:\n"
                f"{sections}\n\n"
                f"Каждый раздел — заголовок в теге <b> и 2-4 абзаца живой речи. "
                f"Опирайся только на данные расчёта выше, ничего не выдумывай. "
                f"Пиши обо мне лично, тепло и по делу.")
            body = await llm.complete(system, user_msg, tier="main", max_tokens=4000,
                                      purpose=f"report:{kind}", tg_id=user["tg_id"],
                                      db=db)
        except Exception as e:  # noqa: BLE001
            log.warning("разбор %s ушёл в офлайн: %s", kind, e)
    if len(body.strip()) < 200:
        body = _report_offline(user, spec, data_block)

    await readings_repo.save_report(db, user["tg_id"], kind, spec["title"], body,
                                    period=period,
                                    meta={"partner": partner_name or None})
    return {"title": spec["title"], "body": body, "kind": kind, "period": period,
            "cached": False}


async def _report_data(db, user, kind: str, partner_date: str | None,
                       partner_name: str) -> str:
    """Детерминированные данные для разбора — их считает код."""
    if kind == "natal":
        return await skills.execute(db, user, "get_chart", {})
    if kind == "matrix":
        return await skills.execute(db, user, "get_matrix", {})
    if kind == "synastry":
        if not partner_date:
            raise ValueError("для синастрии нужна дата партнёра")
        compat = skills._compat(user["birth_date"], partner_date)
        chart = await skills.execute(db, user, "get_chart", {})
        core = (f"{chart}\n\nПартнёр: {partner_name or 'без имени'}, "
                f"{compat['partner']['sign']} ({compat['partner']['element']}), "
                f"дата {partner_date}. Балл пары: {compat['score']}/100 — "
                f"{compat['verdict']}.")
        block = await _synastry_data(db, user, partner_date)
        return core + ("\n\n" + block if block else "")
    if kind == "solar":
        chart = await skills.execute(db, user, "get_chart", {})
        sky = astro.today_sky()
        return (f"{chart}\n\nГод: {date.today().year}. Сейчас Солнце в "
                f"{sky['sun_season']['sign']}, Луна {sky['moon']['name']}. "
                f"День рождения: {user['birth_date']}.")
    if kind == "career":
        # Карьерный разбор строится на трёх источниках сразу: 10-й дом и Сатурн
        # из карты, аркан судьбы из Матрицы и ближайшие деловые окна по Луне.
        chart = await skills.execute(db, user, "get_chart", {})
        matrix = await skills.execute(db, user, "get_matrix", {})
        windows = await skills.execute(db, user, "get_career_windows", {})
        return f"{chart}\n\n{matrix}\n\n{windows}"
    return ""


def _report_offline(user, spec: dict, data_block: str) -> str:
    """Разбор без модели: структура и реальные данные, без «воды» от LLM."""
    name = user["name"] or "милая"
    parts = [f"<b>{spec['title']}</b>", "",
             f"{name}, вот что говорят твои расчёты.", "",
             "<i>Данные карты:</i>", data_block, "",
             "<b>Разделы разбора</b>"]
    parts += [f"• {s}" for s in spec["sections"]]
    parts += ["", "Связь со звёздами сейчас неровная — подробный текст по этим "
                  "разделам придёт, как только она восстановится. Расчёты уже "
                  "сохранены и не изменятся. 🌙"]
    return "\n".join(parts)


async def monthly_report(db, user) -> str:
    """Итог месяца: сколько всего было и что из этого следует."""
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    existing = await readings_repo.get_report(db, user["tg_id"], "monthly", period)
    if existing and existing["body"]:
        return existing["body"]

    readings_n = await readings_repo.readings_count_since(db, user["tg_id"], 30)
    diary_n = await dialog_repo.diary_count_since(db, user["tg_id"], 30)
    streak = await dialog_repo.diary_streak(db, user["tg_id"])
    memories = await dialog_repo.get_memories(db, user["tg_id"], limit=12)

    body = ""
    if llm.enabled() and (readings_n or diary_n or memories):
        try:
            system = await agents.system_for(db, user, agents.get("keeper"))
            user_msg = (f"Мой месяц: раскладов {readings_n}, записей в дневнике "
                        f"{diary_n}, стрик {streak} дн. Что ты обо мне узнала за это "
                        f"время: {'; '.join(memories) or '-'}.\n"
                        f"Напиши тёплый итог месяца: что менялось, что повторялось, "
                        f"на что обратить внимание в следующем. 5-7 абзацев, "
                        f"начни с 🌙.")
            body = await llm.complete(system, user_msg, tier="main", max_tokens=1200,
                                      purpose="report:monthly", tg_id=user["tg_id"],
                                      db=db)
        except Exception as e:  # noqa: BLE001
            log.warning("месячный отчёт ушёл в офлайн: %s", e)
    if len(body.strip()) < 100:
        body = (f"🌙 <b>Твой месяц</b>\n\n"
                f"🎴 Раскладов: {readings_n}\n"
                f"📖 Записей в дневнике: {diary_n} (стрик {streak} дн.)\n"
                f"✦ Я запомнила о тебе {len(memories)} важных вещей.\n\n"
                f"Новый месяц — новое небо. Загляни утром за прогнозом ✨")

    await readings_repo.save_report(db, user["tg_id"], "monthly",
                                    "Итог месяца", body, period=period)
    return body


# ---------------------------------------------------------------- память

EXTRACT_PROMPT = (
    "Ты ведёшь досье клиентки для личного астролога. Извлеки из её сообщения "
    "0-3 факта, которые стоит помнить через месяц: люди и их имена, события, "
    "страхи, цели, важные даты, работа, здоровье.\n"
    "Правила: пиши фактами в третьем лице («её парня зовут Дима»), без оценок; "
    "не сохраняй сам вопрос, вежливости и общие слова; если помнить нечего — "
    "верни пустой массив.\n"
    "Ответ — ТОЛЬКО JSON-массив строк, без пояснений и без markdown."
)

#: Короче этого ответа lite-вызов экстракции не окупается (G23): реплики в духе
#: «поняла 🌙» фактов не несут, а стоимость — вызов модели и эмбеддинги.
EXTRACT_MIN_ANSWER = 120


def _parse_facts(raw: str) -> list[str]:
    """Достаёт массив строк из ответа модели, даже если он в ```-блоке."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
    text = text.removeprefix("json").strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        return []
    try:
        facts = json.loads(text[start:end + 1])
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(facts, list):
        return []
    return [f.strip() for f in facts
            if isinstance(f, str) and 3 < len(f.strip()) < 300]


async def extract_memory_llm(db, user, question: str, answer: str) -> None:
    """Фоновая экстракция фактов (дешёвая модель). Тихо пропускается без ключа.

    Сохраняем через `core.memory`: он склеивает переформулировки одного и того же
    факта по близости векторов, иначе память быстро забивалась повторами.
    """
    if not llm.enabled():
        return
    if len((answer or "").strip()) < EXTRACT_MIN_ANSWER:
        return                     # короткая реплика — без lite-вызова (G23)
    try:
        raw = await llm.complete(EXTRACT_PROMPT, question, tier="lite",
                                 max_tokens=300, purpose="memory_extract",
                                 tg_id=user["tg_id"], db=db)
    except Exception as e:  # noqa: BLE001
        log.debug("экстракция памяти пропущена: %s", e)
        return

    try:
        # один эмбеддинг-запрос на все факты, а не по одному на каждый (G23)
        await memory.remember_many(db, user["tg_id"], _parse_facts(raw)[:3])
    except Exception as e:  # noqa: BLE001
        log.debug("факты не сохранены: %s", e)

    # сводка «кто она» пересобирается редко и только когда фактов реально прибавилось
    try:
        if await memory.needs_summary(db, user["tg_id"]):
            await memory.build_summary(db, user)
    except Exception as e:  # noqa: BLE001
        log.debug("сводка профиля не обновлена: %s", e)
