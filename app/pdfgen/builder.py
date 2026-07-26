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

from ..core import astro, geo, llm, skills
from ..core.matrix import compute_matrix
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

DISCLAIMER = ("Разбор создан для самопознания и вдохновения. Он не заменяет "
              "консультацию врача, психолога или юриста.")


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
        lat, lon, tz)
    matrix = compute_matrix(order.birth_date)
    return {
        "chart": chart,
        "matrix": matrix,
        "sky": astro.today_sky(),
        "tz": tz,
        "brief": astro.chart_brief(chart),
    }


def _facts_block(order: Order, data: dict) -> str:
    """Страница с сухими фактами: то, что покупательница проверит первым делом."""
    chart = data["chart"]
    sun = chart.get("sun") or {}
    asc = chart.get("ascendant") or {}
    rows = [
        ("Дата рождения", _human_date(order.birth_date)),
        ("Время рождения",
         order.birth_time if order.time_known else "неизвестно (карта по знакам)"),
        ("Место рождения", order.birth_city or "не указано"),
        ("Солнце", f"{sun.get('symbol', '')} {sun.get('sign', '—')} "
                   f"· стихия {sun.get('element', '—')}"),
    ]
    if asc:
        rows.append(("Асцендент", f"{asc.get('sign', '—')} {asc.get('deg', '')}°"))
    moon = next((p for p in chart.get("planets", []) if p["name"] == "Луна"), None)
    if moon:
        rows.append(("Луна", f"{moon['sign']} {moon['deg']}°"))
    rows.append(("Аркан судьбы",
                 f"{data['matrix']['destiny']['n']} — "
                 f"{data['matrix']['destiny']['arcana']}"))

    cells = "".join(
        f'<tr><td class="label">{layout.esc(k)}</td>'
        f'<td>{layout.esc(v)}</td></tr>' for k, v in rows)
    return (f'<div class="card"><table>{cells}</table></div>')


def _human_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return iso


async def _section_text(db, order: Order, data: dict, title: str,
                        brief: str) -> str:
    """Текст одного раздела. Без модели — содержательная заглушка на расчётах."""
    if not llm.enabled():
        return _offline_section(title, data)
    chart_facts = data["brief"]
    matrix_facts = "; ".join(
        f"{v['title']}: {v['n']} {v['arcana']} — {v['meaning']}"
        for v in data["matrix"].values())
    system = (
        "Ты — практикующий астролог и нумеролог, пишешь персональный разбор для "
        "печати. Обращаешься к клиентке на «ты», тепло и уважительно. Пишешь "
        "живым языком, без эзотерического жаргона без объяснений. Опираешься "
        "ТОЛЬКО на приведённые расчёты и ничего не выдумываешь: не называешь "
        "планет и арканов, которых нет в данных. Не даёшь медицинских, "
        "юридических и финансовых гарантий, не называешь дат событий.")
    time_note = ("Время рождения известно точно — дома и Асцендент использовать можно."
                 if order.time_known else
                 "Время рождения НЕИЗВЕСТНО — про дома и Асцендент выводов не делай.")
    user_msg = (
        f"{await skills.guide(db, 'natal')}\n\n{await skills.guide(db, 'matrix')}\n\n"
        f"Клиентка: {order.name}, дата рождения {_human_date(order.birth_date)}"
        f"{', ' + order.birth_city if order.birth_city else ''}.\n"
        f"{time_note}\n\n"
        f"Натальная карта: {chart_facts}\n\n"
        f"Матрица Судьбы: {matrix_facts}\n\n"
        f"Напиши раздел разбора «{title}».\n"
        f"Задача раздела: {brief}\n\n"
        f"Объём — 4-6 абзацев сплошного текста, без списков и без заголовка "
        f"(заголовок уже стоит на странице). Пиши обо мне лично и по делу.")
    try:
        return await llm.complete(system, user_msg, tier="main", max_tokens=1200,
                                  purpose="pdf_section", db=db)
    except Exception as e:  # noqa: BLE001
        log.warning("раздел «%s» ушёл в офлайн: %s", title, e)
        return _offline_section(title, data)


def _offline_section(title: str, data: dict) -> str:
    """Раздел без модели: настоящие данные вместо литературного текста."""
    matrix = data["matrix"]
    if "Матриц" in title or "Линия" in title or "предназначен" in title.lower():
        return "\n".join(
            f"{v['title']}: {v['n']} — {v['arcana']}. {v['meaning']}."
            for v in matrix.values())
    chart = data["chart"]
    lines = [data["brief"]]
    for aspect in (chart.get("aspects") or [])[:6]:
        lines.append(f"{aspect['p1']} {aspect['glyph']} {aspect['p2']} — "
                     f"{aspect['aspect']} (орб {aspect['orb']}°).")
    return "\n".join(lines)


def _ticket_block(promo_code: str | None, bot_username: str) -> str:
    """«Золотой билет» — то, ради чего PDF вообще связан с ботом."""
    if not promo_code:
        return ""
    link = (f"https://t.me/{bot_username}?start={promo_code}"
            if bot_username else "")
    where = (f'<p class="small muted">Открой ссылку: {layout.esc(link)}</p>'
             if link else
             '<p class="small muted">Введи код в боте командой /promo</p>')
    return (
        '<div class="ticket">'
        '<h2 style="border:none;margin-bottom:3mm">🎟 Твой золотой билет</h2>'
        '<p>30 дней полного доступа к личному AI-Оракулу: он знает эту карту, '
        'раскладывает Таро и помнит всё, что ты ему расскажешь.</p>'
        f'<div class="code">{layout.esc(promo_code)}</div>'
        f'{where}</div>')


async def generate(db, order: Order, *, bot_username: str = "",
                   concurrency: int = 3) -> str:
    """Собирает разбор целиком и возвращает HTML.

    Разделы пишутся параллельно небольшими группами: последовательно десять
    запросов к модели занимают минуты, а цель ТЗ — не больше пяти минут на заказ.
    Порядок разделов при этом сохраняется.
    """
    data = await build_report_data(order)
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def one(title: str, brief: str) -> str:
        async with semaphore:
            return await _section_text(db, order, data, title, brief)

    texts = await asyncio.gather(*(one(t, b) for t, b in SECTIONS))

    blocks = [
        '<div class="cover">'
        '<h1>Персональный разбор<br>натальной карты<br>и Матрицы Судьбы</h1>'
        f'<div class="who">{layout.esc(order.name)}</div>'
        f'<div class="born">{layout.esc(_human_date(order.birth_date))}'
        f'{" · " + layout.esc(order.birth_city) if order.birth_city else ""}</div>'
        f'<p class="sub">Составлено {date.today().strftime("%d.%m.%Y")}</p>'
        '</div>',
        '<div class="section"><h2>Твоя карта в цифрах</h2>'
        + _facts_block(order, data)
        + f'<div class="wheel">{layout.wheel_svg(data["chart"])}</div>'
        + f'<div class="wheel">{layout.matrix_svg(data["matrix"])}</div></div>',
    ]
    for (title, _), text in zip(SECTIONS, texts):
        blocks.append(f'<div class="section"><h2>{layout.esc(title)}</h2>'
                      f'{layout.paragraphs(text)}</div>')

    blocks.append(
        '<div class="section">'
        + _ticket_block(order.promo_code, bot_username)
        + f'<p class="disclaimer">{layout.esc(DISCLAIMER)}</p></div>')

    return layout.document(f"Разбор — {order.name}", blocks)
