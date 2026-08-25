"""Structured product contracts for relationship and transit chart paths.

The module deliberately contains no FastAPI, database, or LLM code.  It consumes
already calculated canonical charts and returns stable JSON-ready dictionaries.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

from . import astro

SYNASTRY_SCHEMA_VERSION = 1
TRANSIT_SCHEMA_VERSION = 1

_NAME_TO_ID = {value: key for key, value in astro.PLANET_RU.items()}


class ChartProductError(ValueError):
    """A stable, client-facing product validation error."""

    def __init__(self, code: str, message: str, missing: list[str] | None = None):
        self.code = code
        self.message = message
        self.missing = missing or []
        super().__init__(message)



def _planet_rows(chart: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only canonical planetary rows, preserving exact longitudes."""
    rows = []
    for point in chart.get("planets") or []:
        if point.get("abs_deg_exact") is None and point.get("abs_deg") is None:
            continue
        name = str(point.get("name") or "")
        rows.append({
            "id": _NAME_TO_ID.get(name, name),
            "name": name,
            "label": name,
            "sign": point.get("sign"),
            "deg": point.get("deg"),
            "deg_exact": point.get("deg_exact"),
            "abs_deg": point.get("abs_deg"),
            "abs_deg_exact": point.get("abs_deg_exact"),
            "retro": bool(point.get("retro", False)),
        })
    return rows



def _aspect_row(aspect: dict[str, Any], *, first_role: str,
                second_role: str) -> dict[str, Any]:
    first_label = str(aspect.get("p1") or "")
    second_label = str(aspect.get("p2") or "")
    return {
        "first": _NAME_TO_ID.get(first_label, first_label),
        "first_label": first_label,
        "first_role": first_role,
        "second": _NAME_TO_ID.get(second_label, second_label),
        "second_label": second_label,
        "second_role": second_role,
        "code": aspect.get("code"),
        "label": aspect.get("aspect"),
        "glyph": aspect.get("glyph"),
        "orb_deg": aspect.get("orb"),
    }



def _require_planets(chart: dict[str, Any], role: str, *, exact: bool) -> None:
    if not isinstance(chart, dict) or not chart.get("planets"):
        raise ChartProductError("chart_required", "Для расчёта нужна сохранённая натальная карта.", [role])
    if exact and chart.get("precision") != "exact":
        raise ChartProductError(
            "exact_charts_required",
            "Для синастрии нужны две точные карты.",
            [role],
        )



def build_synastry_contract(owner_chart: dict[str, Any], partner_chart: dict[str, Any],
                            *, partner_id: int, partner_label: str) -> dict[str, Any]:
    """Build the exact two-chart contract from two owner-scoped saved charts."""
    _require_planets(owner_chart, "owner", exact=True)
    _require_planets(partner_chart, "partner", exact=True)
    owner_planets = _planet_rows(owner_chart)
    partner_planets = _planet_rows(partner_chart)
    raw_aspects = astro.synastry_aspects(owner_planets, partner_planets, limit=20)
    return {
        "synastry_schema_version": SYNASTRY_SCHEMA_VERSION,
        "product": "synastry",
        "precision": "exact",
        "person": {
            "role": "owner",
            "label": "Я",
            "chart_precision": owner_chart.get("precision"),
            "planets": owner_planets,
        },
        "partner": {
            "role": "partner",
            "partner_id": partner_id,
            "label": partner_label or "Партнёр",
            "chart_precision": partner_chart.get("precision"),
            "planets": partner_planets,
        },
        "aspects": [
            _aspect_row(item, first_role="owner", second_role="partner")
            for item in raw_aspects
        ],
        "limitations": [
            "Показываются мажорные межпланетные аспекты; дома, углы и композитная карта не строятся.",
        ],
    }




def build_transit_contract(natal_chart: dict[str, Any], *, as_of: date,
                           clock: time | None = None) -> dict[str, Any]:
    """Build a deterministic geocentric transit snapshot against natal planets.

    A neutral 0°/0°, UTC subject is used only to obtain geocentric longitudes;
    transit houses and angles are intentionally not part of this first contract.
    """
    _require_planets(natal_chart, "owner", exact=False)
    sample_time = clock or time(12, 0)
    transit_time = f"{sample_time.hour:02d}:{sample_time.minute:02d}"
    transit_chart = astro.compute_chart(
        as_of.isoformat(), transit_time, "UTC", 0.0, 0.0, "UTC", time_known=True,
    )
    transit_planets = _planet_rows(transit_chart)
    natal_planets = _planet_rows(natal_chart)
    raw_aspects = astro.synastry_aspects(transit_planets, natal_planets, limit=20)
    sampled_at = datetime(
        as_of.year, as_of.month, as_of.day, sample_time.hour, sample_time.minute,
        tzinfo=timezone.utc,
    )
    limitations = ["Транзитные дома и углы в этом контракте не строятся."]
    precision = "instant" if clock is not None else "day"
    if clock is None:
        limitations.insert(0, "Без времени показан дневной срез на 12:00 UTC; положение Луны внутри дня может меняться.")
    return {
        "transit_schema_version": TRANSIT_SCHEMA_VERSION,
        "product": "transits",
        "as_of": as_of.isoformat(),
        "sampled_at": sampled_at.isoformat(),
        "precision": precision,
        "natal_precision": natal_chart.get("precision"),
        "transit_planets": transit_planets,
        "aspects_to_natal": [
            _aspect_row(item, first_role="transit", second_role="natal")
            for item in raw_aspects
        ],
        "limitations": limitations,
    }
