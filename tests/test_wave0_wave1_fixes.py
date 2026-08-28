"""Регрессии для аудит-волны Wave 0/Wave 1.

Покрывают:
- SEC-001: fail-closed DEV_MODE при импорте конфигурации;
- SEC-010: age-gate требует год рождения, хранит только keyed-хеш;
- UX-009: публичный /api/public/config для deep-link в бота;
- CONT-001: билингвальные отказы 402/429;
- AI-010: выбор palm-промптов по языку клиентки.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.api.main import app
from app.repo import users


@pytest.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


@pytest.fixture
async def unconfirmed(db):
    """Пользователь без подтверждения возраста."""
    await users.ensure(db, 1007, "Без гейта")
    await users.update(db, 1007, onboarded=1, age_confirmed=0)
    return await users.get(db, 1007)


# ─────────────────────────── SEC-001: DEV_MODE guard ──────────────────────────

def test_dev_mode_fails_closed_at_import_for_non_dev_env():
    from app.config import assert_dev_mode_allowed
    with pytest.raises(RuntimeError):
        assert_dev_mode_allowed(True, "production")
    with pytest.raises(RuntimeError):
        assert_dev_mode_allowed(True, "staging")
    # dev/test и выключенный режим — легальные комбинации
    assert_dev_mode_allowed(True, "dev")
    assert_dev_mode_allowed(True, "test")
    assert_dev_mode_allowed(False, "production")


def test_dev_key_gate(monkeypatch):
    """Когда DEV_KEY задан, dev-вход без заголовка X-Dev-Key отклоняется."""
    from app.api import deps
    from app.config import settings

    class FakeRequest:
        def __init__(self, headers):
            self.headers = headers

    monkeypatch.setattr(settings, "dev_mode", True)
    monkeypatch.setattr(settings, "dev_key", "local-dev-key")
    assert deps._dev_identity_allowed(FakeRequest({})) is False
    assert deps._dev_identity_allowed(FakeRequest({"x-dev-key": "wrong"})) is False
    assert deps._dev_identity_allowed(FakeRequest({"x-dev-key": "local-dev-key"})) is True
    monkeypatch.setattr(settings, "dev_mode", False)
    assert deps._dev_identity_allowed(FakeRequest({"x-dev-key": "local-dev-key"})) is False


# ─────────────────────────── SEC-010: age gate ────────────────────────────────

async def test_age_confirmation_requires_birth_year(client, db, unconfirmed):
    res = await client.post("/api/profile", params={"dev_user": unconfirmed["tg_id"]},
                            json={"age_confirmed": True})
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "birth_year_required"
    row = await users.get(db, unconfirmed["tg_id"])
    assert row["age_confirmed"] == 0


async def test_age_confirmation_rejects_under_16(client, db, unconfirmed):
    from datetime import date
    young_year = date.today().year - 15
    res = await client.post("/api/profile", params={"dev_user": unconfirmed["tg_id"]},
                            json={"age_confirmed": True, "birth_year": young_year})
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "age_requirement_not_met"
    row = await users.get(db, unconfirmed["tg_id"])
    assert row["age_confirmed"] == 0
    assert not row["age_proof_hash"]


async def test_age_confirmation_stores_only_hash(client, db, unconfirmed):
    from datetime import date
    year = date.today().year - 30
    res = await client.post("/api/profile", params={"dev_user": unconfirmed["tg_id"]},
                            json={"age_confirmed": True, "birth_year": year})
    assert res.status_code == 200
    row = await users.get(db, unconfirmed["tg_id"])
    assert row["age_confirmed"] == 1
    assert row["age_proof_hash"]
    assert str(year) not in row["age_proof_hash"]
    assert row["age_proof_hash"] == users.age_proof_hash(unconfirmed["tg_id"], year)


async def test_age_confirmation_idempotent_retry(client, unconfirmed):
    """Повторный ретрай уже подтверждённого аккаунта не требует года заново."""
    from datetime import date
    year = date.today().year - 30
    first = await client.post("/api/profile", params={"dev_user": unconfirmed["tg_id"]},
                              json={"age_confirmed": True, "birth_year": year})
    assert first.status_code == 200
    retry = await client.post("/api/profile", params={"dev_user": unconfirmed["tg_id"]},
                              json={"age_confirmed": True})
    assert retry.status_code == 200


# ─────────────────────────── UX-009: public config ────────────────────────────

async def test_public_config_is_unauthenticated_and_bounded(client):
    res = await client.get("/api/public/config")
    assert res.status_code == 200
    body = res.json()
    assert set(body) <= {"bot_username", "webapp_url"}
    assert isinstance(body["bot_username"], str)


# ─────────────────────────── CONT-001: deny copy ──────────────────────────────

def test_access_denied_is_bilingual():
    from app.api.common.errors import access_denied

    class Verdict:
        reason = "limit_reached"

    ru = access_denied(Verdict(), lang="ru")
    en = access_denied(Verdict(), lang="en")
    assert ru.status_code == 429 and en.status_code == 429
    assert "Вернись" in ru.detail
    assert "dawn" in en.detail

    class SubOver:
        reason = "sub_over"

    assert access_denied(SubOver(), lang="en").status_code == 402
    assert "Renew" in access_denied(SubOver(), lang="en").detail


# ─────────────────────────── AI-010: palm prompts ─────────────────────────────

def test_palm_prompts_follow_user_language():
    from app.core.palm import PALM_SYSTEM, PALM_SYSTEM_EN, PALM_USER, PALM_USER_EN, palm_prompts
    system_ru, user_ru = palm_prompts("ru")
    system_en, user_en = palm_prompts("en")
    assert (system_ru, user_ru) == (PALM_SYSTEM, PALM_USER)
    assert (system_en, user_en) == (PALM_SYSTEM_EN, PALM_USER_EN)
    # EN-контракт содержит ту же JSON-схему и правила безопасности
    assert "palm-evidence-v1" in user_en and "evidence_state" in user_en
    assert "never" in system_en.lower() or "Never" in system_en
    assert "needs_photo" in user_en
    # fallback: неизвестный язык → RU
    assert palm_prompts("de") == (PALM_SYSTEM, PALM_USER)
