"""Regression tests for security and privacy boundaries found in the audit."""
from __future__ import annotations

import hashlib
import hmac
import json
from time import time
from urllib.parse import urlencode

import pytest

from app.api.security import parse_init_data
from app.config import settings
from app.core import skills
from app.repo import dialog, users


def _signed_init_data(*, include_auth_date: bool = True) -> str:
    fields = {"user": json.dumps({"id": 1001}, separators=(",", ":"))}
    if include_auth_date:
        fields["auth_date"] = str(int(time()))
    check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_init_data_requires_fresh_auth_date(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "test:token")
    assert parse_init_data(_signed_init_data(include_auth_date=True))
    assert parse_init_data(_signed_init_data(include_auth_date=False)) is None


def test_init_data_rejects_duplicate_fields(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "test:token")
    data = _signed_init_data() + "&user=%7B%22id%22%3A1001%7D"
    assert parse_init_data(data) is None


async def test_memory_tools_cannot_bypass_memory_off(db, user):
    await users.update(db, user["tg_id"], memory_enabled=0)
    disabled_user = await users.get(db, user["tg_id"])

    saved = await skills._run_save_memory(
        db, disabled_user, {"fact": "секретный факт", "kind": "fact"})
    recalled = await skills._run_recall_memory(
        db, disabled_user, {"query": "секретный"})
    diary = await skills._run_recall_diary(db, disabled_user, {})

    assert "секретный" not in saved
    assert "секретный" not in recalled
    assert "секретный" not in diary
    assert not await dialog.get_memories(db, user["tg_id"])


async def test_diary_tool_is_blocked_when_memory_off(db, user):
    await users.update(db, user["tg_id"], memory_enabled=0)
    await dialog.add_diary(db, user["tg_id"], "личная запись")
    disabled_user = await users.get(db, user["tg_id"])
    result = await skills._run_recall_diary(db, disabled_user, {})
    assert "личная запись" not in result
    assert "выключена" in result


def test_production_config_fails_closed(monkeypatch):
    from app.api.main import _validate_production_config

    monkeypatch.setattr(settings, "dev_mode", False)
    monkeypatch.setattr(settings, "bot_token", "")
    monkeypatch.setattr(settings, "admin_id", 0)
    monkeypatch.setattr(settings, "webapp_url", "")
    with pytest.raises(RuntimeError, match="BOT_TOKEN"):
        _validate_production_config()
