"""Compare OracleAI, Kerykeion, flatlib and direct Swiss Ephemeris outputs."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = Path("/home/ubuntu/natal-engine-candidates")
if (CANDIDATES / "flatlib").is_dir():
    sys.path.insert(0, str(CANDIDATES / "flatlib"))

from app.core import astro  # noqa: E402

BIRTH = {"date": "1990-06-21", "time": "14:30", "lat": 55.79, "lon": 49.12, "tz": "Europe/Moscow"}
PLANETS = [("Sun", swe.SUN), ("Moon", swe.MOON), ("Mercury", swe.MERCURY),
           ("Venus", swe.VENUS), ("Mars", swe.MARS), ("Jupiter", swe.JUPITER),
           ("Saturn", swe.SATURN), ("Uranus", swe.URANUS), ("Neptune", swe.NEPTUNE),
           ("Pluto", swe.PLUTO)]


def arc_diff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def make_kerykeion_subject():
    from kerykeion import AstrologicalSubject

    return AstrologicalSubject(
        name="benchmark", year=1990, month=6, day=21, hour=14, minute=30,
        city="Kazan", lat=BIRTH["lat"], lng=BIRTH["lon"], tz_str=BIRTH["tz"], online=False,
        zodiac_type=astro.ZODIAC_TYPE,
        houses_system_identifier=astro.HOUSE_SYSTEM_IDENTIFIER,
        perspective_type=astro.PERSPECTIVE_TYPE,
    )


def kerykeion_values() -> dict[str, float]:
    model = make_kerykeion_subject().model()
    return {name: float(getattr(model, name.lower()).abs_pos) for name, _ in PLANETS}


def kerykeion_houses() -> dict[str, float]:
    model = make_kerykeion_subject().model()
    result = {"ASC": float(model.ascendant.abs_pos), "MC": float(model.medium_coeli.abs_pos)}
    for index, name in enumerate(("first", "second", "third", "fourth", "fifth", "sixth",
                                  "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"), 1):
        result[f"H{index}"] = float(getattr(model, f"{name}_house").abs_pos)
    return result


def swiss_values() -> dict[str, float]:
    # Kazan was UTC+04:00 for this historical date; the timezone-aware engine is
    # tested with the same explicit instant rather than a machine-local timezone.
    jd = swe.julday(1990, 6, 21, 10.5)
    values: dict[str, float] = {}
    for name, body in PLANETS:
        result, _ = swe.calc_ut(jd, body)
        values[name] = float(result[0])
    return values


def swiss_houses() -> dict[str, float]:
    jd = swe.julday(1990, 6, 21, 10.5)
    cusps, angles = swe.houses_ex(jd, BIRTH["lat"], BIRTH["lon"], astro.HOUSE_SYSTEM_IDENTIFIER.encode())
    result = {"ASC": float(angles[0]), "MC": float(angles[1])}
    result.update({f"H{index}": float(cusp) for index, cusp in enumerate(cusps, 1)})
    return result


def flatlib_values() -> dict[str, float]:
    from flatlib.chart import Chart
    from flatlib.datetime import Datetime
    from flatlib.geopos import GeoPos
    from flatlib import const

    chart = Chart(
        Datetime("1990/06/21", "14:30", "+04:00"),
        GeoPos("55n47", "49e07"),
    )
    constants = {
        "Sun": const.SUN, "Moon": const.MOON, "Mercury": const.MERCURY,
        "Venus": const.VENUS, "Mars": const.MARS, "Jupiter": const.JUPITER,
        "Saturn": const.SATURN, "Uranus": const.URANUS,
        "Neptune": const.NEPTUNE, "Pluto": const.PLUTO,
    }
    values = {}
    for name, _ in PLANETS:
        try:
            values[name] = float(chart.get(constants[name]).lon)
        except KeyError:
            # flatlib's traditional default intentionally omits outer planets.
            continue
    return values


def main() -> None:
    oracle_chart = astro.compute_chart(
        BIRTH["date"], BIRTH["time"], "Казань", BIRTH["lat"], BIRTH["lon"], BIRTH["tz"],
        time_known=True,
    )
    ru_to_en = {ru: en for en, ru in astro.PLANET_RU.items()}
    oracle_values = {ru_to_en.get(item["name"], item["name"]): float(item.get("abs_deg_exact", item["abs_deg"]))
                     for item in oracle_chart["planets"]}
    engines: dict[str, dict[str, float]] = {"oracleai": oracle_values}
    errors: dict[str, str] = {}
    for name, loader in (("kerykeion", kerykeion_values), ("swisseph", swiss_values), ("flatlib", flatlib_values)):
        try:
            engines[name] = loader()
        except Exception as exc:  # keep benchmark informative if optional engine breaks
            errors[name] = f"{type(exc).__name__}: {exc}"

    comparison = {}
    for planet, _ in PLANETS:
        row = {engine: round(values[planet], 8) for engine, values in engines.items() if planet in values}
        numeric = [values[planet] for values in engines.values() if planet in values]
        row["max_difference_arcsec"] = round((max(numeric) - min(numeric)) * 3600, 4) if numeric else None
        comparison[planet] = row

    house_engines = {"kerykeion": kerykeion_houses(), "swisseph": swiss_houses()}
    house_comparison = {}
    for point in house_engines["kerykeion"]:
        values = [engine[point] for engine in house_engines.values()]
        house_comparison[point] = {
            "kerykeion": round(house_engines["kerykeion"][point], 8),
            "swisseph": round(house_engines["swisseph"][point], 8),
            "difference_arcsec": round((max(values) - min(values)) * 3600, 4),
        }

    result = {
        "birth": BIRTH,
        "house_system_oracleai": astro.HOUSE_SYSTEM_NAME,
        "zodiac_type_oracleai": astro.ZODIAC_TYPE,
        "perspective_oracleai": astro.PERSPECTIVE_TYPE,
        "engines": list(engines),
        "houses": house_comparison,
        "comparison": comparison,
        "errors": errors,
        "oracleai_house_count": len(oracle_chart.get("houses") or []),
        "oracleai_aspect_count": len(oracle_chart.get("aspects") or []),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
