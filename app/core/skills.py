"""Скиллы — инструменты, которые LLM вызывает через tool-use.

Каждый скилл состоит из трёх частей:
- `schema` — описание для модели (что это и когда звать);
- `run(db, user, args) -> str` — детерминированное исполнение: считает КОД;
- guide — правила трактовки, которые подмешиваются в результат, чтобы модель
  разбирала данные по правилам школы, а не как получится.

Ключевой инвариант продукта: модель никогда не выдумывает карты, планеты и
арканы — она получает готовый расчёт и объясняет его. Отсюда и «правдивость»,
на которой держится доверие к сервису.

Правила трактовки берутся из БД (`content_items(kind='guide')`), а константы в
этом файле — значение по умолчанию. Так тексты правятся в админке без деплоя, но
пустая база или сбой запроса не ломают ответ.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

from ..repo import content as content_repo
from ..repo import dialog as dialog_repo
from ..repo import readings as readings_repo
from . import astro, memory, tarot
from .matrix import compute_matrix, matrix_brief

log = logging.getLogger("oracle.skills")

# ---------------------------------------------------------------- guides

TAROT_GUIDE = (
    "[Правила трактовки Таро — школа Райдера-Уэйта-Смит (RWS)]\n"
    "1) Колода символическая (А.Уэйт + Памела Колман Смит, 1909): смысл несёт картина — "
    "фигуры, жесты, цвета, сюжет. Смотри на образ карты и символы, а не на словарь значений.\n"
    "2) Родной порядок старших: Сила — VIII, Правосудие — XI (НЕ наоборот, как в Марселе).\n"
    "3) Старший аркан = архетип-веха (Шут-начало, Маг-воля, Жрица-интуиция, Императрица-"
    "изобилие, Император-порядок, Иерофант-традиция, Влюблённые-выбор, Колесница-воля/победа, "
    "Сила-кротость, Отшельник-поиск, Колесо-циклы, Правосудие-равновесие, Повешенный-пауза/взгляд, "
    "Смерть-трансформация, Умеренность-алхимия, Дьявол-зависимость, Башня-прорыв, Звезда-надежда, "
    "Луна-страхи/подсознание, Солнце-радость/ясность, Суд-призвание, Мир-целостность). "
    "Тревожные арканы объясняй ресурсом (Смерть=завершение, Башня=слом старого ради правды, "
    "Дьявол=что можно отпустить), а не пугая.\n"
    "4) Младшие: масти = стихии и сферы — Жезлы=огонь/дело, Кубки=вода/чувства, Мечи=воздух/"
    "мысли, Пентакли=земля/деньги/тело. Числа 1-10 = прогрессия (Туз=потенциал, 2=выбор, "
    "3=рост, 4=стабильность, 5=кризис, 6=гармония, 7=испытание, 8=движение, 9=почти итог, "
    "10=завершение цикла): значение = число × сфера масти. Двор = люди/роли: Паж=вестник/ученик, "
    "Рыцарь=порыв/действие, Королева=зрелая внутренняя энергия, Король=мастерство/воля.\n"
    "5) Перевёрнутая — НЕ «плохо» и НЕ «смысл наоборот»: по Грир это энергия заблокированная "
    "или смещённая внутрь (не прожита, спрятана), задержанная во времени, или теневая сторона "
    "архетипа (та же Сила — но робость). Вопрос: «какая часть этой карты сейчас ей недоступна "
    "и что ей нужно?».\n"
    "6) Связывай карты в один сюжет по позициям расклада: что причина, что следствие, где поворот. "
    "Паттерны: перевес одной масти = ведущая сфера, повторы чисел = сквозная тема, старшие = главные "
    "вехи.\n"
    "7) Обязательно: ТОЛЬКО выпавшие карты, ответ на ЕЁ вопрос + 1 конкретный мягкий совет в конце. "
    "Говори вероятностно («карта может указывать на…»), без фатализма: выбор всегда за ней."
)

NATAL_GUIDE = (
    "[Правила натальной астрологии]\n"
    "1) Планета = что, знак = как, дом = где. 2) Не пугай «тяжёлыми» планетами: Сатурн — "
    "учитель, Плутон — трансформация. 3) Привязывай к её реальной жизни из памяти. "
    "4) Если время рождения неточное — не делай выводов по домам/асценденту."
)

TRANSIT_GUIDE = (
    "[Правила прогнозов]\n"
    "1) Опирайся на фазу Луны и сезон Солнца из данных. 2) Прогноз = настроение дня + "
    "1 сфера внимания + 1 конкретный совет. 3) Никогда не предсказывай беды и болезни."
)

MATRIX_GUIDE = (
    "[Правила Матрицы Судьбы]\n"
    "1) Аркан — это энергия с плюсом и минусом: покажи оба полюса и как выйти в плюс. "
    "2) Аркан судьбы — главный вектор, центр — зона комфорта. 3) Говори про ресурс, а не приговор."
)

COMPAT_GUIDE = (
    "[Правила совместимости]\n"
    "1) Стихии: огонь+воздух и земля+вода дружат; противоположности — рост через трение. "
    "2) Никогда не говори «вы не подходите» — покажи, ЧТО укрепит союз. "
    "3) Балл — ориентир, не вердикт. Если называешь его, бери РОВНО то число, что дано "
    "в данных: клиентка видит его же на шкале, разные цифры её запутают."
)

DIARY_GUIDE = (
    "[Правила работы с дневником]\n"
    "1) Опирайся на её собственные слова из записей — цитируй коротко. "
    "2) Отмечай динамику («три недели назад ты писала иначе»). "
    "3) Не оценивай и не поучай: отражай и поддерживай."
)

CAREER_GUIDE = (
    "[Правила разбора карьеры]\n"
    "1) Предназначение читай по связке: 10-й дом и его управитель, Сатурн "
    "(через что растёт), Солнце (что даёт силы), аркан судьбы из Матрицы. "
    "2) Не называй конкретную профессию как приговор — описывай РОЛЬ и среду, "
    "в которой ей хорошо, и оставь выбор за ней. "
    "3) «Лучшее время» бери только из деловых окон по Луне, не выдумывай даты; "
    "растущая — начинать, убывающая — завершать, полнолуние — не подписывать. "
    "4) Про людей и знаки говори через стихии и потребности, без «этот знак вам "
    "враг». 5) Денег и должностей не обещай: говори о её ресурсе и цене себя."
)

PRACTICE_GUIDE = (
    "[Правила работы с практиками]\n"
    "1) Практика — это дисциплина, а не магия: подчёркивай непрерывность дней. "
    "2) Никогда не обещай результата к сроку и не пугай последствиями пропуска. "
    "3) Опирайся на «знаки продвижения» из описания практики — они помогают "
    "заметить эффект и не бросить. 4) Если её запрос про здоровье или тяжёлое "
    "состояние — практику не назначай, направь к специалисту."
)

DEFAULT_GUIDES = {
    "tarot": TAROT_GUIDE, "natal": NATAL_GUIDE, "transit": TRANSIT_GUIDE,
    "matrix": MATRIX_GUIDE, "compat": COMPAT_GUIDE, "diary": DIARY_GUIDE,
    "career": CAREER_GUIDE, "practice": PRACTICE_GUIDE,
}


async def guide(db, code: str) -> str:
    """Правила трактовки: из БД, иначе встроенные."""
    default = DEFAULT_GUIDES.get(code, "")
    if db is None:
        return default
    try:
        return await content_repo.get_text(db, "guide", code, default) or default
    except Exception as e:  # noqa: BLE001
        log.warning("правила %s из БД недоступны: %s", code, e)
        return default


# ---------------------------------------------------------------- helpers

ELEMENT_SCORE = {
    frozenset(["огонь"]): 88, frozenset(["земля"]): 86,
    frozenset(["воздух"]): 85, frozenset(["вода"]): 90,
    frozenset(["огонь", "воздух"]): 84, frozenset(["земля", "вода"]): 87,
    frozenset(["огонь", "земля"]): 58, frozenset(["огонь", "вода"]): 52,
    frozenset(["воздух", "земля"]): 56, frozenset(["воздух", "вода"]): 63,
}

# Вклады в балл пары. Балл должен объясняться, а не выглядеть магией.
ASPECT_BONUS = {"trine": 6, "sextile": 4, "conjunction": 3,
                "square": -4, "opposition": -3}


def synastry_bonus(aspects: list[dict]) -> int:
    """Суммарный вклад синастрических аспектов в балл пары."""
    return sum(ASPECT_BONUS.get(a.get("code", ""), 0) for a in aspects)


def _element_bonus(a: str | None, b: str | None) -> int:
    """Созвучие двух стихий: +4 созвучные, -3 в трении, 0 нейтрально."""
    if not a or not b:
        return 0
    if a == b:
        return 4
    if frozenset((a, b)) in (frozenset(["огонь", "воздух"]),
                             frozenset(["земля", "вода"])):
        return 4
    if frozenset((a, b)) in (frozenset(["огонь", "земля"]),
                             frozenset(["огонь", "вода"])):
        return -3
    return 0  # воздух-земля и воздух-вода — нейтрально: не питают и не режут


def _compat(user_birth: str, partner_birth: str) -> dict:
    """Совместимость пары по реальным точкам карты.

    Формула одна на весь продукт: бот, Mini App и ответ Оракула обязаны называть
    одно и то же число, иначе клиентка видит противоречие и теряет доверие.
    Базой служат стихии Солнц, поверх — Луна (душа), Венера (любовь) и крест
    «Солнце-Луна» — это сильнейшие синастрические нити по датам без времени.
    Балл детерминирован для пары и симметричен: не зависит от того, кто спросил.
    """
    d1 = datetime.strptime(user_birth, "%Y-%m-%d").date()
    d2 = datetime.strptime(partner_birth, "%Y-%m-%d").date()
    s1, _, e1 = astro.sun_sign_precise(d1)
    s2, _, e2 = astro.sun_sign_precise(d2)
    m1, v1 = astro.moon_venus_signs(d1)
    m2, v2 = astro.moon_venus_signs(d2)

    base = ELEMENT_SCORE.get(frozenset([e1, e2]), 60)
    if e1 == e2:
        broken = f"обе {e1}"
    elif frozenset([e1, e2]) in (frozenset(["огонь", "воздух"]),
                                 frozenset(["земля", "вода"])):
        broken = f"{e1} и {e2} — питают друг друга"
    else:
        broken = f"{e1} и {e2} — рост через трение"
    breakdown = [{"title": "Стихии Солнца", "value": base, "note": broken}]
    score = base

    lunar = _element_bonus(m1[1] if m1 else None, m2[1] if m2 else None)
    if lunar:
        breakdown.append({"title": "Луна (душа)", "value": lunar,
                          "note": "как вы чувствуете друг друга без слов"})
        score += lunar

    venus = _element_bonus(v1[1] if v1 else None, v2[1] if v2 else None)
    if venus:
        breakdown.append({"title": "Венера (любовь)", "value": venus,
                          "note": "как вы притягиваетесь и цените друг друга"})

        score += venus

    cross = (_element_bonus(m2[1] if m2 else None, e1)
             + _element_bonus(m1[1] if m1 else None, e2))
    if cross:
        breakdown.append({"title": "Крест Солнце-Луна", "value": cross,
                          "note": "его Солнце встречает её Луну и наоборот — "
                                  "самая живая нить синастрии"})
        score += cross

    score = max(35, min(98, score))
    return {"you": {"sign": s1, "element": e1},
            "partner": {"sign": s2, "element": e2},
            "score": score, "breakdown": breakdown,
            "verdict": _verdict(score, e1, e2)}


_ELEMENT_VERB = {
    ("огонь", "огонь"): "союз-пламя: вы зажигаете друг друга",
    ("земля", "земля"): "союз-основа: вы строите надёжное",
    ("воздух", "воздух"): "союз-ветер: вы свободно дышите вместе",
    ("вода", "вода"): "союз-глубина: вы чувствуете друг друга без слов",
}


def _verdict(score: int, e1: str, e2: str) -> str:
    """Вердикт по стихии пары — «пламя» уходит только паре из огня."""
    by_style = _ELEMENT_VERB.get((e1, e2)) or _ELEMENT_VERB.get((e2, e1))
    if score >= 80:
        return by_style or "союз-гармония: вы дополняете друг друга"
    if score >= 60:
        return "союз-рост: разность стихий учит вас обоих"
    return "союз-урок: трение сильное, но именно оно шлифует"


# ---------------------------------------------------------------- skills

async def _run_draw_tarot(db, user, args) -> str:
    n = max(1, min(int(args.get("n", 3) or 3), 12))
    spread_code = str(args.get("spread", "") or "")
    item = tarot.spread(spread_code) if spread_code else None
    positions = item["positions"] if item and spread_code in tarot.SPREADS else None
    if positions:
        n = len(positions)
    cards = tarot.draw(n)
    title = item["title"] if item else "свободный"
    return (f"{await guide(db, 'tarot')}\n\nРасклад: {title}\n"
            f"Карты:\n{tarot.cards_text(cards, positions)}")


async def _run_get_chart(db, user, args) -> str:
    try:
        chart = json.loads(user["chart_json"] or "{}")
    except (TypeError, ValueError):
        chart = {}
    if not chart:
        return "карта ещё не построена — попроси клиентку пройти /start"
    known = "точное" if user["birth_time_known"] else "НЕТОЧНОЕ (дома не использовать)"
    lines = [await guide(db, "natal"), "", f"Время рождения: {known}",
             astro.chart_brief(chart, time_known=bool(user["birth_time_known"]))]
    houses = chart.get("houses") or []
    if houses and user["birth_time_known"]:
        lines.append("Куспиды домов: " + "; ".join(
            f"{h['n']}-й в {h['sign']}" for h in houses))
    return "\n".join(lines)


async def _run_get_transits(db, user, args) -> str:
    sky = astro.today_sky()
    try:
        chart = json.loads(user["chart_json"] or "{}")
    except (TypeError, ValueError):
        chart = {}
    sun = (chart.get("sun") or {}).get("sign", "?")
    # Реальное небо из эфемерид, а не только «лунная фаза»: знаки Луны и Венеры
    # меняются медленно и дают контекст для трактовки чувств и ценностей.
    extras = []
    moon, venus = astro.moon_venus_signs(date.today())
    if moon:
        extras.append(f"Луна в {moon[0]}")
    if venus:
        extras.append(f"Венера в {venus[0]}")
    sky_line = (f"Луна: {sky['moon']['emoji']} {sky['moon']['name']} "
                f"({sky['moon']['advice']}), лунный день ~{sky['moon']['day']}")
    if extras:
        sky_line += ", " + ", ".join(extras)
    return (f"{await guide(db, 'transit')}\n\nСегодня: сезон Солнца в "
            f"{sky['sun_season']['sign']}, {sky_line}. Её Солнце: {sun}.")


async def _run_moon_week(db, user, args) -> str:
    """Лунный календарь на неделю — для планирования, а не «на сегодня»."""
    today = date.today()
    lines = []
    for i in range(7):
        d = today + timedelta(days=i)
        phase = astro.moon_phase(d)
        lines.append(f"{d.strftime('%d.%m')}: {phase['emoji']} {phase['name']} "
                     f"({phase['day']}-й лунный день) — {phase['advice']}")
    return f"{await guide(db, 'transit')}\n\nЛунная неделя:\n" + "\n".join(lines)


# Что фаза Луны даёт деловым решениям. Астрологический электив в его самой
# практичной части: начинать — на растущей, завершать и увольняться — на убывающей.
_CAREER_WINDOWS = {
    "Новолуние": ("старт", "закладывать намерение и планировать, но не подписывать"),
    "Растущий серп": ("старт", "первые переговоры, отклики, знакомства"),
    "Первая четверть": ("решение", "принимать решение и снимать сомнения"),
    "Растущая Луна": ("действие", "подписывать, запускать, просить повышение"),
    "Полнолуние": ("осторожно", "эмоции громче фактов — не подписывать и не ссориться"),
    "Убывающая Луна": ("завершение", "закрывать долги, доделывать хвосты"),
    "Последняя четверть": ("завершение", "увольняться, расставаться с лишним"),
    "Старый серп": ("пауза", "отдыхать и не начинать нового"),
}


async def _run_career_windows(db, user, args) -> str:
    """Деловые окна на две недели: когда действовать, когда молчать."""
    days = max(7, min(int(args.get("days", 14) or 14), 30))
    today = date.today()
    lines = []
    for i in range(days):
        d = today + timedelta(days=i)
        phase = astro.moon_phase(d)
        kind, advice = _CAREER_WINDOWS.get(phase["name"], ("нейтрально", "обычный день"))
        weekday = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"][d.weekday()]
        lines.append(f"{d.strftime('%d.%m')} ({weekday}) {phase['emoji']} "
                     f"{phase['name']} — [{kind}] {advice}")
    return (f"{await guide(db, 'career')}\n\nДеловые окна на {days} дней:\n"
            + "\n".join(lines))


async def _run_get_matrix(db, user, args) -> str:
    if not user["birth_date"]:
        return "нет данных рождения"
    m = compute_matrix(user["birth_date"])
    return f"{await guide(db, 'matrix')}\n\n{matrix_brief(m)}"


async def _run_compatibility(db, user, args) -> str:
    partner = str(args.get("partner_birth_date", "") or "").strip()
    try:
        datetime.strptime(partner, "%Y-%m-%d")
    except ValueError:
        return "нужна дата партнёра в формате YYYY-MM-DD — уточни её у клиентки"
    if not user["birth_date"]:
        return "нет даты рождения клиентки"
    c = _compat(user["birth_date"], partner)
    return (f"{await guide(db, 'compat')}\n\nОна: {c['you']['sign']} "
            f"({c['you']['element']}), партнёр: {c['partner']['sign']} "
            f"({c['partner']['element']}). Балл совместимости: {c['score']}/100 — "
            f"{c['verdict']}.")


async def _run_list_partners(db, user, args) -> str:
    partners = await readings_repo.list_partners(db, user["tg_id"])
    if not partners:
        return "в её окружении пока никто не сохранён"
    return "Люди, которых она сохранила:\n" + "\n".join(
        f"- {p['name'] or 'без имени'} ({p['relation']}), рождение {p['birth_date']}"
        for p in partners)


async def _run_save_memory(db, user, args) -> str:
    fact = str(args.get("fact", "") or "").strip()
    if not fact:
        return "нечего сохранять"
    saved = await memory.remember(db, user["tg_id"], fact,
                                  kind=str(args.get("kind", "fact") or "fact"))
    return "сохранено" if saved else "уже знаю это — усилила важность"


async def _run_recall_memory(db, user, args) -> str:
    query = str(args.get("query", "") or "")
    mems = await memory.recall(db, user["tg_id"], query, limit=12)
    return "\n".join(f"- {m}" for m in mems) or "память пуста"


async def _run_recall_diary(db, user, args) -> str:
    entries = await dialog_repo.get_diary(db, user["tg_id"], limit=10)
    if not entries:
        return "дневник пока пуст"
    streak = await dialog_repo.diary_streak(db, user["tg_id"])
    lines = [f"{e['created_at'][:10]}: {e['text'][:200]}" for e in entries]
    return (f"{await guide(db, 'diary')}\n\nСтрик: {streak} дн.\n"
            "Последние записи:\n" + "\n".join(lines))


async def _run_suggest_practice(db, user, args) -> str:
    """Каталог практик под её запрос + что у неё уже идёт.

    Модель не придумывает ритуалы: она выбирает из каталога, потому что шаги,
    сроки и предупреждения (например, «это к психологу») выверены в контенте.
    """
    from ..services import practices as practices_svc

    category = str(args.get("category", "") or "").strip() or None
    items = await practices_svc.list_for_user(db, user, category=category)
    if not items:
        return "подходящих практик в каталоге нет"
    lines = [await guide(db, "practice"), ""]
    running = [p for p in items if p["started"] and not p["finished"]]
    if running:
        lines.append("Уже идут у неё:")
        lines += [f"- {p['title']}: день {p['day_index']} из {p['days']}, "
                  f"стрик {p['streak']}" for p in running]
        lines.append("")
    lines.append("Каталог (код — название — для чего — сколько дней):")
    for p in items[:14]:
        lines.append(f"- {p['code']} — {p['title']} — {p['goal']} — "
                     f"{p['days']} дн." + (" [уже идёт]" if p["started"] else ""))
    lines.append("\nПредложи ОДНУ практику, объясни почему именно её, назови срок "
                 "и скажи, что открыть её можно в разделе «Дневник» → «Практики».")
    return "\n".join(lines)


SKILLS: dict[str, dict] = {
    "draw_tarot": {
        "run": _run_draw_tarot,
        "schema": {
            "name": "draw_tarot",
            "description": ("Вытянуть карты Таро (реальный случайный выбор из 78 карт). "
                            "Зови, когда нужен расклад или клиентка просит «что говорят карты»."),
            "input_schema": {"type": "object", "properties": {
                "n": {"type": "integer", "description": "Число карт 1-12"},
                "spread": {"type": "string",
                           "description": "Код расклада: one, three, love, choice, "
                                          "money, career, work, celtic, year"},
            }, "required": ["n"]},
        },
    },
    "get_chart": {
        "run": _run_get_chart,
        "schema": {
            "name": "get_chart",
            "description": ("Натальная карта клиентки (планеты/знаки/дома/аспекты). Зови "
                            "для вопросов о характере, предназначении, «почему я такая»."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_transits": {
        "run": _run_get_transits,
        "schema": {
            "name": "get_transits",
            "description": ("Небо сегодня: фаза Луны, лунный день, сезон Солнца. "
                            "Зови для прогнозов на день/«как сегодня действовать»."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_moon_week": {
        "run": _run_moon_week,
        "schema": {
            "name": "get_moon_week",
            "description": ("Лунный календарь на 7 дней вперёд. Зови, когда клиентка "
                            "выбирает день для решения, поездки, разговора, стрижки."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_career_windows": {
        "run": _run_career_windows,
        "schema": {
            "name": "get_career_windows",
            "description": ("Деловые окна на ближайшие недели: когда начинать, "
                            "подписывать, просить повышение, а когда — завершать "
                            "и не принимать решений. Зови для вопросов о карьере, "
                            "переговорах, увольнении, запуске дела."),
            "input_schema": {"type": "object", "properties": {
                "days": {"type": "integer", "description": "Горизонт, 7-30 дней"},
            }},
        },
    },
    "suggest_practice": {
        "run": _run_suggest_practice,
        "schema": {
            "name": "suggest_practice",
            "description": ("Каталог практик и мантр (мантры, денежные, любовные, "
                            "энергия) и то, что клиентка уже проходит. Зови, когда "
                            "она спрашивает «что мне делать», просит ритуал, "
                            "практику или мантру."),
            "input_schema": {"type": "object", "properties": {
                "category": {"type": "string",
                             "description": "mantra|money|love|energy"},
            }},
        },
    },
    "get_matrix": {
        "run": _run_get_matrix,
        "schema": {
            "name": "get_matrix",
            "description": ("Матрица Судьбы клиентки (арканы). Зови для вопросов о "
                            "предназначении, кармических задачах, денежной/любовной линии."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_compatibility": {
        "run": _run_compatibility,
        "schema": {
            "name": "get_compatibility",
            "description": ("Совместимость с партнёром по датам рождения. Если дата "
                            "партнёра неизвестна — сначала спроси её у клиентки."),
            "input_schema": {"type": "object", "properties": {
                "partner_birth_date": {"type": "string",
                                       "description": "Дата партнёра YYYY-MM-DD"},
            }, "required": ["partner_birth_date"]},
        },
    },
    "list_partners": {
        "run": _run_list_partners,
        "schema": {
            "name": "list_partners",
            "description": ("Список людей, которых клиентка сохранила (партнёр, коллега, "
                            "подруга) с их датами рождения. Зови, когда она говорит "
                            "«он», «она» без уточнения."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "save_memory": {
        "run": _run_save_memory,
        "schema": {
            "name": "save_memory",
            "description": ("Сохранить важный факт о клиентке (люди, события, чувства, "
                            "цели, даты). Зови всякий раз, когда она делится личным."),
            "input_schema": {"type": "object", "properties": {
                "fact": {"type": "string"},
                "kind": {"type": "string",
                         "description": "person|event|emotion|goal|fact"},
            }, "required": ["fact"]},
        },
    },
    "recall_memory": {
        "run": _run_recall_memory,
        "schema": {
            "name": "recall_memory",
            "description": "Поиск в памяти о клиентке по ключевым словам (люди, темы).",
            "input_schema": {"type": "object", "properties": {
                "query": {"type": "string"}}, "required": ["query"]},
        },
    },
    "recall_diary": {
        "run": _run_recall_diary,
        "schema": {
            "name": "recall_diary",
            "description": ("Последние записи её дневника и стрик. Зови, когда речь о "
                            "самочувствии, динамике, «как у меня дела в последнее время»."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
}

#: Полный набор инструментов — для главного агента.
TOOLS = [s["schema"] for s in SKILLS.values()]


def tools_for(names: list[str] | tuple[str, ...] | None) -> list[dict]:
    """Схемы только перечисленных скиллов — набор инструментов агента.

    Специализированному агенту лишние инструменты вредят: модель начинает
    отвечать не по своей теме, и «Таролог» уходит в астрологию.
    """
    if not names:
        return list(TOOLS)
    return [SKILLS[n]["schema"] for n in names if n in SKILLS]


async def execute(db, user, name: str, args: dict) -> str:
    skill = SKILLS.get(name)
    if not skill:
        return "неизвестный инструмент"
    try:
        return await skill["run"](db, user, args or {})
    except Exception as e:  # noqa: BLE001
        log.warning("скилл %s упал: %s", name, e)
        return f"ошибка инструмента: {e}"
