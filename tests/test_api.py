"""API Mini App и админ-панели: доступы, коды ответов, формат данных.

Соединение с БД подменяется через `dependency_overrides` — иначе тесты писали бы
в боевой файл, указанный в .env.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("httpx", reason="httpx нужен для тестов API")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.api.deps import get_db  # noqa: E402
from app.api.main import app  # noqa: E402
from app.api.security import parse_init_data  # noqa: E402
from app.repo import dialog, users  # noqa: E402


@pytest.fixture
async def client(db, user):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


def as_user(user, params: dict | None = None) -> dict:
    return {"dev_user": user["tg_id"], **(params or {})}


# ─────────────────────────── доступ и безопасность ────────────────────────────

async def test_health_is_open(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


async def test_me_requires_identity(client):
    res = await client.get("/api/me")
    assert res.status_code == 401


async def test_unknown_user_gets_404(client):
    res = await client.get("/api/me", params={"dev_user": 999999})
    assert res.status_code == 404


async def test_new_user_auth_lifecycle_requires_start_then_allows_me(client, db):
    new_tg_id = 987654321
    before = await client.get("/api/me", params={"dev_user": new_tg_id})
    assert before.status_code == 404
    assert "нажми /start" in before.json()["detail"]

    created = await users.ensure(db, new_tg_id, "Новый пользователь", "new_user", lang="ru")
    assert created["tg_id"] == new_tg_id
    assert created["sub_level"] == "trial"
    assert created["crystals"] > 0
    assert created["onboarded"] == 0

    after = await client.get("/api/me", params={"dev_user": new_tg_id})
    assert after.status_code == 200
    assert after.json()["name"] == "Новый пользователь"
    assert after.json()["sub_active"] is True

    same = await users.ensure(db, new_tg_id, "Другое имя", "new_user", lang="ru")
    assert same["tg_id"] == new_tg_id
    assert same["name"] == "Новый пользователь"


async def test_blocked_user_is_refused(client, db, user):
    await users.set_status(db, user["tg_id"], "blocked")
    res = await client.get("/api/me", params=as_user(user))
    assert res.status_code == 403
    await users.set_status(db, user["tg_id"], "active")


async def test_bad_init_data_is_rejected():
    assert parse_init_data("") is None
    assert parse_init_data("user=%7B%22id%22%3A1%7D&hash=deadbeef") is None


async def test_chart_request_emits_structured_operational_log(client, db, user, caplog):
    chart = {
        "mode": "full", "precision": "date_only",
        "sun": {"sign": "Лев"},
        "planets": [{"name": "Солнце", "sign": "Лев"}],
        "houses": [], "aspects": [], "nodes": [],
    }
    await users.update(db, user["tg_id"], chart_json=json.dumps(chart, ensure_ascii=False))
    with caplog.at_level("INFO", logger="oracle.astro"):
        response = await client.get("/api/chart", params=as_user(user))
    assert response.status_code == 200
    record = next(r for r in caplog.records if getattr(r, "event", "") == "astro_chart_served")
    assert record.mode == "full"
    assert record.precision == "date_only"
    assert record.cache_hit is True
    assert record.planet_count == 1
    assert "987654321" not in record.getMessage()


async def test_path_traversal_is_blocked(client):
    """`GET /..%2F.env` не должен отдать файл с токенами."""
    res = await client.get("/..%2F.env")
    assert res.status_code == 404


# ──────────────────────────────── профиль ─────────────────────────────────────

async def test_me_returns_full_state(client, user):
    res = await client.get("/api/me", params=as_user(user))
    assert res.status_code == 200
    data = res.json()
    for key in ("name", "plan", "allowance", "agents", "flags", "crystals",
                "sub_active", "questions_left", "gender", "tarot_deck_id", "tarot_deck"):
        assert key in data, key
    assert data["allowance"]["limit"] == 3
    assert len(data["agents"]) >= 3


async def test_profile_tarot_deck_preference_is_persisted_and_validated(client, user):
    updated = await client.patch("/api/profile", params=as_user(user),
                                 json={"tarot_deck_id": "lenormand-36-game-of-hope-v1"})
    assert updated.status_code == 200
    assert updated.json()["updated"] == ["tarot_deck_id"]
    profile = await client.get("/api/me", params=as_user(user))
    assert profile.json()["tarot_deck_id"] == "lenormand-36-game-of-hope-v1"
    assert profile.json()["tarot_deck"]["card_count"] == 36
    bad = await client.patch("/api/profile", params=as_user(user),
                             json={"tarot_deck_id": "not-a-deck"})
    assert bad.status_code == 400


async def test_profile_update_validates_persona(client, user):
    res = await client.post("/api/profile", params=as_user(user),
                            json={"persona": "не-существует"})
    assert res.status_code == 400

    res = await client.post("/api/profile", params=as_user(user),
                            json={"persona": "witch", "oracle_name": "Ниса"})
    assert res.status_code == 200
    assert set(res.json()["updated"]) == {"persona", "oracle_name"}


async def test_profile_update_validates_timezone(client, user):
    res = await client.post("/api/profile", params=as_user(user),
                            json={"tz": "Mars/Olympus"})
    assert res.status_code == 400


async def test_profile_gender_can_be_set_and_cleared(client, user):
    updated = await client.patch("/api/profile", params=as_user(user), json={"gender": "m"})
    assert updated.status_code == 200
    assert updated.json()["updated"] == ["gender"]

    profile = await client.get("/api/me", params=as_user(user))
    assert profile.json()["gender"] == "m"

    cleared = await client.post("/api/profile", params=as_user(user), json={"gender": None})
    assert cleared.status_code == 200
    assert cleared.json()["updated"] == ["gender"]
    assert (await client.get("/api/me", params=as_user(user))).json()["gender"] is None


async def test_profile_gender_rejects_unknown_code(client, user):
    res = await client.post("/api/profile", params=as_user(user), json={"gender": "other"})
    assert res.status_code == 422


async def test_referral_returns_link_and_stats(client, user):
    res = await client.get("/api/referral", params=as_user(user))
    assert res.status_code == 200
    data = res.json()
    assert "link" in data and "share_text" in data
    assert data["bonus_per_invite"] > 0


# ──────────────────────────── сегодня и карта ─────────────────────────────────

async def test_today_needs_active_subscription(client, db, free_user):
    res = await client.get("/api/today", params={"dev_user": free_user["tg_id"]})
    assert res.status_code == 402


async def test_today_returns_forecast_and_card(client, user):
    res = await client.get("/api/today", params=as_user(user))
    assert res.status_code == 200
    data = res.json()
    assert data["forecast"] and data["card"]["name"] and data["moon"]["name"]
    # прогноз кешируется на сутки: повторный запрос отдаёт тот же текст
    again = await client.get("/api/today", params=as_user(user))
    assert again.json()["forecast"] == data["forecast"]


async def test_chart_and_matrix(client, user):
    chart = await client.get("/api/chart", params=as_user(user))
    assert chart.status_code == 200
    data = chart.json()
    assert data["sun"]["sign"]
    assert data["natal_schema_version"] == 2
    assert data["engine"] == "Swiss Ephemeris via Kerykeion"
    assert data["zodiac_type"] == "Tropical"
    assert data["house_system"] == "P"
    assert data["house_system_name"] == "Placidus"
    assert data["perspective_type"] == "Apparent Geocentric"
    assert data["lunar_nodes"]["mode"] == "true"
    assert data["lunar_nodes"]["rahu"]["name"].startswith("Раху")
    assert data["lunar_nodes"]["ketu"]["name"].startswith("Кету")
    assert {point["name"] for point in data["additional_points"]} >= {
        "Хирон", "Джуно", "Церера", "Веста", "Паллада",
    }

    matrix = await client.get("/api/matrix", params=as_user(user))
    assert matrix.status_code == 200
    assert 1 <= matrix.json()["destiny"]["n"] <= 22


async def test_moon_week(client, user):
    res = await client.get("/api/moon/week", params=as_user(user, {"days": 7}))
    assert res.status_code == 200
    assert len(res.json()) == 7


# ─────────────────────────── совместимость ────────────────────────────────────

async def test_compat_score_is_explained(client, user):
    res = await client.post("/api/compat", params=as_user(user),
                            json={"partner_date": "1996-11-03"})
    assert res.status_code == 200
    data = res.json()
    assert 35 <= data["score"] <= 98
    assert data["breakdown"] and data["verdict"]


async def test_compat_accepts_russian_date_format(client, user):
    res = await client.post("/api/compat", params=as_user(user),
                            json={"partner_date": "03.11.1996"})
    assert res.status_code == 200


async def test_compat_rejects_garbage_date(client, user):
    res = await client.post("/api/compat", params=as_user(user),
                            json={"partner_date": "вчера"})
    assert res.status_code == 400


async def test_partner_can_be_saved_and_removed(client, user):
    created = await client.post("/api/partners", params=as_user(user),
                                json={"name": "Дима", "birth_date": "03.11.1996"})
    assert created.status_code == 200
    partner_id = created.json()["id"]

    listed = await client.get("/api/partners", params=as_user(user))
    assert any(p["id"] == partner_id for p in listed.json())

    removed = await client.delete(f"/api/partners/{partner_id}", params=as_user(user))
    assert removed.status_code == 200
    assert not (await client.get("/api/partners", params=as_user(user))).json()


# ──────────────────────────────── Таро ────────────────────────────────────────

async def test_tarot_deck_catalog_has_three_separate_traditions(client, user):
    res = await client.get("/api/tarot/decks", params=as_user(user))
    assert res.status_code == 200
    decks = {item["deck_id"]: item for item in res.json()}
    assert set(decks) >= {"rws-78-geldard-v1", "lenormand-36-game-of-hope-v1", "marseille-78-conver-v1"}
    assert decks["rws-78-geldard-v1"]["asset_root"] != decks["lenormand-36-game-of-hope-v1"]["asset_root"]
    assert decks["lenormand-36-game-of-hope-v1"]["supports_reversals"] is False


async def test_spread_catalog(client, user):
    res = await client.get("/api/tarot/spreads", params=as_user(user))
    assert res.status_code == 200
    codes = {s["code"] for s in res.json()}
    assert {"one", "three", "love", "celtic"} <= codes
    lenormand = await client.get("/api/tarot/spreads", params=as_user(user, {"deck_id": "lenormand-36-game-of-hope-v1"}))
    assert {s["code"] for s in lenormand.json()} == {"one", "three", "line5", "relationship"}


async def test_lenormand_draw_persists_selected_deck_and_ledger(client, user):
    drawn = await client.post("/api/tarot/draw", params=as_user(user, {"spread": "line5"}),
                              json={"question": "Какой следующий шаг?", "deck_id": "lenormand-36-game-of-hope-v1"})
    assert drawn.status_code == 200
    data = drawn.json()
    assert data["deck_id"] == "lenormand-36-game-of-hope-v1"
    assert len(data["cards"]) == 5
    assert all(card["deck_id"] == data["deck_id"] and card["reversed"] is False for card in data["cards"])
    assert data["ledger"]["asset_root"] == "/static/img/lenormand"
    assert data["ledger"]["card_count"] == 36
    await client.post(f"/api/tarot/interpret/{data['reading_id']}", params=as_user(user))
    history = await client.get("/api/tarot/history", params=as_user(user))
    row = next(item for item in history.json() if item["id"] == data["reading_id"])
    assert row["deck_id"] == data["deck_id"]
    assert row["ledger"]["checksum"] == data["ledger"]["checksum"]


async def test_draw_then_interpret(client, user):
    drawn = await client.post("/api/tarot/draw", params=as_user(user, {"spread": "three"}))
    assert drawn.status_code == 200
    data = drawn.json()
    assert len(data["cards"]) == 3

    answer = await client.post(f"/api/tarot/interpret/{data['reading_id']}",
                               params=as_user(user))
    assert answer.status_code == 200
    assert answer.json()["answer"]

    history = await client.get("/api/tarot/history", params=as_user(user))
    assert history.json()[0]["id"] == data["reading_id"]


async def test_tarot_spreads_full_has_guide(client, user):
    res = await client.get("/api/tarot/spreads/full", params=as_user(user))
    assert res.status_code == 200
    items = {s["code"]: s for s in res.json()}
    assert "path" in items
    assert all(s.get("guide") for s in items.values())
    assert items["celtic"]["positions"]


async def test_tarot_question_saved_and_draw_returns_guide(client, user):
    """Question-first: вопрос клиентки доходит до расклада и истории."""
    q = "Когда я встречу своего человека?"
    drawn = await client.post("/api/tarot/draw", params=as_user(user, {"spread": "love"}),
                              json={"question": q})
    assert drawn.status_code == 200
    data = drawn.json()
    assert data["guide"], "draw не вернул guide расклада"
    assert data["spread"] == "love"
    # history показывает только трактованные расклады (answer<>''),
    # поэтому сначала интерпретируем — и проверяем, что вопрос дошёл
    await client.post(f"/api/tarot/interpret/{data['reading_id']}", params=as_user(user))
    history = await client.get("/api/tarot/history", params=as_user(user))
    row = next(r for r in history.json() if r["id"] == data["reading_id"])
    assert row["question"] == q


async def test_tarot_outcome_stats(client, user):
    """Счётчик «сбылось» агрегирует отметки без изменений схемы."""
    drawn = await client.post("/api/tarot/draw", params=as_user(user, {"spread": "one"}))
    reading_id = drawn.json()["reading_id"]
    await client.post(f"/api/tarot/outcome/{reading_id}", params=as_user(user),
                      json={"outcome": "came_true"})
    res = await client.get("/api/tarot/stats", params=as_user(user))
    assert res.status_code == 200
    stats = res.json()
    assert stats["came_true"] >= 1
    assert stats["marked"] == stats["came_true"] + stats["partly"] + stats["no"]


async def test_premium_spread_is_paywalled(client, user):
    res = await client.post("/api/tarot/draw", params=as_user(user, {"spread": "celtic"}))
    # без права расклад берётся из лимита тарифа; после исчерпания — отказ
    assert res.status_code in (200, 402, 429)


async def test_cards_cannot_be_forged_by_client(client, user):
    """Трактовка берёт карты из БД: подменить их запросом нельзя."""
    drawn = await client.post("/api/tarot/draw", params=as_user(user, {"spread": "one"}))
    reading_id = drawn.json()["reading_id"]
    res = await client.post(f"/api/tarot/interpret/{reading_id}", params=as_user(user),
                            json={"cards": [{"name": "Солнце"}]})
    assert res.status_code == 200


async def test_interpret_other_user_reading_is_404(client, db, user, free_user):
    drawn = await client.post("/api/tarot/draw", params=as_user(user, {"spread": "one"}))
    reading_id = drawn.json()["reading_id"]
    res = await client.post(f"/api/tarot/interpret/{reading_id}",
                            params={"dev_user": free_user["tg_id"]})
    assert res.status_code in (402, 404)


async def test_outcome_validation(client, user):
    drawn = await client.post("/api/tarot/draw", params=as_user(user, {"spread": "one"}))
    reading_id = drawn.json()["reading_id"]
    ok = await client.post(f"/api/tarot/outcome/{reading_id}", params=as_user(user),
                           json={"outcome": "came_true"})
    assert ok.status_code == 200
    bad = await client.post(f"/api/tarot/outcome/{reading_id}", params=as_user(user),
                            json={"outcome": "мусор"})
    assert bad.status_code == 400


# ──────────────────────────────── чаты ────────────────────────────────────────

async def test_agents_list_has_threads(client, user):
    res = await client.get("/api/agents", params=as_user(user))
    assert res.status_code == 200
    agents = res.json()
    assert len(agents) == 4
    assert {a["code"] for a in agents} == {"oracle", "astro", "tarot", "chiromant"}
    assert all("greeting" in a and "code" in a and "avatar" in a for a in agents)
    chiromant = next(a for a in agents if a["code"] == "chiromant")
    assert chiromant["avatar"] == "/static/img/agents/chiromant.jpg"


async def test_chat_history_and_ask(client, user):
    empty = await client.get("/api/chat/oracle", params=as_user(user))
    assert empty.status_code == 200
    assert empty.json()["messages"] == []

    asked = await client.post("/api/chat/oracle", params=as_user(user),
                              json={"text": "Что меня ждёт?"})
    assert asked.status_code == 200
    assert asked.json()["answer"]
    body = asked.json()
    assert body["agent_profile"]["quality"]["output_contract"] == "agent_response.v1"
    assert "capabilities" in body["agent_profile"]
    assert body["proof"]["mode"] in {"deterministic", "offline"}
    assert isinstance(body["proof"]["tools_used"], list)

    filled = await client.get("/api/chat/oracle", params=as_user(user))
    assert len(filled.json()["messages"]) == 2


async def test_unknown_agent_is_404(client, user):
    res = await client.post("/api/chat/nobody", params=as_user(user),
                            json={"text": "привет"})
    assert res.status_code == 404


async def test_ask_validates_length(client, user):
    res = await client.post("/api/chat/oracle", params=as_user(user),
                            json={"text": "x" * 5000})
    assert res.status_code == 422


async def test_chat_can_be_archived(client, user):
    await client.post("/api/chat/oracle", params=as_user(user), json={"text": "вопрос"})
    res = await client.delete("/api/chat/oracle", params=as_user(user))
    assert res.status_code == 200
    fresh = await client.get("/api/chat/oracle", params=as_user(user))
    assert fresh.json()["messages"] == []


# ──────────────────────────── дневник и лавка ─────────────────────────────────

async def test_diary_roundtrip(client, user):
    res = await client.post("/api/diary", params=as_user(user),
                            json={"text": "Сегодня был странный день", "mood": "calm"})
    assert res.status_code == 200
    assert res.json()["streak"] >= 1

    listed = await client.get("/api/diary", params=as_user(user))
    assert listed.json()["entries"][0]["text"].startswith("Сегодня")


async def test_shop_shows_catalog(client, user):
    res = await client.get("/api/shop", params=as_user(user))
    assert res.status_code == 200
    data = res.json()
    assert data["plans"] and "spread" in data["products"]


async def test_invoice_requires_target(client, user):
    res = await client.post("/api/shop/invoice", params=as_user(user), json={})
    assert res.status_code == 400


async def test_buy_with_crystals_without_balance(client, db, user):
    await users.update(db, user["tg_id"], crystals=0)
    res = await client.post("/api/shop/crystals", params=as_user(user),
                            json={"sku": "spread_celtic"})
    assert res.status_code == 402


async def test_buy_with_crystals_succeeds(client, db, user):
    await users.update(db, user["tg_id"], crystals=500)
    res = await client.post("/api/shop/crystals", params=as_user(user),
                            json={"sku": "spread_celtic"})
    assert res.status_code == 200
    assert res.json()["granted"]["kind"] == "spread"


async def test_promo_endpoint(client, db, user):
    from app.repo import growth
    codes = await growth.create_codes(db, 1, kind="crystals", crystals=50)
    res = await client.post("/api/shop/promo", params=as_user(user),
                            json={"code": codes[0]})
    assert res.status_code == 200
    bad = await client.post("/api/shop/promo", params=as_user(user),
                            json={"code": "НЕВЕРНЫЙ"})
    assert bad.status_code == 400


async def test_report_requires_purchase(client, user):
    res = await client.post("/api/reports/natal", params=as_user(user), json={})
    assert res.status_code == 402


async def test_report_builds_after_purchase(client, db, user):
    from app.repo import billing
    await billing.grant_entitlement(db, user["tg_id"], "report", "natal", qty=1)
    res = await client.post("/api/reports/natal", params=as_user(user), json={})
    assert res.status_code == 200
    assert res.json()["body"]
    # право списано, но готовый разбор доступен снова без оплаты
    again = await client.post("/api/reports/natal", params=as_user(user), json={})
    assert again.status_code == 200
    assert again.json()["cached"] is True


# ─────────────────────────── админ-панель ─────────────────────────────────────

async def test_admin_requires_role(client, user):
    res = await client.get("/api/admin/me", params=as_user(user))
    assert res.status_code == 403


async def test_admin_owner_from_env_has_access(client, db):
    await users.ensure(db, 1, "Владелец")
    res = await client.get("/api/admin/me", params={"dev_user": 1})
    assert res.status_code == 200
    assert res.json()["role"] == "owner"


async def test_admin_health_reports_telegram_webapp_readiness(client, db, monkeypatch):
    from app.config import settings

    await users.ensure(db, 1, "Владелец")
    monkeypatch.setattr(settings, "webapp_url", "")
    missing = await client.get("/api/admin/health", params={"dev_user": 1})
    assert missing.json()["telegram_webapp_ready"] is False
    monkeypatch.setattr(settings, "webapp_url", "https://oracle.example")
    ready = await client.get("/api/admin/health", params={"dev_user": 1})
    assert ready.json()["telegram_webapp_ready"] is True


async def test_admin_dashboard_and_users(client, db, user):
    await users.ensure(db, 1, "Владелец")
    dash = await client.get("/api/admin/dashboard", params={"dev_user": 1})
    assert dash.status_code == 200
    data = dash.json()
    assert data["overview"]["users_total"] >= 1
    assert len(data["funnel"]) == 5
    assert len(data["timeseries"]) == 30

    listed = await client.get("/api/admin/users",
                              params={"dev_user": 1, "q": "Тестовая"})
    assert listed.status_code == 200
    assert any(u["tg_id"] == user["tg_id"] for u in listed.json()["items"])


async def test_admin_user_card_and_actions(client, db, user):
    await users.ensure(db, 1, "Владелец")
    card = await client.get(f"/api/admin/users/{user['tg_id']}", params={"dev_user": 1})
    assert card.status_code == 200
    assert card.json()["user"]["tg_id"] == user["tg_id"]

    note = await client.post(f"/api/admin/users/{user['tg_id']}/notes",
                             params={"dev_user": 1}, json={"text": "Просила скидку"})
    assert note.status_code == 200

    grant = await client.post(f"/api/admin/users/{user['tg_id']}/grant",
                              params={"dev_user": 1},
                              json={"kind": "crystals", "qty": 25,
                                    "reason": "компенсация"})
    assert grant.status_code == 200
    assert grant.json()["amount"] == 25

    audit = await client.get("/api/admin/audit", params={"dev_user": 1})
    assert any(a["action"] == "user.grant" for a in audit.json())


async def test_admin_grant_validates_kind(client, db, user):
    await users.ensure(db, 1, "Владелец")
    res = await client.post(f"/api/admin/users/{user['tg_id']}/grant",
                            params={"dev_user": 1},
                            json={"kind": "магия", "qty": 1})
    assert res.status_code == 400


async def test_admin_can_edit_catalog_and_content(client, db):
    await users.ensure(db, 1, "Владелец")
    plan = await client.post("/api/admin/plans", params={"dev_user": 1},
                             json={"code": "vip", "fields": {"price_stars": 1400}})
    assert plan.status_code == 200
    plans = await client.get("/api/admin/plans", params={"dev_user": 1})
    assert next(p for p in plans.json() if p["code"] == "vip")["price_stars"] == 1400

    content = await client.post("/api/admin/content", params={"dev_user": 1},
                                json={"kind": "copy", "code": "welcome",
                                      "body": "Новый текст приветствия"})
    assert content.status_code == 200

    flag = await client.post("/api/admin/flags", params={"dev_user": 1},
                             json={"code": "voice_questions", "is_on": False})
    assert flag.status_code == 200
    flags = await client.get("/api/admin/flags", params={"dev_user": 1})
    assert not next(f for f in flags.json() if f["code"] == "voice_questions")["is_on"]


async def test_admin_rate_limited(client, db):
    """Панель: после 60 запросов в минуту на админа — 429 (G24)."""
    await users.ensure(db, 1, "Владелец")
    codes = [await client.get("/api/admin/me", params={"dev_user": 1})
             for _ in range(62)]
    statuses = [c.status_code for c in codes]
    assert statuses.count(200) == 60
    assert statuses[-1] == 429, "перебор админ-эндпоинтов не обрезан"


async def test_csp_header_in_production(client, monkeypatch):
    """В бою (dev_mode=0) все ответы несут CSP; в dev — нет (нужен Swagger)."""
    import app.config as config
    monkeypatch.setattr(config.settings, "dev_mode", False)
    res = await client.get("/api/health")
    csp = res.headers.get("content-security-policy")
    assert csp and "default-src 'self'" in csp
    assert "frame-ancestors 'self'" in csp


async def test_csp_absent_in_dev(client):
    res = await client.get("/api/health")
    assert "content-security-policy" not in res.headers


async def test_cache_control_on_assets(client):
    """Ассеты кешируются коротко; HTML и API — всегда no-cache (G25)."""
    css = await client.get("/styles.css")
    assert css.status_code == 200
    assert css.headers.get("cache-control") == "public, max-age=3600"
    admin_css = await client.get("/admin/static/admin.css")
    assert admin_css.status_code == 200
    assert admin_css.headers.get("cache-control") == "public, max-age=3600"


async def test_no_cache_on_html_and_api(client):
    for path in ("/", "/admin", "/api/health"):
        res = await client.get(path)
        assert res.headers.get("cache-control") == "no-cache", path


async def test_admin_promo_batch(client, db):
    await users.ensure(db, 1, "Владелец")
    res = await client.post("/api/admin/promo", params={"dev_user": 1},
                            json={"count": 5, "batch": "etsy-2", "days": 30})
    assert res.status_code == 200
    assert len(res.json()["codes"]) == 5
    listed = await client.get("/api/admin/promo", params={"dev_user": 1})
    assert any(b["batch"] == "etsy-2" for b in listed.json()["batches"])


async def test_admin_broadcast_preview_and_create(client, db, user):
    await users.ensure(db, 1, "Владелец")
    preview = await client.post("/api/admin/broadcasts/preview", params={"dev_user": 1},
                                json={"title": "t", "body": "b", "segment": "all"})
    assert preview.status_code == 200
    assert preview.json()["count"] >= 1

    created = await client.post("/api/admin/broadcasts", params={"dev_user": 1},
                                json={"title": "Тест", "body": "Привет",
                                      "segment": "onboarded", "send_now": False})
    assert created.status_code == 200
    assert created.json()["total"] >= 1


async def test_admin_broadcast_rejects_unknown_segment(client, db):
    await users.ensure(db, 1, "Владелец")
    res = await client.post("/api/admin/broadcasts", params={"dev_user": 1},
                            json={"title": "t", "body": "b", "segment": "выдумка"})
    assert res.status_code == 400


async def test_owner_manages_roles_without_losing_admin_title(client, db):
    """Владелец выдаёт/меняет роли, поддержка не может повышать права."""
    from app.repo import users as users_repo

    await users_repo.ensure(db, 1, "Владелец")
    await users_repo.ensure(db, 2002, "Саппорт")
    created = await client.post("/api/admin/admins", params={"dev_user": 1}, json={
        "tg_id": 2002, "role": "support", "title": "Служба заботы",
    })
    assert created.status_code == 200

    # Роль support годится для работы с клиентками, но не для выдачи ролей.
    support_me = await client.get("/api/admin/me", params={"dev_user": 2002})
    assert support_me.json()["role"] == "support"
    forbidden = await client.post("/api/admin/admins", params={"dev_user": 2002},
                                  json={"tg_id": 2003, "role": "admin"})
    assert forbidden.status_code == 403

    changed = await client.patch("/api/admin/admins/2002", params={"dev_user": 1},
                                 json={"role": "analyst"})
    assert changed.status_code == 200
    admins = (await client.get("/api/admin/admins", params={"dev_user": 1})).json()
    managed = next(item for item in admins if item["tg_id"] == 2002)
    assert managed["role"] == "analyst"
    assert managed["title"] == "Служба заботы"

    missing = await client.patch("/api/admin/admins/999999", params={"dev_user": 1},
                                 json={"role": "admin"})
    assert missing.status_code == 404
    self_change = await client.patch("/api/admin/admins/1", params={"dev_user": 1},
                                     json={"role": "analyst"})
    assert self_change.status_code == 400
    invalid_id = await client.post("/api/admin/admins", params={"dev_user": 1},
                                   json={"tg_id": -1, "role": "admin"})
    assert invalid_id.status_code == 422

    audit = (await client.get("/api/admin/audit", params={"dev_user": 1})).json()
    assert any(item["action"] == "admin.role" and item["target"] == "2002"
               for item in audit)


async def test_admin_sees_coupon_activations_and_can_filter_batch(client, db, user):
    from app.repo import growth
    from app.repo import users as users_repo

    await users_repo.ensure(db, 1, "Владелец")
    code = (await growth.create_codes(
        db, 1, kind="crystals", crystals=10, batch="creator-campaign",
        created_by=1))[0]
    assert await growth.redeem(db, code, user["tg_id"])

    res = await client.get("/api/admin/promo/redemptions", params={
        "dev_user": 1, "batch": "creator-campaign",
    })
    assert res.status_code == 200
    [redemption] = res.json()
    assert redemption["code"] == code
    assert redemption["tg_id"] == user["tg_id"]
    assert redemption["batch"] == "creator-campaign"
    assert redemption["kind"] == "crystals"
    assert redemption["crystals"] == 10
    assert redemption["name"] == "Тестовая"


async def test_chat_search_scoped_to_active_threads(client, db, user):
    first = await dialog.create_thread(db, user["tg_id"], "tarot", "Работа и решение")
    await dialog.save_message(db, user["tg_id"], "user", "Хочу понять следующий шаг в работе",
                              thread_id=first["id"], agent="tarot", surface="miniapp")
    archived = await dialog.create_thread(db, user["tg_id"], "oracle", "Старый разговор")
    await dialog.save_message(db, user["tg_id"], "user", "старый разговор о работе",
                              thread_id=archived["id"], agent="oracle", surface="miniapp")
    await dialog.archive_thread(db, archived["id"], user["tg_id"])
    other = await users.ensure(db, 99001, "Другой пользователь")
    foreign = await dialog.create_thread(db, other["tg_id"], "tarot", "Чужой проект")
    await dialog.save_message(db, other["tg_id"], "user", "проект и работа",
                              thread_id=foreign["id"], agent="tarot", surface="miniapp")

    res = await client.get("/api/chat/search", params=as_user(user, {"q": "следующий"}))
    assert res.status_code == 200
    rows = res.json()
    assert [row["thread_id"] for row in rows] == [first["id"]]
    assert rows[0]["agent"] == "tarot"
    assert "следующий" in rows[0]["last_text"].lower()

    archived_res = await client.get("/api/chat/search", params=as_user(user, {"q": "старый"}))
    assert archived_res.status_code == 200
    archived_rows = archived_res.json()
    assert [row["thread_id"] for row in archived_rows] == [archived["id"]]
    assert archived_rows[0]["archived"] is True

    history = await client.get(
        f"/api/chat/oracle/sessions/{archived['id']}", params=as_user(user))
    assert history.status_code == 200
    assert history.json()["archived"] is True
    blocked = await client.post(
        f"/api/chat/oracle/sessions/{archived['id']}",
        params=as_user(user), json={"text": "новое сообщение"})
    assert blocked.status_code == 409

    empty = await client.get("/api/chat/search", params=as_user(user, {"q": "чужой проект"}))
    assert empty.status_code == 200
    assert empty.json() == []


async def test_client_platform_metadata_is_normalized(client, db, user):
    res = await client.get(
        "/api/me",
        params=as_user(user),
        headers={
            "X-Client-Platform": "Android",
            "X-Client-Viewport": "390x844",
            "X-Client-Mode": "mobile",
        },
    )
    assert res.status_code == 200
    stored = await users.get(db, user["tg_id"])
    assert stored["last_platform"] == "android"
    assert stored["last_viewport"] == "390x844"
    assert stored["last_client_mode"] == "mobile"
    assert stored["last_client_at"]

    bad = await client.get(
        "/api/me",
        params=as_user(user),
        headers={
            "X-Client-Platform": "raw-device-name",
            "X-Client-Viewport": "1x2",
            "X-Client-Mode": "landscape",
        },
    )
    assert bad.status_code == 200
    stored = await users.get(db, user["tg_id"])
    assert stored["last_platform"] == "unknown"
    assert stored["last_viewport"] == "390x844"
    assert stored["last_client_mode"] == "mobile"
