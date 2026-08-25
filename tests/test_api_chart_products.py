from __future__ import annotations

import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.api.main import app
from app.repo import readings, users


@pytest.fixture
async def product_client(db):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


def auth(user) -> dict:
    return {"dev_user": user["tg_id"]}


async def test_synastry_returns_versioned_owner_scoped_contract(product_client, db, user):
    chart = json.loads(user["chart_json"])
    partner_id = await readings.add_partner(
        db, user["tg_id"], "Алексей", "1991-02-03", birth_time="10:00",
        birth_city="Казань", lat=55.79, lon=49.12, tz="Europe/Moscow", chart=chart,
    )

    response = await product_client.post("/api/synastry", params=auth(user),
                                         json={"partner_id": partner_id})

    assert response.status_code == 200
    data = response.json()
    assert data["synastry_schema_version"] == 1
    assert data["product"] == "synastry"
    assert data["partner"]["partner_id"] == partner_id
    assert data["person"]["planets"]
    assert all("birth_date" not in item for item in data["person"]["planets"])


async def test_synastry_does_not_cross_owner_boundary(product_client, db, user):
    other = await users.ensure(db, 2002, "Другой пользователь", "other")
    partner_id = await readings.add_partner(
        db, other["tg_id"], "Чужой партнёр", "1991-02-03",
    )

    response = await product_client.post("/api/synastry", params=auth(user),
                                         json={"partner_id": partner_id})

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "partner_not_found"


async def test_synastry_rejects_date_only_partner(product_client, db, user):
    chart = json.loads(user["chart_json"])
    chart["precision"] = "date_only"
    partner_id = await readings.add_partner(
        db, user["tg_id"], "Без времени", "1991-02-03", chart=chart,
    )

    response = await product_client.post("/api/synastry", params=auth(user),
                                         json={"partner_id": partner_id})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "exact_charts_required"
    assert response.json()["detail"]["missing"] == ["partner"]


async def test_transits_returns_date_aware_contract_without_birth_pii(product_client, user):
    response = await product_client.post(
        "/api/transits", params=auth(user),
        json={"as_of": "2026-08-26", "time": "09:30"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transit_schema_version"] == 1
    assert data["product"] == "transits"
    assert data["precision"] == "instant"
    assert data["sampled_at"] == "2026-08-26T09:30:00+00:00"
    assert data["transit_planets"]
    assert "birth_date" not in json.dumps(data, ensure_ascii=False)


async def test_transits_rejects_invalid_date(product_client, user):
    response = await product_client.post(
        "/api/transits", params=auth(user),
        json={"as_of": "not-a-date"},
    )

    assert response.status_code == 422
