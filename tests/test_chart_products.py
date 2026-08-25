from datetime import date, time

import pytest

from app.core.chart_products import (
    ChartProductError,
    build_synastry_contract,
    build_transit_contract,
)


def _chart(*, precision="exact", offset=0.0):
    names = [
        ("Солнце", 10.0), ("Луна", 50.0), ("Меркурий", 80.0),
        ("Венера", 100.0), ("Марс", 140.0), ("Юпитер", 180.0),
        ("Сатурн", 220.0), ("Уран", 260.0), ("Нептун", 300.0),
        ("Плутон", 340.0),
    ]
    return {
        "mode": "full",
        "precision": precision,
        "planets": [
            {
                "name": name,
                "sign": "Овен",
                "deg": round((abs_deg + offset) % 30, 1),
                "deg_exact": (abs_deg + offset) % 30,
                "abs_deg": (abs_deg + offset) % 360,
                "abs_deg_exact": (abs_deg + offset) % 360,
                "retro": False,
            }
            for name, abs_deg in names
        ],
    }


def test_synastry_contract_is_versioned_and_labeled():
    result = build_synastry_contract(_chart(), _chart(offset=120), partner_id=7,
                                     partner_label="Алексей")

    assert result["synastry_schema_version"] == 1
    assert result["product"] == "synastry"
    assert result["precision"] == "exact"
    assert result["partner"]["partner_id"] == 7
    assert result["person"]["planets"][0]["id"] == "Sun"
    assert all(item["first_role"] == "owner" for item in result["aspects"])
    assert any(item["code"] == "trine" for item in result["aspects"])


def test_synastry_rejects_non_exact_chart():
    with pytest.raises(ChartProductError) as error:
        build_synastry_contract(_chart(precision="date_only"), _chart(),
                                partner_id=7, partner_label="Алексей")

    assert error.value.code == "exact_charts_required"
    assert error.value.missing == ["owner"]


def test_transit_contract_has_day_precision_without_time():
    result = build_transit_contract(_chart(), as_of=date(2026, 8, 26))

    assert result["transit_schema_version"] == 1
    assert result["product"] == "transits"
    assert result["precision"] == "day"
    assert result["as_of"] == "2026-08-26"
    assert result["sampled_at"] == "2026-08-26T12:00:00+00:00"
    assert result["transit_planets"]
    assert "Лун" in result["limitations"][0]


def test_transit_contract_marks_explicit_time_as_instant():
    result = build_transit_contract(_chart(precision="date_only"),
                                    as_of=date(2026, 8, 26), clock=time(9, 30))

    assert result["precision"] == "instant"
    assert result["sampled_at"] == "2026-08-26T09:30:00+00:00"
    assert result["natal_precision"] == "date_only"


@pytest.mark.asyncio
async def test_agent_synastry_context_includes_versioned_contract(db, user):
    import json

    from app.core import agent
    from app.repo import readings

    chart = json.loads(user["chart_json"])
    await readings.add_partner(
        db, user["tg_id"], "Алексей", "1991-02-03", birth_time="10:00",
        birth_city="Казань", lat=55.79, lon=49.12, tz="Europe/Moscow", chart=chart,
    )
    evidence = await agent._synastry_data(db, user, "1991-02-03")

    assert evidence is not None
    assert "synastry contract" in evidence
    assert '"synastry_schema_version": 1' in evidence


@pytest.mark.asyncio
async def test_agent_transit_tool_includes_structured_evidence(db, user):
    from app.core import skills

    evidence = await skills._run_get_transits(db, user, {"as_of": "2026-08-26"})

    assert "Детерминированное transit evidence" in evidence
    assert '"transit_schema_version": 1' in evidence
    assert '"as_of": "2026-08-26"' in evidence
