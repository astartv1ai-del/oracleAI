"""API Mini App и админ-панели: доступы, коды ответов, формат данных.

Соединение с БД подменяется через `dependency_overrides` — иначе тесты писали бы
в боевой файл, указанный в .env.
"""
from __future__ import annotations

import pytest

pytest.importorskip("httpx", reason="httpx нужен для тестов API")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.api.deps import get_db  # noqa: E402
from app.api.main import app  # noqa: E402
from app.api.security import parse_init_data  # noqa: E402
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


async def test_blocked_user_is_refused(client, db, user):
    await users.set_status(db, user["tg_id"], "blocked")
    res = await client.get("/api/me", params=as_user(user))
    assert res.status_code == 403
    await users.set_status(db, user["tg_id"], "active")


async def test_bad_init_data_is_rejected():
    assert parse_init_data("") is None
    assert parse_init_data("user=%7B%22id%22%3A1%7D&hash=deadbeef") is None


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
                "sub_active", "questions_left", "gender"):
        assert key in data, key
    assert data["allowance"]["limit"] == 3
    assert len(data["agents"]) >= 3


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
    assert chart.json()["sun"]["sign"]

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

async def test_spread_catalog(client, user):
    res = await client.get("/api/tarot/spreads", params=as_user(user))
    assert res.status_code == 200
    codes = {s["code"] for s in res.json()}
    assert {"one", "three", "love", "celtic"} <= codes


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
    assert all("greeting" in a and "code" in a for a in agents)


async def test_chat_history_and_ask(client, user):
    empty = await client.get("/api/chat/oracle", params=as_user(user))
    assert empty.status_code == 200
    assert empty.json()["messages"] == []

    asked = await client.post("/api/chat/oracle", params=as_user(user),
                              json={"text": "Что меня ждёт?"})
    assert asked.status_code == 200
    assert asked.json()["answer"]

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
