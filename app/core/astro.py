"""Астро-расчёты.

Полный режим: kerykeion (Swiss Ephemeris) — планеты, дома, аспекты.
Лайт-режим (библиотека не установлена): знак Солнца + стихия, честно помеченный.
LLM никогда не считает карту — только трактует результат этого модуля.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime

log = logging.getLogger("oracle.astro")

SIGNS = [
    ("Овен", "♈", "огонь"), ("Телец", "♉", "земля"), ("Близнецы", "♊", "воздух"),
    ("Рак", "♋", "вода"), ("Лев", "♌", "огонь"), ("Дева", "♍", "земля"),
    ("Весы", "♎", "воздух"), ("Скорпион", "♏", "вода"), ("Стрелец", "♐", "огонь"),
    ("Козерог", "♑", "земля"), ("Водолей", "♒", "воздух"), ("Рыбы", "♓", "вода"),
]

# границы знаков по дням (приближённо, для лайт-режима)
_SUN_BOUNDS = [(1, 20), (2, 19), (3, 21), (4, 20), (5, 21), (6, 21),
               (7, 23), (8, 23), (9, 23), (10, 23), (11, 22), (12, 22)]

PLANET_RU = {
    "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
    "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн",
    "Uranus": "Уран", "Neptune": "Нептун", "Pluto": "Плутон",
}
SIGN_EN2RU = {
    "Ari": "Овен", "Tau": "Телец", "Gem": "Близнецы", "Can": "Рак", "Leo": "Лев",
    "Vir": "Дева", "Lib": "Весы", "Sco": "Скорпион", "Sag": "Стрелец",
    "Cap": "Козерог", "Aqu": "Водолей", "Pis": "Рыбы",
}

# kerykeion отдаёт дом строкой вида "Ninth_House"
HOUSE_ORDER = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth",
               "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth"]
HOUSE_NUM = {f"{n}_House": i + 1 for i, n in enumerate(HOUSE_ORDER)}

ASPECT_RU = {
    "conjunction": ("соединение", "☌"), "opposition": ("оппозиция", "☍"),
    "trine": ("трин", "△"), "square": ("квадрат", "□"), "sextile": ("секстиль", "⚹"),
}
# только мажорные аспекты между «настоящими» планетами — иначе шум из 55 строк
POINT_RU = {**PLANET_RU, "Ascendant": "Асцендент", "Medium_Coeli": "Середина неба"}
ASPECT_PLANETS = set(POINT_RU)


def sun_sign(d: date) -> tuple[str, str, str]:
    """(знак, символ, стихия) по дате — без эфемерид."""
    m, day = d.month, d.day
    bm, bd = _SUN_BOUNDS[m - 1]
    idx = (m - 1) if day >= bd else (m - 2)
    # индекс знака: 21 марта = Овен (0). Сдвиг: март -> 0
    return SIGNS[(idx - 2) % 12]


# ───────────────────────── эфемеридные знаки без времени ─────────────────────
#
# Для знаков планет точное время и место рождения не нужны — планеты находятся
# в одном знаке круглые сутки. kerykeion строит карту на дату в 12:00 и с
# координатами, не влияющими на знаки; кеш по дате экономит повторные расчёты,
# потому что прогноз дня, гороскопы и спидометр зовут их часто.
_LIGHT_CACHE: dict[str, dict] = {}


def _light_sky(d: date) -> dict:
    """Знаки Солнца/Луны/Венеры на дату: эфемериды → календарный фолбэк."""
    key = d.isoformat()
    cached = _LIGHT_CACHE.get(key)
    if cached:
        return cached
    try:
        from kerykeion import AstrologicalSubject
        subj = AstrologicalSubject(name="sky", year=d.year, month=d.month,
                                   day=d.day, hour=12, minute=0, city="-",
                                   lat=52.5, lng=13.4, tz_str="UTC", online=False)
        m = subj.model()

        def sign_of(p) -> tuple[str, str]:
            s = SIGN_EN2RU.get(p.sign, p.sign)
            el = next((x[2] for x in SIGNS if x[0] == s), "")
            return s, el

        # Точный знак Солнца: момент входа по эфемеридам, а не по календарю.
        s, el = sign_of(m.sun)
        sym = next((x[1] for x in SIGNS if x[0] == s), "☉")
        out = {"sun": (s, sym, el),
               "moon": sign_of(m.moon), "venus": sign_of(m.venus)}
    except Exception as e:  # noqa: BLE001
        log.debug("эфемеридные знаки недоступны (%s), фолбэк на календарь", e)
        out = {"sun": sun_sign(d), "moon": None, "venus": None}
    if len(_LIGHT_CACHE) > 800:
        _LIGHT_CACHE.clear()
    _LIGHT_CACHE[key] = out
    return out


def sun_sign_precise(d: date) -> tuple[str, str, str]:
    """Точный знак Солнца (эфемериды): переход на годы, а не статичная таблица.

    Рождённый 21 марта в одном году уже Телец, в другом ещё Овен — календарные
    границы грешат на ±1–2 дня. При недоступных эфемеридах — календарный знак.
    """
    return _light_sky(d)["sun"]


def moon_venus_signs(d: date) -> tuple[tuple[str, str] | None,
                                       tuple[str, str] | None]:
    """(знак, стихия) Луны и Венеры на дату; кортежи None — эфемериды недоступны."""
    sky = _light_sky(d)
    return sky["moon"], sky["venus"]


# ─────────────────────────────── синастрия ────────────────────────────────────

# Орбы синастрии: светилам шире (10°), планетам 6–8° — классика мажорных.
_SYNASTRY_ORBS = {"conjunction": 8, "opposition": 8, "trine": 8,
                  "square": 7, "sextile": 6}
_ASPECT_ANGLE = {"conjunction": 0.0, "opposition": 180.0, "trine": 120.0,
                 "square": 90.0, "sextile": 60.0}
_LUMINARY = {"Солнце", "Луна"}


def _delta360(a: float, b: float) -> float:
    delta = abs(a - b) % 360
    return min(delta, 360 - delta)


def synastry_aspects(planets_a: list[dict], planets_b: list[dict],
                     limit: int = 10) -> list[dict]:
    """Мажорные аспекты между планетами двух карт, точные первыми.

    Одноимённые точки (Солнце—Солнце и т.п.) пропускаем: это не аспект «между»,
    а две стороны одного качества — в классике синастрии их не читают орбно.
    """
    out = []
    for pa in planets_a:
        if pa.get("abs_deg") is None:   # 0° — легитимная долгота
            continue
        for pb in planets_b:
            if pa["name"] == pb["name"] or pb.get("abs_deg") is None:
                continue
            delta = _delta360(pa["abs_deg"], pb["abs_deg"])
            orb = 10 if (pa["name"] in _LUMINARY or pb["name"] in _LUMINARY) else 8
            for aspect, good in _ASPECT_ANGLE.items():
                if abs(delta - good) <= _SYNASTRY_ORBS.get(aspect, orb):
                    glyph = ASPECT_RU[aspect][1]
                    out.append({"p1": pa["name"], "p2": pb["name"],
                                "aspect": ASPECT_RU[aspect][0], "glyph": glyph,
                                "orb": round(abs(delta - good), 1), "code": aspect})
                    break
    out.sort(key=lambda x: x["orb"])
    return out[:limit]


def synastry_aspects_text(aspects: list[dict]) -> str:
    if not aspects:
        return "аспектов между картами не найдено"
    return "; ".join(f"{a['p1']} {a['glyph']} {a['p2']} (орб {a['orb']}°)"
                     for a in aspects[:8])


def compute_chart(birth_date: str, birth_time: str | None, city: str | None,
                  lat: float | None, lon: float | None,
                  tz: str | None = None) -> dict:
    """Возвращает dict карты. mode: 'full' | 'lite'.

    tz обязателен для точных домов: время рождения — местное, и без таймзоны
    эфемериды посчитают карту со сдвигом в несколько часов.
    """
    d = datetime.strptime(birth_date, "%Y-%m-%d").date()
    try:
        return _full_chart(d, birth_time, city, lat, lon, tz)
    except Exception as e:  # noqa: BLE001
        log.warning("полная карта недоступна (%s), считаю упрощённо", e)
        sign, sym, element = sun_sign(d)
        return {
            "mode": "lite",
            "sun": {"sign": sign, "symbol": sym, "element": element},
            "planets": [],
            "houses": [],
            "aspects": [],
            "note": "Упрощённый расчёт (полные эфемериды недоступны).",
        }


async def compute_chart_async(birth_date: str, birth_time: str | None,
                              city: str | None, lat: float | None,
                              lon: float | None, tz: str | None = None) -> dict:
    """`compute_chart` в отдельном потоке.

    Расчёт эфемерид занимает сотни миллисекунд и держит GIL: из async-хендлера
    это означало, что на время построения карты бот не отвечал никому.
    """
    return await asyncio.to_thread(compute_chart, birth_date, birth_time, city,
                                   lat, lon, tz)


def _aspects(subject) -> list[dict]:
    """Мажорные аспекты между планетами, самые точные — первыми."""
    from kerykeion import NatalAspects  # type: ignore

    out = []
    for a in NatalAspects(subject).relevant_aspects:
        if a.aspect not in ASPECT_RU:
            continue
        if a.p1_name not in ASPECT_PLANETS or a.p2_name not in ASPECT_PLANETS:
            continue
        name, glyph = ASPECT_RU[a.aspect]
        out.append({
            "p1": POINT_RU.get(a.p1_name, a.p1_name),
            "p2": POINT_RU.get(a.p2_name, a.p2_name),
            "aspect": name, "glyph": glyph, "orb": round(abs(a.orbit), 1),
        })
    out.sort(key=lambda x: x["orb"])
    return out[:12]


def _full_chart(d: date, birth_time, city, lat, lon, tz) -> dict:
    from kerykeion import AstrologicalSubject  # type: ignore

    hour, minute = 12, 0
    if birth_time:
        hh, mm = birth_time.split(":")
        hour, minute = int(hh), int(mm)

    kwargs = dict(name="user", year=d.year, month=d.month, day=d.day,
                  hour=hour, minute=minute, city=city or "-")
    if lat is not None and lon is not None:
        subject = AstrologicalSubject(**kwargs, lat=lat, lng=lon,
                                      tz_str=tz or "Europe/Moscow", online=False)
    else:
        # без координат считаем по Москве — это честнее, чем поход в интернет,
        # который в офлайне уронит расчёт целиком
        subject = AstrologicalSubject(**{**kwargs, "city": "Moscow"},
                                      lat=55.75, lng=37.62,
                                      tz_str=tz or "Europe/Moscow", online=False)

    m = subject.model()

    planets = []
    for attr in ["sun", "moon", "mercury", "venus", "mars", "jupiter",
                 "saturn", "uranus", "neptune", "pluto"]:
        p = getattr(m, attr)
        planets.append({
            "name": PLANET_RU.get(p.name, p.name),
            "sign": SIGN_EN2RU.get(p.sign, p.sign),
            "deg": round(p.position, 1),
            "abs_deg": round(p.abs_pos, 1),
            "house": HOUSE_NUM.get(str(p.house), None),
            "retro": bool(getattr(p, "retrograde", False)),
        })

    houses = []
    for i, name in enumerate(HOUSE_ORDER, start=1):
        h = getattr(m, f"{name.lower()}_house")
        houses.append({"n": i, "sign": SIGN_EN2RU.get(h.sign, h.sign),
                       "deg": round(h.position, 1), "abs_deg": round(h.abs_pos, 1)})

    asc = m.ascendant
    mc = m.medium_coeli
    sun = planets[0]
    sym = next((s[1] for s in SIGNS if s[0] == sun["sign"]), "☉")
    element = next((s[2] for s in SIGNS if s[0] == sun["sign"]), "")
    # Лунные узлы (Раху — северный, Кету — южный) и Чёрная Луна — часть карты,
    # без них «полная карта» выглядит неполной.
    nodes = []
    for attr, ru in [("true_north_lunar_node", "Раху (Северный узел)"),
                     ("true_south_lunar_node", "Кету (Южный узел)"),
                     ("true_lilith", "Лилит (Чёрная Луна)")]:
        try:
            n = getattr(m, attr)
        except AttributeError:
            continue
        if n is None or getattr(n, "sign", None) is None:
            continue
        nodes.append({
            "name": ru,
            "sign": SIGN_EN2RU.get(n.sign, n.sign),
            "deg": round(n.position, 1),
            "house": HOUSE_NUM.get(str(getattr(n, "house", "")), None),
            "retro": bool(getattr(n, "retrograde", False)),
        })
    return {
        "mode": "full",
        "sun": {"sign": sun["sign"], "symbol": sym, "element": element},
        "ascendant": {"sign": SIGN_EN2RU.get(asc.sign, asc.sign),
                      "deg": round(asc.position, 1), "abs_deg": round(asc.abs_pos, 1)},
        "mc": {"sign": SIGN_EN2RU.get(mc.sign, mc.sign), "deg": round(mc.position, 1)},
        "planets": planets,
        "houses": houses,
        "aspects": _aspects(subject),
        "nodes": nodes,
    }


MOON_PHASES = [
    ("Новолуние", "🌑", "время намерений: загадай и отпусти"),
    ("Растущий серп", "🌒", "время первых шагов и новых знакомств"),
    ("Первая четверть", "🌓", "время решений: убери сомнения"),
    ("Растущая Луна", "🌔", "время набора силы: действуй смелее"),
    ("Полнолуние", "🌕", "пик энергии: эмоции громче разума, будь мягче"),
    ("Убывающая Луна", "🌖", "время благодарности и завершения дел"),
    ("Последняя четверть", "🌗", "время отпускать лишнее"),
    ("Старый серп", "🌘", "время тишины и восстановления"),
]


def moon_phase(d: date | None = None) -> dict:
    """Фаза и лунный день по синодическому циклу (точность ±1 день).

    Считаем день от новолуния; классические лунные календари ведут сутки от
    восхода Луны, поэтому в начале цикла возможна разница в сутки. Название
    «лунный день» сохраняем — так это ищут женщины, а «~» в текстах честно
    помечает приближение. Канон по восходу требует эфемеридных итераций и
    вынесен из сферы прогнозов.
    """
    d = d or date.today()
    known_new_moon = date(2000, 1, 6)
    days = (d - known_new_moon).days % 29.530588
    idx = int((days / 29.530588) * 8 + 0.5) % 8
    name, emoji, advice = MOON_PHASES[idx]
    return {"name": name, "emoji": emoji, "advice": advice,
            "day": round(days) + 1}


def today_sky(d: date | None = None) -> dict:
    """«Небо сегодня»: знак сезона Солнца + фаза Луны."""
    d = d or date.today()
    sign, sym, element = sun_sign_precise(d)
    return {"sun_season": {"sign": sign, "symbol": sym, "element": element},
            "moon": moon_phase(d)}


def chart_brief(chart: dict, *, time_known: bool | None = None) -> str:
    """Краткая текстовая выжимка карты для промпта агента.

    `time_known=False` — время рождения неизвестно, дома посчитаны по полудню:
    их нельзя показывать и тем более нельзя давать LLM делать домовые выводы.
    """
    if chart.get("mode") == "full" and chart.get("planets"):
        parts = []
        asc = chart.get("ascendant")
        if asc:
            parts.append(f"Асцендент в {asc['sign']}")
        for p in chart["planets"]:
            house = f", {p['house']} дом" if (p.get("house") and time_known) else ""
            parts.append(f"{p['name']} в {p['sign']}{house}"
                         + (" (R)" if p["retro"] else ""))
        brief = "; ".join(parts)
        if time_known is False:
            brief += ". ВНИМАНИЕ: время рождения неизвестно, дома рассчитаны по полдню — не используй их"
        aspects = chart.get("aspects") or []
        if aspects:
            brief += ". Ключевые аспекты: " + "; ".join(
                f"{a['p1']} {a['glyph']} {a['p2']} (орб {a['orb']}°)"
                for a in aspects[:6])
        return brief
    s = chart.get("sun", {})
    return f"Солнце в {s.get('sign', '?')} (стихия: {s.get('element', '?')}); расчёт упрощённый"
