from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.repo import users
from app.services import payment_monitor


@pytest.mark.asyncio
async def test_monitor_detects_stale_orders_and_deduplicates_alerts(db, monkeypatch):
    now = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
    await users.ensure(db, 1, "Владелец")
    await db.execute(
        "INSERT INTO orders(tg_id, kind, sku, title, amount_stars, status, payload, "
        "created_at) VALUES(?,?,?,?,?,?,?,?)",
        (1001, "product", "demo", "Demo", 100, "pending", "monitor-payload",
         (now - timedelta(hours=3)).isoformat()),
    )
    sent = []

    async def fake_send(_tg_id, text, *, html=True):
        sent.append((text, html))
        return True

    monkeypatch.setattr(payment_monitor.telegram, "send_message", fake_send)
    first = await payment_monitor.run(None, db, now=now)
    second = await payment_monitor.run(None, db, now=now + timedelta(minutes=1))

    assert first["status"] == "degraded"
    assert first["checks"]["pending_orders_stale"] == 1
    assert len(sent) == 1
    assert sent[0][1] is False
    assert "monitor-payload" not in sent[0][0]
    assert second["status"] == "degraded"
    third = await payment_monitor.run(None, db, now=now + timedelta(hours=7))
    assert third["status"] == "degraded"
    assert len(sent) == 2


@pytest.mark.asyncio
async def test_monitor_reconciles_recovery_and_failure_journal_is_safe(db):
    from app.api.routers.webhooks import _failure

    await users.ensure(db, 1, "Владелец")
    await _failure(db, "cryptobot", "signature_rejected", status_code=401)
    snapshot = await payment_monitor.build_snapshot(
        db, now=datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc), external=False)
    assert snapshot["checks"]["webhook_failures_24h"]["cryptobot"] == 1

    cur = await db.execute("SELECT code, status_code FROM payment_webhook_failures")
    row = await cur.fetchone()
    assert row["code"] == "signature_rejected"
    assert row["status_code"] == 401
    assert "payload" not in str(row).lower()
    assert "tg_id" not in str(row).lower()


@pytest.mark.asyncio
async def test_demo_payload_has_requested_figures_and_is_in_memory():
    from app.services.analytics import demo_dashboard

    data = await demo_dashboard(days=30)
    assert data["demo"] == {
        "active": True,
        "label": "ДЕМО · тестовые данные",
        "note": "Не реальные пользователи, заказы или баланс",
        "operating_days": 17,
    }
    assert data["overview"]["users_total"] == 451
    assert data["monetization"]["repeat_payers"] == 130
    assert data["overview"]["stars_total"] == 17056
    assert len(data["timeseries"]) == 30
