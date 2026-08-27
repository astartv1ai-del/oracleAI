from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core import astro, tarot, vedic
from app.core.chart_products import circular_midpoint


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "domain_golden.json").read_text(encoding="utf-8")
)


def _jsonable(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


def _chart_summary(chart: dict) -> dict:
    return {
        "mode": chart.get("mode"),
        "precision": chart.get("precision"),
        "sun": chart.get("sun"),
        "ascendant": chart.get("ascendant"),
        "mc": chart.get("mc"),
        "planets": chart.get("planets"),
        "houses": chart.get("houses"),
        "aspects": chart.get("aspects"),
        "nodes": chart.get("nodes"),
        "calculation": chart.get("calculation"),
    }


@pytest.mark.parametrize("case", FIXTURE["cases"], ids=lambda case: case["input"]["id"])
def test_chart_golden_case_is_reproducible(case):
    inputs = case["input"]
    actual = astro.compute_chart(
        inputs["birth_date"], inputs["birth_time"], inputs["city"],
        inputs["lat"], inputs["lon"], inputs["tz"],
        time_known=inputs["time_known"],
    )
    assert _jsonable(_chart_summary(actual)) == case["output"]
    repeated = astro.compute_chart(
        inputs["birth_date"], inputs["birth_time"], inputs["city"],
        inputs["lat"], inputs["lon"], inputs["tz"],
        time_known=inputs["time_known"],
    )
    assert _jsonable(_chart_summary(repeated)) == _jsonable(_chart_summary(actual))


def test_time_without_timezone_never_becomes_exact():
    chart = astro.compute_chart(
        "1990-06-21", "14:30", "Kazan", 55.79, 49.12, None, time_known=True,
    )
    assert chart["precision"] in {"date_only", "sun_only"}
    assert chart["calculation"]["input"]["precision_reason"] == "date_only_missing_timezone"
    assert chart.get("ascendant") is None
    assert chart.get("houses") == []


def test_invalid_coordinates_are_not_promoted_to_angular_precision():
    chart = astro.compute_chart(
        "1990-06-21", "14:30", "Kazan", 91, 181, "Europe/Moscow", time_known=True,
    )
    assert chart["precision"] in {"time_without_location", "date_only", "sun_only"}
    assert chart.get("ascendant") is None
    assert chart.get("houses") == []


def test_aspect_orb_boundary_is_explicit_and_deterministic():
    inside = astro.synastry_aspects(
        [{"name": "Солнце", "abs_deg": 0}],
        [{"name": "Луна", "abs_deg": 8}],
    )
    outside = astro.synastry_aspects(
        [{"name": "Солнце", "abs_deg": 0}],
        [{"name": "Луна", "abs_deg": 8.0001}],
    )
    assert inside and not outside


def test_circular_midpoint_handles_zero_boundary():
    assert circular_midpoint(350, 10) == 0


def test_vedic_date_only_contract_is_separate_and_honest():
    envelope = vedic.compute_vedic_chart(
        "1990-06-21", None, "Kazan", 55.79, 49.12, "Europe/Moscow", time_known=False,
    )
    assert envelope["tradition"] == "Vedic/Jyotish"
    assert envelope["ayanamsa"] == "Lahiri"
    assert envelope["result"]["precision"] == "date_only"
    assert envelope["result"]["lagna"] is None
    assert envelope["result"]["houses"] == []
    assert "sidereal" in envelope["limitations"][0] or envelope["limitations"]


def test_golden_pure_contracts_match_runtime_invariants():
    pure = FIXTURE["pure_contracts"]
    assert pure["circular_midpoint_350_10"] == circular_midpoint(350, 10)
    assert len(tarot.DECK) == pure["tarot_deck_counts"]["total"] == 78
    assert len({card["img"] for card in tarot.DECK}) == pure["tarot_deck_counts"]["unique_ids"] == 78
    assert pure["tarot_deck_counts"]["majors"] == 22
    assert pure["tarot_deck_counts"]["minors"] == 56
    assert set(pure["tarot_deck_counts"]["suits"]) == set(tarot.SUITS)
    assert all(count == 14 for count in pure["tarot_deck_counts"]["suits"].values())


def test_typed_domain_failures_are_not_silent():
    with pytest.raises(ValueError):
        astro.compute_chart("1990-06-21", "25:90", "Kazan", 55.79, 49.12, "Europe/Moscow")
    with pytest.raises(ValueError):
        vedic.get_nakshatra(-0.1)
    with pytest.raises(ValueError):
        tarot.replay_ledger([{"img": "not-a-card", "reversed": False}], "one")


@pytest.mark.asyncio
async def test_skill_tarot_tool_rejects_invalid_sizes_instead_of_clamping():
    from app.core import skills

    for raw in (0, 13, -1, 3.5, True, "3.5"):
        result = await skills._run_draw_tarot(None, {}, {"n": raw})
        assert "целым от 1 до 12" in result


@pytest.mark.asyncio
async def test_skill_chart_tool_uses_calculated_precision_not_profile_flag():
    from app.core import skills

    chart = astro.compute_chart(
        "1990-06-21", "14:30", "Kazan", 55.79, 49.12, None, time_known=True,
    )
    user = {"chart_json": json.dumps(chart, ensure_ascii=False), "birth_time_known": 1}
    result = await skills._run_get_chart(None, user, {})

    assert "Точность рождения: дата без подтверждённого времени" in result
    assert "точное; рассчитаны углы и дома" not in result
    assert "Куспиды домов:" not in result


@pytest.mark.asyncio
async def test_skill_vimshottari_requires_confirmed_time_and_timezone():
    from app.core import skills

    missing_confirmation = await skills._run_get_vimshottari_dasha(
        None,
        {"birth_date": "1990-06-21", "birth_time": "14:30", "birth_time_known": 0, "tz": "Europe/Moscow"},
        {},
    )
    missing_timezone = await skills._run_get_vimshottari_dasha(
        None,
        {"birth_date": "1990-06-21", "birth_time": "14:30", "birth_time_known": 1, "tz": None},
        {},
    )

    assert "подтверждённое время" in missing_confirmation
    assert "часовой пояс" in missing_timezone


@pytest.mark.asyncio
async def test_monthly_report_persists_versioned_privacy_safe_snapshot(db, user, monkeypatch):
    from app.core import agent
    from app.repo import readings

    monkeypatch.setattr(agent.llm, "enabled", lambda: False)
    await agent.monthly_report(db, user)
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    row = await readings.get_report(db, user["tg_id"], "monthly", period)

    metadata = json.loads(row["meta_json"])
    assert metadata["evidence_schema_version"] == "monthly-evidence-v1"
    assert metadata["evidence_kind"] == "monthly"
    assert isinstance(metadata["readings_count"], int)
    assert isinstance(metadata["diary_count"], int)
    assert "raw diary" in metadata["privacy_note"]
