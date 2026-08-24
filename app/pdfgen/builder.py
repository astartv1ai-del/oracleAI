"""Сбор персонального разбора: расчёты → тексты → HTML.

Разбор строится на тех же расчётах, что и продукт: `core/astro` для карты,
`core/matrix` для арканов, `core/skills.guide` для правил трактовки. Модель
пишет только текст разделов и получает на вход готовые цифры — поэтому PDF не
может «выдумать» планету, которой нет в карте.

Работает и без LLM: тогда разделы собираются из реальных данных без литературной
части. Это честнее, чем не отдать заказ вообще.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime

from ..config import settings
from ..core import astro, geo, llm, skills
from ..core.matrix import compute_matrix
from ..repo import content
from . import layout

log = logging.getLogger("oracle.pdfgen")

#: Структура разбора. Порядок = порядок страниц; менять безопасно.
SECTIONS = [
    ("Кто ты по своей карте",
     "Солнце, Луна и Асцендент: ядро характера, чувства и то, какой тебя видят "
     "впервые. Объясни простыми словами, без терминов без расшифровки."),
    ("Твои сильные стороны",
     "Что даётся тебе легче, чем другим, и на что опираться в трудный момент. "
     "Опирайся на аспекты и положение планет в знаках."),
    ("Сферы жизни: планеты по домам",
     "Где именно в жизни разворачиваются твои главные темы. Если время рождения "
     "неточное — скажи об этом честно и работай по знакам."),
    ("Любовь и близость",
     "Венера и Луна: как ты любишь, что тебе нужно в отношениях и что ты "
     "принимаешь за любовь по ошибке."),
    ("Деньги и дело",
     "Второй и десятый дома, Сатурн, Юпитер: как ты зарабатываешь, что мешает "
     "просить свою цену и в чём твой профессиональный ресурс."),
    ("Матрица Судьбы: предназначение",
     "Арканы: личный, духовный, родовой, аркан судьбы и центр. Каждый — двумя "
     "полюсами (плюс и минус) и переходом из минуса в плюс."),
    ("Линия любви и линия денег",
     "Два аркана Матрицы, которые про отношения и про достаток. Что они дают и "
     "чего требуют."),
    ("Задачи и точки роста",
     "Через что ты растёшь: Сатурн, напряжённые аспекты, кармический вектор. "
     "Без запугивания — как задача, а не приговор."),
    ("Как тебе принимать решения",
     "Практический раздел: по каким признакам ты понимаешь, что решение твоё, "
     "и что делать, когда не понимаешь."),
    ("Год впереди",
     "Ближайшие двенадцать месяцев крупными мазками: главная тема, периоды "
     "действия и периоды паузы. Никаких точных дат и обещаний событий."),
]

SECTION_EN = {
    "Кто ты по своей карте": ("Who you are in your chart", "Sun, Moon and Ascendant: your core, feelings and first impression. Explain simply and define every technical term."),
    "Твои сильные стороны": ("Your strengths", "What may come more naturally and what to lean on in difficult moments. Use planets in signs and major aspects."),
    "Сферы жизни: планеты по домам": ("Life areas: planets by houses", "Where the main themes of the chart may unfold. If birth time is uncertain, say so and work by signs."),
    "Любовь и близость": ("Love and closeness", "Venus and Moon: needs, affection and boundaries in relationships, without deterministic claims."),
    "Деньги и дело": ("Money and work", "Second and tenth houses, Saturn and Jupiter: symbolic resources for work and practical reflection, not financial advice."),
    "Матрица Судьбы: предназначение": ("Destiny Matrix: purpose", "Personal, spiritual, ancestral, destiny and centre arcana, with constructive and difficult expressions."),
    "Линия любви и линия денег": ("Love line and money line", "Two Matrix arcana for relationship and resource themes, interpreted as reflection rather than a promise."),
    "Задачи и точки роста": ("Tasks and growth points", "Saturn, tense aspects and the symbolic lunar-node axis as hypotheses for growth, never as a sentence."),
    "Как тебе принимать решения": ("How you make decisions", "A practical reflection guide: signals, questions and small reversible experiments when you are unsure."),
    "Год впереди": ("The year ahead", "A non-predictive twelve-month reflection frame. Do not invent dates or promise events."),
}

SIGN_EN = {
    "Овен": "Aries", "Телец": "Taurus", "Близнецы": "Gemini", "Рак": "Cancer",
    "Лев": "Leo", "Дева": "Virgo", "Весы": "Libra", "Скорпион": "Scorpio",
    "Стрелец": "Sagittarius", "Козерог": "Capricorn", "Водолей": "Aquarius", "Рыбы": "Pisces",
}
POINT_EN = {
    "Солнце": "Sun", "Луна": "Moon", "Меркурий": "Mercury", "Венера": "Venus",
    "Марс": "Mars", "Юпитер": "Jupiter", "Сатурн": "Saturn", "Уран": "Uranus",
    "Нептун": "Neptune", "Плутон": "Pluto", "Раху (Северный узел)": "Rahu (North Node)",
    "Кету (Южный узел)": "Ketu (South Node)", "Лилит (Чёрная Луна)": "Lilith (Black Moon)",
    "Хирон": "Chiron", "Джуно": "Juno", "Церера": "Ceres", "Веста": "Vesta", "Паллада": "Pallas",
    "Асцендент": "Ascendant", "Середина неба": "Midheaven", "Десцендент": "Descendant", "Имум цели": "Imum Coeli",
}
ELEMENT_EN = {"огонь": "fire", "земля": "earth", "воздух": "air", "вода": "water"}
ARCANA_EN_NAME = {
    "Маг": "The Magician", "Жрица": "The High Priestess", "Императрица": "The Empress", "Император": "The Emperor",
    "Иерофант": "The Hierophant", "Влюблённые": "The Lovers", "Колесница": "The Chariot", "Справедливость": "Justice",
    "Отшельник": "The Hermit", "Колесо Фортуны": "Wheel of Fortune", "Сила": "Strength", "Повешенный": "The Hanged One",
    "Смерть": "Death", "Умеренность": "Temperance", "Дьявол": "The Devil", "Башня": "The Tower",
    "Звезда": "The Star", "Луна": "The Moon", "Солнце": "The Sun", "Суд": "Judgement",
    "Мир": "The World", "Шут": "The Fool",
}
ARCANA_EN_MEANING = {
    "Маг": "will, initiative and the ability to begin", "Жрица": "intuition, hidden knowledge and inner voice",
    "Императрица": "abundance, creativity and generative strength", "Император": "structure, order and leadership",
    "Иерофант": "mentorship, tradition and learning", "Влюблённые": "heart-led choice, partnership and harmony",
    "Колесница": "movement, victory and direction", "Справедливость": "balance, honesty and consequences",
    "Отшельник": "wisdom, self-search and solitude", "Колесо Фортуны": "turning points and changing circumstances",
    "Сила": "gentle strength and the integration of passion", "Повешенный": "a new perspective and growth through a pause",
    "Смерть": "transformation and the completion of cycles", "Умеренность": "balance, integration and proportion",
    "Дьявол": "desire, attachment and the shadow side", "Башня": "release from a false structure",
    "Звезда": "hope, inspiration and orientation", "Луна": "the subconscious, uncertainty and imagination",
    "Солнце": "joy, confidence and recognition", "Суд": "awakening, calling and accountability",
    "Мир": "wholeness and completion of a larger cycle", "Шут": "freedom, trust and a new path",
}
MATRIX_TITLE_EN = {
    "Личный аркан (характер)": "Personal arcana (character)", "Духовный аркан": "Spiritual arcana",
    "Родовая линия": "Ancestral line", "Линия предназначения": "Purpose line", "Центр матрицы": "Matrix centre",
    "Линия любви": "Love line", "Линия денег": "Money line",
}

TEXT = {
    "ru": {
        "title": "Полный отчёт натальной карты и Матрицы Судьбы",
        "summary": "Карта в цифрах",
        "reference": "Натальная карта: полный расчёт",
        "facts": ("Дата рождения", "Время рождения", "Место рождения", "Солнце", "Асцендент", "Луна", "Rahu / Раху", "Ketu / Кету", "Аркан судьбы"),
        "eyebrow": "ПЕРСОНАЛЬНЫЙ НАТАЛЬНЫЙ ОТЧЁТ", "perspective": "Перспектива", "node_mode": "Режим узлов",
        "engine": "Эфемеридный движок", "zodiac": "Зодиак", "houses": "Система домов", "precision": "Точность",
        "planets": "Планеты", "nodes": "Лунные узлы: Rahu и Ketu", "additional": "Дополнительные точки",
        "cusps": "Куспиды домов", "aspects": "Ключевые аспекты", "object": "Объект", "sign": "Знак",
        "degree": "Градус", "house": "Дом", "status": "Статус", "link": "Открыть проект",
        "exact_note": "Округлённые значения удобны для чтения, точные значения в скобках сохранены для проверки.",
        "true_node": "True Node", "direct": "директный", "retro": "ретроградный", "unknown": "неизвестно (карта по знакам)",
        "matrix": "Матрица Судьбы", "disclaimer": "Разбор создан для самопознания и вдохновения. Он не заменяет консультацию врача, психолога или юриста.",
        "ticket": "Твой золотой билет", "ticket_body": "30 дней полного доступа к личному AI-Оракулу.",
        "open_link": "Открой ссылку", "promo_help": "Введи код в боте командой /promo", "composed": "Составлено",
    },
    "en": {
        "title": "Full natal chart and Destiny Matrix report",
        "summary": "Your chart in numbers",
        "reference": "Natal chart: full calculation",
        "facts": ("Birth date", "Birth time", "Birth place", "Sun", "Ascendant", "Moon", "Rahu", "Ketu", "Destiny arcana"),
        "eyebrow": "PERSONAL NATAL REPORT", "perspective": "Perspective", "node_mode": "Node mode",
        "engine": "Ephemeris engine", "zodiac": "Zodiac", "houses": "House system", "precision": "Precision",
        "planets": "Planets", "nodes": "Lunar nodes: Rahu and Ketu", "additional": "Additional points",
        "cusps": "House cusps", "aspects": "Key aspects", "object": "Point", "sign": "Sign",
        "degree": "Degree", "house": "House", "status": "Status", "link": "Open project",
        "exact_note": "Rounded values are easier to read; exact values are kept in parentheses for verification.",
        "true_node": "True Node", "direct": "direct", "retro": "retrograde", "unknown": "unknown (sign-based chart)",
        "matrix": "Destiny Matrix", "disclaimer": "This report is for self-reflection and inspiration. It does not replace medical, psychological or legal advice.",
        "ticket": "Your golden ticket", "ticket_body": "30 days of full access to your personal AI Oracle.",
        "open_link": "Open this link", "promo_help": "Enter the code in the bot with /promo", "composed": "Prepared",
    },
}


def _lang(value: str | None) -> str:
    return "en" if (value or "").lower().startswith("en") else "ru"


def _text(lang: str, key: str):
    return TEXT[_lang(lang)][key]


def _section_title(title: str, lang: str) -> str:
    return SECTION_EN.get(title, (title, ""))[0] if _lang(lang) == "en" else title


def _section_brief(title: str, brief: str, lang: str) -> str:
    return SECTION_EN.get(title, (title, brief))[1] if _lang(lang) == "en" else brief


def _display_point(name: str, lang: str) -> str:
    return POINT_EN.get(name, name) if _lang(lang) == "en" else name


def _display_sign(sign: str, lang: str) -> str:
    return SIGN_EN.get(sign, sign) if _lang(lang) == "en" else sign


def _matrix_display(item: dict, lang: str) -> tuple[str, str, str]:
    if _lang(lang) != "en":
        return item.get("title", ""), item.get("arcana", ""), item.get("meaning", "")
    arcana = item.get("arcana", "")
    return (MATRIX_TITLE_EN.get(item.get("title", ""), item.get("title", "")),
            ARCANA_EN_NAME.get(arcana, arcana),
            ARCANA_EN_MEANING.get(arcana, item.get("meaning", "")))


def _display_precision(value: str, lang: str) -> str:
    if _lang(lang) == "ru":
        return value
    return {"exact": "exact", "date_only": "date only", "time_without_location": "time without location", "sun_only": "Sun only"}.get(value, value)


@dataclass
class Order:
    """Заказ на разбор: то, что приходит из CSV площадки или из CLI."""

    name: str
    birth_date: str                      # YYYY-MM-DD
    birth_time: str | None = None        # HH:MM, None — время неизвестно
    birth_city: str | None = None
    promo_code: str | None = None
    email: str = ""
    listing: str = ""
    lang: str = "ru"
    extras: dict = field(default_factory=dict)

    @property
    def time_known(self) -> bool:
        return bool(self.birth_time)


async def build_report_data(order: Order) -> dict:
    """Считает всё, что нужно разбору: карту, арканы, небо. Без модели."""
    lat = lon = None
    tz = "Europe/Moscow"
    if order.birth_city:
        lat, lon, tz = await geo.resolve_city_async(order.birth_city)
    chart = await astro.compute_chart_async(
        order.birth_date, order.birth_time or "12:00", order.birth_city,
        lat, lon, tz, time_known=order.time_known,
    )
    matrix = compute_matrix(order.birth_date)
    return {
        "chart": chart,
        "matrix": matrix,
        "sky": astro.today_sky(),
        "tz": tz,
        "brief": astro.chart_brief(chart, time_known=order.time_known),
    }


async def _brand_context(db, lang: str) -> dict[str, str]:
    """Read editable project branding, with deterministic offline defaults."""
    language = _lang(lang)
    defaults = {
        "name": "OracleAI" if language == "en" else "Оракул",
        "tagline": ("A personal AI astrologer that knows you" if language == "en"
                    else "Личный AI-астролог, который знает именно тебя"),
        "project_url": (settings.public_url or settings.webapp_url
                        or "https://github.com/astartv1ai-del/oracleAI"),
        "disclaimer": (_text(language, "disclaimer")),
    }
    if db is None:
        return defaults
    try:
        name_key = "brand.name_en" if language == "en" else "brand.name"
        tagline_key = "brand.tagline_en" if language == "en" else "brand.tagline"
        name = await content.get_setting(db, name_key, defaults["name"])
        tagline = await content.get_setting(db, tagline_key, defaults["tagline"])
        project_url = await content.get_setting(db, "brand.project_url", defaults["project_url"])
        disclaimer_key = "disclaimer_en" if language == "en" else "disclaimer"
        disclaimer = await content.get_setting(db, disclaimer_key, defaults["disclaimer"])
        return {
            "name": str(name or defaults["name"]),
            "tagline": str(tagline or defaults["tagline"]),
            "project_url": str(project_url or defaults["project_url"]),
            "disclaimer": str(disclaimer or defaults["disclaimer"]),
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("не удалось прочитать brand settings для PDF: %s", exc)
        return defaults


def _facts_block(order: Order, data: dict, lang: str) -> str:
    """Compact facts card used as the first content block after the cover."""
    language = _lang(lang)
    chart = data["chart"]
    sun = chart.get("sun") or {}
    asc = chart.get("ascendant") or {}
    labels = _text(language, "facts")
    element = sun.get("element", "—")
    element = ELEMENT_EN.get(element, element) if language == "en" else element
    rows = [
        (labels[0], _human_date(order.birth_date)),
        (labels[1], order.birth_time if order.time_known else _text(language, "unknown")),
        (labels[2], order.birth_city or ("not specified" if language == "en" else "не указано")),
        (labels[3], f"{sun.get('symbol', '')} {_display_sign(sun.get('sign', '—'), language)} · {element}"),
    ]
    if asc:
        rows.append((labels[4], f"{_display_sign(asc.get('sign', '—'), language)} {asc.get('deg', '')}°"))
    moon = next((p for p in chart.get("planets", []) if p["name"] == "Луна"), None)
    if moon:
        rows.append((labels[5], f"{_display_sign(moon['sign'], language)} {moon['deg']}°"))
    lunar_nodes = chart.get("lunar_nodes") or {}
    rahu = lunar_nodes.get("rahu") or next((n for n in chart.get("nodes", []) if n.get("name", "").startswith("Раху")), None)
    ketu = lunar_nodes.get("ketu") or next((n for n in chart.get("nodes", []) if n.get("name", "").startswith("Кету")), None)
    if rahu:
        rows.append((labels[6], f"{_display_sign(rahu.get('sign', '—'), language)} {rahu.get('deg', '—')}°"))
    if ketu:
        rows.append((labels[7], f"{_display_sign(ketu.get('sign', '—'), language)} {ketu.get('deg', '—')}°"))
    _, destiny_arcana, _ = _matrix_display(data["matrix"]["destiny"], language)
    rows.append((labels[8], f"{data['matrix']['destiny']['n']} — {destiny_arcana}"))
    cells = "".join(
        f'<tr><td class="label">{layout.esc(k)}</td><td>{layout.esc(v)}</td></tr>'
        for k, v in rows
    )
    return f'<div class="card"><table>{cells}</table></div>'


def _human_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return iso


async def _section_text(db, order: Order, data: dict, title: str,
                        brief: str) -> str:
    """Generate one section in the selected report language."""
    language = _lang(order.lang)
    if not llm.enabled():
        return _offline_section(title, data, language)
    chart_facts = data["brief"]
    matrix_facts = "; ".join(
        f"{v['title']}: {v['n']} {v['arcana']} — {v['meaning']}"
        for v in data["matrix"].values())
    if language == "en":
        system = (
            "You are a careful astrologer and numerologist writing a personal printable report. "
            "Use only the supplied calculations; never invent a planet, point, aspect or arcana. "
            "Explain technical terms, avoid deterministic claims, and do not make medical, legal "
            "or financial guarantees. Write in English."
        )
        time_note = ("Birth time is known; houses and Ascendant may be used."
                     if order.time_known else
                     "Birth time is unknown; do not make house or Ascendant claims.")
        user_msg = (
            f"Client: {order.name}, birth date {_human_date(order.birth_date)}"
            f"{', ' + order.birth_city if order.birth_city else ''}.\n{time_note}\n\n"
            f"Natal chart facts: {chart_facts}\n\nDestiny Matrix facts: {matrix_facts}\n\n"
            f"Write the section '{_section_title(title, language)}'.\n"
            f"Task: {_section_brief(title, brief, language)}\n\n"
            "Write 4-6 substantial paragraphs, without lists or a heading."
        )
    else:
        system = (
            "Ты — практикующий астролог и нумеролог, пишешь персональный разбор для печати. "
            "Обращаешься к клиентке на «ты», тепло и уважительно. Пишешь живым языком, без "
            "эзотерического жаргона без объяснений. Опираешься ТОЛЬКО на приведённые расчёты и "
            "ничего не выдумываешь: не называешь планет и арканов, которых нет в данных. Не даёшь "
            "медицинских, юридических и финансовых гарантий, не называешь дат событий."
        )
        time_note = ("Время рождения известно точно — дома и Асцендент использовать можно."
                     if order.time_known else
                     "Время рождения НЕИЗВЕСТНО — про дома и Асцендент выводов не делай.")
        user_msg = (
            f"{await skills.guide(db, 'natal')}\n\n{await skills.guide(db, 'matrix')}\n\n"
            f"Клиентка: {order.name}, дата рождения {_human_date(order.birth_date)}"
            f"{', ' + order.birth_city if order.birth_city else ''}.\n{time_note}\n\n"
            f"Натальная карта: {chart_facts}\n\nМатрица Судьбы: {matrix_facts}\n\n"
            f"Напиши раздел разбора «{title}».\nЗадача раздела: {brief}\n\n"
            "Объём — 4-6 абзацев сплошного текста, без списков и без заголовка "
            "(заголовок уже стоит на странице). Пиши обо мне лично и по делу."
        )
    try:
        return await llm.complete(system, user_msg, tier="main", max_tokens=1200,
                                  purpose="pdf_section", db=db)
    except Exception as e:  # noqa: BLE001
        log.warning("раздел «%s» ушёл в офлайн: %s", title, e)
        return _offline_section(title, data, language)


def _offline_section_en(title: str, data: dict) -> str:
    chart = data["chart"]
    planets = chart.get("planets") or []
    nodes = chart.get("nodes") or []
    all_points = planets + nodes + (chart.get("additional_points") or [])

    def point(name: str) -> dict:
        return next((item for item in all_points if item.get("name") == name), {})

    def position(name: str) -> str:
        item = point(name)
        if not item:
            return f"{_display_point(name, 'en')}: no data"
        house = f", house {item['house']}" if item.get("house") else ""
        retro = ", retrograde" if item.get("retro") else ""
        return f"{_display_point(name, 'en')} in {_display_sign(item.get('sign', '—'), 'en')}, {item.get('deg', '—')}°{house}{retro}"

    def house(number: int) -> str:
        item = next((h for h in chart.get("houses") or [] if h.get("n") == number), {})
        if not item:
            return f"House {number} is unavailable without confirmed birth time and coordinates"
        return f"House {number} in {_display_sign(item.get('sign', '—'), 'en')} ({item.get('deg', '—')}°)"

    aspect_text = "; ".join(
        f"{_display_point(a.get('p1', '—'), 'en')} {a.get('glyph', '')} {_display_point(a.get('p2', '—'), 'en')} — {a.get('aspect', '—')} (orb {a.get('orb', '—')}°)"
        for a in (chart.get("aspects") or [])[:5]
    ) or "No key aspects were selected in the available calculation."
    matrix = data["matrix"]

    if title.startswith("Кто ты"):
        return "\n\n".join([
            f"{position('Солнце')}. In symbolic astrology this is a prompt to reflect on self-expression and steady intentions.",
            f"{position('Луна')}. Use this placement as a prompt to observe needs, emotional patterns and recovery.",
            f"Ascendant in {_display_sign((chart.get('ascendant') or {}).get('sign', '—'), 'en')} — {(chart.get('ascendant') or {}).get('deg', '—')}°, when birth time and place are confirmed. It is not a fixed label.",
        ])
    if "сильные" in title.lower():
        return "\n\n".join([
            f"Key patterns to study: {aspect_text}.",
            f"Supportive placements: {position('Юпитер')}; {position('Сатурн')}; {position('Марс')}.",
            "Test each interpretation against lived experience: where has this resource already appeared, and what alternative explanation also fits?",
        ])
    if "сферы жизни" in title.lower():
        return "\n\n".join([
            f"Focus areas: {house(2)}; {house(6)}; {house(10)}.",
            f"Planets by house: {'; '.join(position(p.get('name', '—')) for p in planets[:6])}.",
            "Houses are meaningful only when birth time and coordinates are confirmed. In date-only mode, use sign placements instead.",
        ])
    if "любовь" in title.lower() or "близость" in title.lower():
        return "\n\n".join([
            f"{position('Венера')}. In this symbolic system it can open reflection on values, pleasure and reciprocity.",
            f"{position('Луна')}. Notice which conditions help you feel safe and present in closeness.",
            f"{house(7)}. Instead of predicting a relationship, formulate one observable agreement with a partner.",
        ])
    if "деньги" in title.lower() or "дело" in title.lower():
        return "\n\n".join([
            f"Resource areas: {house(2)}; {house(6)}; {house(10)}.",
            f"Growth and discipline themes: {position('Юпитер')}; {position('Сатурн')}.",
            "Symbolic astrology is not financial advice or a guarantee of income. Translate reflection into a budget, experiment or conversation about value.",
        ])
    if "Матрица" in title or "предназначен" in title.lower():
        return "\n\n".join(
            f"{value['title']}: {value['n']} — {value['arcana']}. {value['meaning']}."
            for value in matrix.values()
        )
    if "Линия" in title:
        return "\n\n".join([
            f"Love line: {matrix.get('love', {}).get('n', '—')} — {matrix.get('love', {}).get('arcana', '—')}.",
            f"Money line: {matrix.get('money', {}).get('n', '—')} — {matrix.get('money', {}).get('arcana', '—')}.",
            "This is a symbolic reflection language, not a promise about relationships or financial outcomes.",
        ])
    if "задач" in title.lower() or "точки роста" in title.lower():
        return "\n\n".join([
            f"Within the tradition, the lunar-node axis is {position('Раху (Северный узел)')} and {position('Кету (Южный узел)')}.",
            f"Boundaries and practice: {position('Сатурн')}; patterns to examine: {aspect_text}.",
            "Treat this as a hypothesis for observation and choice, never as a sentence, diagnosis or literal proof of a past life.",
        ])
    if "решения" in title.lower():
        return "\n\n".join([
            f"Name the question and separate facts from interpretation: {position('Меркурий')}.",
            f"Check your need for safety and recovery: {position('Луна')}.",
            f"Run a small reversible experiment: {position('Марс')}. Review the result using observable evidence.",
        ])
    if "год впереди" in title.lower():
        return "\n\n".join([
            "Without a separate transit calculation, it would be dishonest to present a calendar prediction.",
            f"For reflection, use natal anchors: {position('Солнце')}; {position('Сатурн')}; {position('Юпитер')}.",
            "Choose one theme for a month, record the starting point and assess change through facts rather than coincidences.",
        ])
    return "This chapter uses the calculated chart as a structured prompt for self-reflection."


def _offline_section(title: str, data: dict, lang: str = "ru") -> str:
    """Section-specific fallback grounded only in deterministic chart facts."""
    if _lang(lang) == "en":
        return _offline_section_en(title, data)
    chart = data["chart"]
    matrix = data["matrix"]
    planets = chart.get("planets") or []
    nodes = chart.get("nodes") or []
    all_points = planets + nodes + (chart.get("additional_points") or [])

    def point(name: str) -> dict:
        return next((item for item in all_points if item.get("name") == name), {})

    def position(name: str) -> str:
        item = point(name)
        if not item:
            return f"{name}: данных нет"
        house = f", {item['house']} дом" if item.get("house") else ""
        retro = ", ретроградный" if item.get("retro") else ""
        return f"{name} в {item.get('sign', '—')}, {item.get('deg', '—')}°{house}{retro}"

    def house(number: int) -> str:
        item = next((h for h in chart.get("houses") or [] if h.get("n") == number), {})
        if not item:
            return f"{number}-й дом недоступен без точного времени и координат"
        return f"{number}-й дом в {item.get('sign', '—')} ({item.get('deg', '—')}°)"

    aspect_text = "; ".join(
        f"{a['p1']} {a['glyph']} {a['p2']} — {a['aspect']} (орб {a['orb']}°)"
        for a in (chart.get("aspects") or [])[:5]
    ) or "Ключевые аспекты не выделены в доступном расчёте."
    asc = chart.get("ascendant") or {}
    rahu = next((n for n in nodes if n.get("name", "").startswith("Раху")), {})
    ketu = next((n for n in nodes if n.get("name", "").startswith("Кету")), {})

    if title.startswith("Кто ты"):
        return "\n\n".join([
            f"{position('Солнце')}. Это символическое ядро самовыражения и устойчивых намерений.",
            f"{position('Луна')}. Этот показатель можно использовать как повод наблюдать за потребностями и восстановлением.",
            f"Асцендент в {asc.get('sign', '—')} — {asc.get('deg', '—')}°, если время и место рождения подтверждены. Это описание способа входить в ситуации, а не фиксированный ярлык.",
        ])
    if "сильные" in title.lower():
        return "\n\n".join([
            f"Главные связки, которые стоит изучить: {aspect_text}",
            f"Опорные положения: {position('Юпитер')}; {position('Сатурн')}; {position('Марс')}.",
            "Проверяй каждую интерпретацию конкретным опытом: где этот ресурс уже проявлялся, а где сработало альтернативное объяснение.",
        ])
    if "сферы жизни" in title.lower():
        return "\n\n".join([
            f"{house(2)}; {house(6)}; {house(10)}.",
            f"Планеты по домам: {'; '.join(position(p.get('name', '—')) for p in planets[:6])}.",
            "Дома показывают символическую область внимания только при точном времени и координатах; при date-only режиме используй положения по знакам.",
        ])
    if "любовь" in title.lower() or "близость" in title.lower():
        return "\n\n".join([
            f"{position('Венера')}. В символической системе это повод исследовать ценности, удовольствие и взаимность.",
            f"{position('Луна')}. Наблюдай, какие условия помогают чувствовать безопасность в близости.",
            f"{house(7)}. Вместо предсказания отношений сформулируй одну проверяемую договорённость с партнёром.",
        ])
    if "деньги" in title.lower() or "дело" in title.lower():
        return "\n\n".join([
            f"Ресурсные зоны карты: {house(2)}; {house(6)}; {house(10)}.",
            f"Темы роста и дисциплины: {position('Юпитер')}; {position('Сатурн')}.",
            "Символика не является финансовой рекомендацией или гарантией дохода. Переводи наблюдение в бюджет, эксперимент или разговор о цене.",
        ])
    if "Матрица" in title or "предназначен" in title.lower():
        return "\n\n".join(
            f"{value['title']}: {value['n']} — {value['arcana']}. {value['meaning']}."
            for value in matrix.values()
        )
    if "Линия" in title:
        return "\n\n".join([
            f"{matrix.get('love', {}).get('title', 'Линия любви')}: {matrix.get('love', {}).get('n', '—')} — {matrix.get('love', {}).get('arcana', '—')}.",
            f"{matrix.get('money', {}).get('title', 'Линия денег')}: {matrix.get('money', {}).get('n', '—')} — {matrix.get('money', {}).get('arcana', '—')}.",
            "Это символический язык рефлексии, а не обещание отношений или финансового результата.",
        ])
    if "задач" in title.lower() or "точки роста" in title.lower():
        return "\n\n".join([
            f"Кармическая ось в рамках традиции: {rahu.get('name', 'Раху')} в {rahu.get('sign', '—')} и {ketu.get('name', 'Кету')} в {ketu.get('sign', '—')}.",
            f"Граница и навык: {position('Сатурн')}; напряжённые связки: {aspect_text}.",
            "Смотри на это как на гипотезу для наблюдения и выбора, а не как на приговор, диагноз или воспоминание о прошлой жизни.",
        ])
    if "решения" in title.lower():
        return "\n\n".join([
            f"Сначала назови вопрос и отдели факт от интерпретации: {position('Меркурий')}.",
            f"Проверь телесную реакцию и потребность в безопасности: {position('Луна')}.",
            f"Сделай маленький обратимый эксперимент: {position('Марс')}. Через неделю оцени результат по наблюдаемым признакам.",
        ])
    if "год впереди" in title.lower():
        return "\n\n".join([
            "Без отдельного транзитного расчёта нельзя честно выдавать календарный прогноз событий.",
            f"Для рефлексии можно использовать натальные опоры: {position('Солнце')}; {position('Сатурн')}; {position('Юпитер')}.",
            "Выбери одну тему на месяц, зафиксируй исходную точку и оцени изменения по фактам, а не по совпадениям.",
        ])
    return data["brief"]


def _ticket_block(promo_code: str | None, bot_username: str, lang: str) -> str:
    """Promo block linking the generated report back to the project."""
    if not promo_code:
        return ""
    language = _lang(lang)
    link = (f"https://t.me/{bot_username}?start={promo_code}" if bot_username else "")
    where = (f'<p class="small muted">{_text(language, "open_link")}: {layout.esc(link)}</p>'
             if link else f'<p class="small muted">{_text(language, "promo_help")}</p>')
    return (
        '<div class="ticket">'
        f'<h2 style="border:none;margin-bottom:3mm">{_text(language, "ticket")}</h2>'
        f'<p>{_text(language, "ticket_body")}</p>'
        f'<div class="code">{layout.esc(promo_code)}</div>'
        f'{where}</div>')


def _data_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    head = "".join(f"<th>{layout.esc(value)}</th>" for value in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f'<table class="data-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def _exact_degree(value) -> str:
    try:
        return f"{float(value):.4f}°"
    except (TypeError, ValueError):
        return "—"


def _point_rows(points: list[dict], lang: str) -> list[list[str]]:
    language = _lang(lang)
    rows = []
    for point in points:
        name = point.get("name", "—")
        glyph = layout.PLANET_GLYPHS.get(name, "•")
        display_name = _display_point(name, language)
        sign = _display_sign(point.get("sign", "—"), language)
        exact = point.get("deg_exact", point.get("deg"))
        degree = f"{point.get('deg', '—')}° <span class=\"muted small\">({_exact_degree(exact)})</span>"
        house = (f"{_text(language, 'house')} {point.get('house')}"
                 if point.get("house") else "—")
        status = _text(language, "retro" if point.get("retro") else "direct")
        rows.append([f"{layout.esc(glyph)} {layout.esc(display_name)}", layout.esc(sign), degree, house, status])
    return rows


def _natal_reference_block(data: dict, lang: str) -> str:
    language = _lang(lang)
    chart = data["chart"]
    def t(key: str):
        return _text(language, key)

    headers = [t("object"), t("sign"), t("degree"), t("house"), t("status")]
    parts = [
        f'<div class="section"><h2>{t("reference")}</h2>',
        f'<p class="small muted">{t("exact_note")}</p>',
        f'<div class="card"><table><tr><td class="label">{t("engine")}</td><td>{layout.esc(chart.get("engine", "Swiss Ephemeris"))}</td></tr>'
        f'<tr><td class="label">{t("zodiac")}</td><td>{layout.esc(chart.get("zodiac_type", "Tropical"))}</td></tr>'
        f'<tr><td class="label">{t("houses")}</td><td>{layout.esc(chart.get("house_system_name", "Placidus"))} ({layout.esc(chart.get("house_system", "P"))})</td></tr>'
        f'<tr><td class="label">{t("perspective")}</td><td>{layout.esc(chart.get("perspective_type", "Apparent Geocentric"))}</td></tr>'
        f'<tr><td class="label">{t("precision")}</td><td>{layout.esc(_display_precision(chart.get("precision", "unknown"), language))}</td></tr>'
        f'<tr><td class="label">{t("node_mode")}</td><td>{layout.esc((chart.get("lunar_nodes") or {}).get("mode_label", t("true_node")))}</td></tr></table></div>',
        f'<h3>{t("planets")}</h3>',
        _data_table(headers, _point_rows(chart.get("planets") or [], language)),
    ]
    nodes = chart.get("nodes") or []
    if nodes:
        note = ("Rahu is the North Node and Ketu is the South Node. This is a symbolic axis, not proof of predetermined events."
                if language == "en" else
                "Rahu — Северный лунный узел, Ketu — Южный лунный узел. Это символическая ось, а не доказательство предопределённости событий.")
        parts.extend([f'<h3>{t("nodes")}</h3>', f'<p>{note}</p>', _data_table(headers, _point_rows(nodes, language))])
    expanded = chart.get("additional_points") or []
    if expanded:
        parts.extend([f'<h3>{t("additional")}</h3>', _data_table(headers, _point_rows(expanded, language))])
    houses = chart.get("houses") or []
    if houses:
        rows = []
        for house in houses:
            exact = house.get("abs_deg_exact", house.get("abs_deg"))
            degree = f"{house.get('deg', '—')}° <span class=\"muted small\">({_exact_degree(exact)})</span>"
            rows.append([str(house.get("n", "—")), layout.esc(_display_sign(house.get("sign", "—"), language)), degree])
        parts.extend([f'<h3>{t("cusps")}</h3>', _data_table([t("house"), t("sign"), "Cusp longitude" if language == "en" else "Долгота куспида"], rows)])
    aspects = chart.get("aspects") or []
    if aspects:
        aspect_en = {"соединение": "conjunction", "оппозиция": "opposition", "трин": "trine", "квадрат": "square", "секстиль": "sextile"}
        rows = []
        for aspect in aspects:
            orb = aspect.get("orb_exact", aspect.get("orb", "—"))
            p1 = _display_point(aspect.get("p1", "—"), language)
            p2 = _display_point(aspect.get("p2", "—"), language)
            aspect_name = aspect_en.get(aspect.get("aspect", "—"), aspect.get("aspect", "—")) if language == "en" else aspect.get("aspect", "—")
            rows.append([layout.esc(f"{p1} {aspect.get('glyph', '')} {p2}"), layout.esc(aspect_name), f"{aspect.get('orb', '—')}° <span class=\"muted small\">({_exact_degree(orb)})</span>"])
        parts.extend([f'<h3>{t("aspects")}</h3>', _data_table(["Pattern" if language == "en" else "Связка", "Aspect" if language == "en" else "Аспект", "Orb" if language == "en" else "Орб"], rows)])
    matrix_rows = []
    for item in data["matrix"].values():
        title, arcana, meaning = _matrix_display(item, language)
        matrix_rows.append([str(item.get("n", "—")), layout.esc(title), layout.esc(arcana), layout.esc(meaning)])
    parts.extend([f'<h3>{t("matrix")}</h3>', _data_table(["#", "Position" if language == "en" else "Позиция", "Arcana" if language == "en" else "Аркан", "Meaning" if language == "en" else "Смысл"], matrix_rows)])
    parts.append('</div>')
    return "".join(parts)


def _closing_block(order: Order, data: dict, brand: dict[str, str], lang: str) -> str:
    language = _lang(lang)
    chart = data["chart"]
    nodes = chart.get("lunar_nodes") or {}
    rahu = nodes.get("rahu") or next((n for n in chart.get("nodes", []) if n.get("name", "").startswith("Раху")), {})
    ketu = nodes.get("ketu") or next((n for n in chart.get("nodes", []) if n.get("name", "").startswith("Кету")), {})
    sun = chart.get("sun") or {}
    asc = chart.get("ascendant") or {}
    _, destiny_arcana, destiny_meaning = _matrix_display(data["matrix"]["destiny"], language)
    rows = [
        ("Rahu / Раху" if language == "ru" else "Rahu", f"{_display_sign(rahu.get('sign', '—'), language)} {rahu.get('deg', '—')}°"),
        ("Ketu / Кету" if language == "ru" else "Ketu", f"{_display_sign(ketu.get('sign', '—'), language)} {ketu.get('deg', '—')}°"),
        (_text(language, "facts")[3], f"{_display_sign(sun.get('sign', '—'), language)} {sun.get('deg', '—')}°"),
        (_text(language, "facts")[4], f"{_display_sign(asc.get('sign', '—'), language)} {asc.get('deg', '—')}°" if asc else _text(language, "unknown")),
        (_text(language, "facts")[8], f"{data['matrix']['destiny']['n']} — {destiny_arcana}"),
    ]
    rows_html = "".join(f'<tr><td class="label">{layout.esc(k)}</td><td>{layout.esc(v)}</td></tr>' for k, v in rows)
    guide_title = "Практический guide" if language == "ru" else "Practical guide"
    guide = ("Используй карту как язык наблюдения: выбери одну тему, сформулируй проверяемый вопрос, "
             "запиши исходную точку и вернись к ней через месяц. Символические значения не отменяют "
             "факты, личные границы и помощь профильных специалистов."
             if language == "ru" else
             "Use the chart as a language for observation: choose one theme, formulate an observable question, "
             "record the starting point and revisit it in a month. Symbolic meanings do not replace facts, "
             "personal boundaries or qualified professional support.")
    project = (f'<p class="small"><a href="{layout.esc(brand["project_url"])}">'
               f'{layout.esc(_text(language, "link"))}: {layout.esc(brand["project_url"])}</a></p>'
               if brand["project_url"].startswith(("https://", "http://")) else "")
    return (f'<div class="closing-grid"><div class="card"><h3>{layout.esc("Ключевые позиции" if language == "ru" else "Key placements")}</h3>'
            f'<table>{rows_html}</table></div><div class="card"><h3>{layout.esc(guide_title)}</h3>'
            f'<p>{layout.esc(guide)}</p><p class="small muted">{layout.esc(destiny_meaning)}</p>{project}</div></div>')


async def generate(db, order: Order, *, bot_username: str = "",
                   concurrency: int = 3) -> str:
    """Build a compact, localized HTML report ready for PDF rendering."""
    language = _lang(order.lang)
    brand = await _brand_context(db, language)
    data = await build_report_data(order)
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def one(title: str, brief: str) -> str:
        async with semaphore:
            return await _section_text(db, order, data, title, brief)

    texts = await asyncio.gather(*(one(t, b) for t, b in SECTIONS))
    project_url = brand["project_url"]
    safe_url = project_url if project_url.startswith(("https://", "http://")) else ""
    matrix_labels = {
        item.get("title", ""): _matrix_display(item, language)[0]
        for item in data["matrix"].values()
    }
    cover_title = _text(language, "title")
    cover_link = (f'<a class="project-link" href="{layout.esc(safe_url)}">'
                  f'{layout.esc(_text(language, "link"))}: {layout.esc(safe_url)}</a>'
                  if safe_url else "")
    born = _human_date(order.birth_date)
    if order.birth_time:
        born += f" · {order.birth_time}"
    if order.birth_city:
        born += f" · {order.birth_city}"
    blocks = [
        '<div class="cover">'
        f'<div class="brand-mark">{layout.brand_mark_svg()}</div>'
        f'<div class="brand">{layout.esc(brand["name"])}</div>'
        f'<div class="eyebrow">{layout.esc(_text(language, "eyebrow"))}</div>'
                 f'<h1>{layout.esc(cover_title)}</h1>'
         f'<p class="sub">{layout.esc(brand["tagline"])}</p>'
         f'<div class="cover-wheel">{layout.wheel_svg(data["chart"], size=300)}</div>'
         f'<div class="who">{layout.esc(order.name)}</div>'

        f'<div class="born">{layout.esc(born)}</div>'
        f'<p class="sub small">{layout.esc(_text(language, "composed"))} {date.today().strftime("%d.%m.%Y")}</p>'
        f'{cover_link}'
        '</div>',
        f'<div class="section"><h2>{layout.esc(_text(language, "summary"))}</h2>'
        '<div class="overview-grid">'
        f'<div>{_facts_block(order, data, language)}</div>'
        '<div class="overview-visuals">'
        f'<div class="wheel">{layout.wheel_svg(data["chart"], size=300)}</div>'
        f'<div class="wheel">{layout.matrix_svg(data["matrix"], size=270, labels=matrix_labels)}</div>'
        '</div></div></div>',
        _natal_reference_block(data, language),
    ]
    for (title, brief), text in zip(SECTIONS, texts):
        blocks.append(f'<div class="section chapter"><h2>{layout.esc(_section_title(title, language))}</h2>'
                      f'{layout.paragraphs(text)}</div>')
    blocks.append(
        f'<div class="section footer-section"><h2>{layout.esc(_text(language, "composed"))}</h2>'
        + _closing_block(order, data, brand, language)
        + _ticket_block(order.promo_code, bot_username, language)
        + f'<p class="disclaimer">{layout.esc(brand["disclaimer"])}</p></div>')
    return layout.document(f"{cover_title} — {order.name}", blocks, lang=language)
