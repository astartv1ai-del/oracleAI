from __future__ import annotations

import json
from pathlib import Path

from app.repo import analytics as analytics_repo
from app.services import analytics
from scripts.validate_monetization_assumptions import validate


ASSUMPTIONS = Path(__file__).resolve().parents[1] / "docs" / "MONETIZATION_ASSUMPTIONS.csv"


async def test_monetization_event_filters_unapproved_props(db):
    assert await analytics.track_monetization(
        db,
        analytics.E_PAYWALL_CHOICE,
        1001,
        surface="miniapp",
        sku="report_natal",
        channel="miniapp",
        price_variant="core_a",
        credit_band_name="large",
        result_category="report",
        reason="question_text_should_not_pass",
    )
    cur = await db.execute(
        "SELECT props_json FROM events WHERE tg_id=? AND name=?",
        (1001, analytics.E_PAYWALL_CHOICE),
    )
    props = json.loads((await cur.fetchone())["props_json"])
    assert props == {
        "sku": "report_natal",
        "channel": "miniapp",
        "price_variant": "core_a",
        "credit_band": "large",
        "result_category": "report",
    }
    assert not await analytics.track_monetization(
        db, "client_created_revenue_event", 1001, surface="miniapp",
    )


async def test_monetization_dashboard_does_not_fake_net_revenue(db):
    await analytics.track_monetization(
        db, analytics.E_CREDIT_PACK_PAID, 1001,
        surface="bot", sku="crystals_250", channel="bot", credit_band_name="large",
    )
    await analytics.track_monetization(
        db, analytics.E_CREDIT_SPENT, 1001,
        surface="bot", sku="report_natal", channel="bot",
        credit_band_name="medium", result_category="report",
    )
    kpis = await analytics_repo.monetization_kpis(db, days=30)
    assert kpis["credit_pack_paid"] == 1
    assert kpis["credit_spent"] == 1
    assert kpis["net_revenue_estimate"] is None
    assert kpis["contribution_margin_estimate"] is None
    assert kpis["status"] == "estimated_requires_settlement_inputs"


def test_monetization_assumptions_contract_is_valid():
    assert validate(ASSUMPTIONS) == []
