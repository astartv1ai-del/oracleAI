from __future__ import annotations

import pytest

from app.core import palm


# Settings.provider_chain — read-only property; настраиваем её входные поля
# (тот же паттерн, что и в tests/test_llm.py::_two_provider_chain).
def _set_chain(monkeypatch, *, custom: bool, openai: bool, anthropic: bool = False,
               llm_provider: str = "off") -> None:
    monkeypatch.setattr(palm.settings, "custom_base_url",
                        "https://proxy.example" if custom else "")
    monkeypatch.setattr(palm.settings, "custom_model_main",
                        "proxy-model" if custom else "")
    monkeypatch.setattr(palm.settings, "openai_key", "k" if openai else "")
    monkeypatch.setattr(palm.settings, "anthropic_key", "k" if anthropic else "")
    monkeypatch.setattr(palm.settings, "llm_provider", llm_provider)


@pytest.mark.asyncio
async def test_custom_only_provider_drops_native_json_schema(monkeypatch):
    captured = {}

    async def fake_original(*args, **kwargs):
        captured.update(kwargs)
        return "{}"

    _set_chain(monkeypatch, custom=True, openai=False, llm_provider="custom")
    monkeypatch.setattr(palm, "_ORIGINAL_COMPLETE_VISION", fake_original)

    await palm._complete_vision_compat(
        "system", "user", "data:image/jpeg;base64,AA==", response_format={"type": "json_schema"}
    )
    assert captured["response_format"] is None


@pytest.mark.asyncio
async def test_native_schema_is_preserved_for_mixed_chain(monkeypatch):
    captured = {}

    async def fake_original(*args, **kwargs):
        captured.update(kwargs)
        return "{}"

    _set_chain(monkeypatch, custom=True, openai=True, llm_provider="openai")
    monkeypatch.setattr(palm, "_ORIGINAL_COMPLETE_VISION", fake_original)
    schema = {"type": "json_schema"}

    await palm._complete_vision_compat(
        "system", "user", "data:image/jpeg;base64,AA==", response_format=schema
    )
    assert captured["response_format"] == schema
