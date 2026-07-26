"""API новых разделов: практики, гороскопы, шеринг, web-оплата, новые экраны панели.

Соединение с БД подменяется через `dependency_overrides` — иначе тесты писали бы
в боевой файл, указанный в .env.
"""
from __future__ import annotations

import pytest

pytest.importorskip("httpx", reason="httpx нужен для тестов API")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.api.deps import get_db  # noqa: E402
from app.api.main import app  # noqa: E402
from app.repo import users  # noqa: E402


@pytest.fixture
async def client(db, user):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


def as_user(user, params: dict | None = None) -> dict:
    return {"dev_user": user["tg_id"], **(params or {})}


# ────────────────────────────── практики ──────────────────────────────────────

async def test_practices_catalog_has_categories(client, user):
    res = await client.get("/api/practices", params=as_user(user))
    assert res.status_code == 200
    data = res.json()
    assert data["categories"], "нет разделов практик"
    assert len(data["items"]) >= 10, "каталог практик почти пуст"
    assert all(p["steps"] and p["today_step"] for p in data["items"])


async def test_practices_filter_by_category(client, user):
    res = await client.get("/api/practices",
                           params=as_user(user, {"category": "love"}))
    assert res.status_code == 200
    items = res.json()["items"]
    assert items and {p["category"] for p in items} == {"love"}


async def test_practice_lifecycle(client, user):
    started = await client.post("/api/practices/money_mirror/start",
                                params=as_user(user))
    assert started.status_code == 200
    assert started.json()["started"] is True

    done = await client.post("/api/practices/money_mirror/done", params=as_user(user))
    assert done.status_code == 200
    assert done.json()["streak"] == 1
    assert done.json()["message"]

    again = await client.post("/api/practices/money_mirror/done", params=as_user(user))
    assert again.json()["already"] is True, "повторное нажатие накрутило стрик"

    stopped = await client.post("/api/practices/money_mirror/stop",
                                params=as_user(user))
    assert stopped.json()["ok"] is True


async def test_unknown_practice_is_404(client, user):
    res = await client.post("/api/practices/выдумка/start", params=as_user(user))
    assert res.status_code == 404


async def test_practice_card_endpoint(client, user):
    res = await client.get("/api/practices/mantra_lakshmi", params=as_user(user))
    assert res.status_code == 200
    item = res.json()
    assert item["text"], "у мантры нет текста"
    assert item["signs"], "нет знаков продвижения"


# ────────────────────────────── гороскопы ─────────────────────────────────────

async def test_horoscope_for_own_sign(client, user):
    res = await client.get("/api/horoscope", params=as_user(user))
    assert res.status_code == 200
    data = res.json()
    assert data["sign"] and data["text"]
    assert len(data["text"]) > 60


async def test_horoscope_all_signs(client, user):
    res = await client.get("/api/horoscope/all", params=as_user(user))
    assert res.status_code == 200
    assert len(res.json()) == 12


async def test_horoscope_unknown_sign_is_404(client, user):
    res = await client.get("/api/horoscope",
                           params=as_user(user, {"sign": "Дракон"}))
    assert res.status_code == 404


# ─────────────────────────── дневник: вопрос дня ──────────────────────────────

async def test_diary_prompt_is_personal(client, user):
    res = await client.get("/api/diary/prompt", params=as_user(user))
    assert res.status_code == 200
    data = res.json()
    assert data["prompt"] and not data["written_today"]

    await client.post("/api/diary", params=as_user(user),
                      json={"text": "день прошёл спокойно"})
    after = await client.get("/api/diary/prompt", params=as_user(user))
    assert after.json()["written_today"] is True


# ──────────────────────────── картинки для сторис ─────────────────────────────

async def test_share_state_is_reported(client, user):
    res = await client.get("/api/share/enabled", params=as_user(user))
    assert res.status_code == 200
    assert set(res.json()) == {"cards", "flag"}


async def test_share_reading_requires_ownership(client, db, user):
    """Прямая ссылка на картинку чужого расклада не должна работать."""
    from app.services import chat as chat_svc
    drawn = await chat_svc.draw(db, user, "one")
    await users.ensure(db, 4242, "Чужая")
    res = await client.get(f"/api/share/reading/{drawn['reading_id']}.png",
                           params={"dev_user": 4242})
    assert res.status_code == 404


async def test_share_missing_reading_is_404(client, user):
    res = await client.get("/api/share/reading/999999.png", params=as_user(user))
    assert res.status_code == 404


# ────────────────────────────── web-оплата ────────────────────────────────────

async def test_web_checkout_hidden_when_flag_off(client, user):
    """Флаг `web_payments` выключен по умолчанию — предлагать оплату нельзя."""
    res = await client.post("/api/shop/web-checkout", params=as_user(user),
                            json={"plan": "vip"})
    assert res.status_code == 404


async def test_web_checkout_needs_configuration(client, db, user):
    from app.repo import content
    await content.set_flag(db, "web_payments", is_on=True)
    res = await client.post("/api/shop/web-checkout", params=as_user(user),
                            json={"plan": "vip"})
    # ссылки на чекаут нет в .env — честный 503, а не битая ссылка клиентке
    assert res.status_code == 503


async def test_paddle_webhook_requires_signature(client):
    res = await client.post("/api/webhooks/paddle",
                            json={"event_id": "evt_1",
                                  "event_type": "transaction.completed"})
    assert res.status_code in (401, 503)


# ─────────────────────────── админка: новые экраны ────────────────────────────

async def test_admin_costs_are_reported(client, db):
    await users.ensure(db, 1, "Владелец")
    res = await client.get("/api/admin/costs", params={"dev_user": 1})
    assert res.status_code == 200
    data = res.json()
    for key in ("cost_usd", "calls", "per_paying_usd", "by_purpose", "by_model"):
        assert key in data, key


async def test_admin_safety_log(client, db, user):
    from app.services import chat as chat_svc
    await users.ensure(db, 1, "Владелец")
    await chat_svc.ask(db, user, "не хочу жить")
    res = await client.get("/api/admin/safety", params={"dev_user": 1})
    assert res.status_code == 200
    assert res.json()["recent"], "кризисное обращение не попало в панель"


async def test_admin_horoscopes_build(client, db):
    await users.ensure(db, 1, "Владелец")
    res = await client.post("/api/admin/horoscopes/build", params={"dev_user": 1})
    assert res.status_code == 200
    assert res.json()["built"] == 12
    listed = await client.get("/api/admin/horoscopes", params={"dev_user": 1})
    assert len(listed.json()["items"]) == 12
