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
    lunar_nodes = chart.get("lunar_nodes") or {}
    rahu = lunar_nodes.get("rahu") or next((n for n in chart.get("nodes", []) if n.get("name", "").startswith("Раху")), None)
    ketu = lunar_nodes.get("ketu") or next((n for n in chart.get("nodes", []) if n.get("name", "").startswith("Кету")), None)
    if rahu:
        rows.append(("Rahu / Раху", f"{rahu.get('sign', '—')} {rahu.get('deg', '—')}°"))
    if ketu:
        rows.append(("Ketu / Кету", f"{ketu.get('sign', '—')} {ketu.get('deg', '—')}°"))
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
    """Section-specific fallback grounded only in deterministic chart facts."""
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


def _point_rows(points: list[dict]) -> list[list[str]]:
    rows = []
    for point in points:
        name = point.get("name", "—")
        glyph = layout.PLANET_GLYPHS.get(name, "•")
        sign = point.get("sign", "—")
        exact = point.get("deg_exact", point.get("deg"))
        degree = f"{point.get('deg', '—')}° <span class=\"muted small\">({_exact_degree(exact)})</span>"
        house = f"{point.get('house')} дом" if point.get("house") else "—"
        status = "ретроградный" if point.get("retro") else "директный"
        rows.append([f"{layout.esc(glyph)} {layout.esc(name)}", layout.esc(sign), degree, house, status])
    return rows


def _natal_reference_block(data: dict) -> str:
    chart = data["chart"]
    parts = [
        '<div class="section"><h2>Натальная карта: полный расчёт</h2>',
        '<p class="small muted">Ниже приведены исходные расчётные данные. Округлённые значения удобны для чтения, а точные значения в скобках сохранены для проверки.</p>',
        f'<div class="card"><table><tr><td class="label">Эфемеридный движок</td><td>{layout.esc(chart.get("engine", "Swiss Ephemeris"))}</td></tr>'
        f'<tr><td class="label">Зодиак</td><td>{layout.esc(chart.get("zodiac_type", "Tropical"))}</td></tr>'
        f'<tr><td class="label">Система домов</td><td>{layout.esc(chart.get("house_system_name", "Placidus"))} ({layout.esc(chart.get("house_system", "P"))})</td></tr>'
        f'<tr><td class="label">Точность</td><td>{layout.esc(chart.get("precision", "unknown"))}</td></tr></table></div>',
        '<h3>Планеты</h3>',
        _data_table(["Объект", "Знак", "Градус", "Дом", "Статус"], _point_rows(chart.get("planets") or [])),
    ]
    nodes = chart.get("nodes") or []
    if nodes:
        parts.extend([
            '<h3>Лунные узлы: Rahu и Ketu</h3>',
            '<p>В этой карте <b>Rahu</b> представлен как Северный лунный узел, а <b>Ketu</b> — как Южный лунный узел. Это символическая ось; она не является доказательством предопределённости событий.</p>',
            _data_table(["Объект", "Знак", "Градус", "Дом", "Статус"], _point_rows(nodes)),
        ])
    expanded = chart.get("additional_points") or []
    if expanded:
        parts.extend([
            '<h3>Дополнительные точки</h3>',
            _data_table(["Объект", "Знак", "Градус", "Дом", "Статус"], _point_rows(expanded)),
        ])
    houses = chart.get("houses") or []
    if houses:
        rows = []
        for house in houses:
            exact = house.get("abs_deg_exact", house.get("abs_deg"))
            degree = f"{house.get('deg', '—')}° <span class=\"muted small\">({_exact_degree(exact)})</span>"
            rows.append([str(house.get("n", "—")), layout.esc(house.get("sign", "—")), degree])
        parts.extend([
            '<h3>Куспиды домов</h3>',
            _data_table(["Дом", "Знак", "Долгота куспида"], rows),
        ])
    aspects = chart.get("aspects") or []
    if aspects:
        rows = []
        for aspect in aspects:
            orb = aspect.get("orb_exact", aspect.get("orb", "—"))
            rows.append([
                layout.esc(f"{aspect.get('p1', '—')} {aspect.get('glyph', '')} {aspect.get('p2', '—')}"),
                layout.esc(aspect.get("aspect", "—")),
                f"{aspect.get('orb', '—')}° <span class=\"muted small\">({_exact_degree(orb)})</span>",
            ])
        parts.extend(['<h3>Ключевые аспекты</h3>', _data_table(["Связка", "Аспект", "Орб"], rows)])
    parts.append('</div>')
    return "".join(parts)


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
        '<h1>Полный отчёт<br>натальной карты<br>и Матрицы Судьбы</h1>'
        f'<div class="who">{layout.esc(order.name)}</div>'
        f'<div class="born">{layout.esc(_human_date(order.birth_date))}'
        f'{" · " + layout.esc(order.birth_city) if order.birth_city else ""}</div>'
        f'<p class="sub">Составлено {date.today().strftime("%d.%m.%Y")}</p>'
        '</div>',
        '<div class="section"><h2>Твоя карта в цифрах</h2>'
        + _facts_block(order, data)
        + f'<div class="wheel">{layout.wheel_svg(data["chart"])}</div>'
        + f'<div class="wheel">{layout.matrix_svg(data["matrix"])}</div></div>',
        _natal_reference_block(data),
    ]
    for (title, _), text in zip(SECTIONS, texts):
        blocks.append(f'<div class="section"><h2>{layout.esc(title)}</h2>'
                      f'{layout.paragraphs(text)}</div>')

    blocks.append(
        '<div class="section">'
        + _ticket_block(order.promo_code, bot_username)
        + f'<p class="disclaimer">{layout.esc(DISCLAIMER)}</p></div>')

    return layout.document(f"Разбор — {order.name}", blocks)
