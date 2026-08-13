from __future__ import annotations

from scripts import release_gate


def test_static_release_gate_passes_repository_contract():
    assert release_gate.run(production=False) == []


def test_production_release_gate_fails_closed_without_real_env(monkeypatch):
    for name in ("APP_ENV", "DEV_MODE", "WEBAPP_URL", "BOT_TOKEN", "ADMIN_ID"):
        monkeypatch.delenv(name, raising=False)
    errors = release_gate.run(production=True)
    assert "APP_ENV must equal production" in errors
    assert "DEV_MODE must be disabled" not in errors
    assert "WEBAPP_URL must be an HTTPS URL" in errors
    assert "BOT_TOKEN is missing" in errors
    assert "ADMIN_ID is missing" in errors


def test_production_release_gate_accepts_minimal_safe_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEV_MODE", "0")
    monkeypatch.setenv("WEBAPP_URL", "https://oracle.example")
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("ADMIN_ID", "1001")
    assert release_gate.run(production=True) == []
