"""G18: единый бакет исходящих Telegram + ретрай createInvoiceLink.

Бакет — глобальный модуль-синглтон, поэтому между тестами сбрасываем его
состояние явно.
"""
from __future__ import annotations

import asyncio
import time

import pytest

from app.core import flood


@pytest.fixture(autouse=True)
def _reset_bucket():
    yield
    flood._tokens = flood.BURST
    flood._last = time.monotonic()


async def test_burst_allows_immediate_burst():
    """Залп в пределах BURST проходит без ожидания."""
    before = flood._tokens
    for _ in range(int(flood.BURST)):
        await asyncio.wait_for(flood.acquire(), timeout=0.1)
    assert flood._tokens < before, "токены должны расходоваться"


async def test_acquire_paces_when_bucket_empty():
    """Когда токены кончились, acquire ждёт пополнения, но не вешает запросившего."""
    flood._tokens = 0.0
    await asyncio.wait_for(flood.acquire(), timeout=2.0)


def test_control_methods_do_not_cost_bucket():
    assert flood.is_control("getUpdates")
    assert not flood.is_control("sendMessage")


async def test_invoice_link_retries_then_succeeds(db, monkeypatch):
    """Две неудачи подряд — третья попытка отдаёт ссылку (G18)."""
    from app.services import telegram as tg

    real_sleep = asyncio.sleep
    calls: list[str] = []

    async def fake_call(method: str, payload: dict) -> dict:
        calls.append(method)
        if len(calls) < 3:
            raise tg.TelegramError("ошибка сети")
        return "https://t.me/oracle_invoice?k=abc"

    monkeypatch.setattr(tg, "call", fake_call)
    # не ждём настоящие паузы в копеечных степенях двойки
    monkeypatch.setattr(tg.asyncio, "sleep", lambda s: real_sleep(0))

    link = await tg.create_invoice_link("Тариф Vip", "На месяц", "p-1", 99)
    assert link == "https://t.me/oracle_invoice?k=abc"
    assert calls == ["createInvoiceLink"] * 3


async def test_invoice_link_raises_after_all_retries(db, monkeypatch):
    """Если Telegram всё время падает — пробрасываем последнюю ошибку наверх."""
    from app.services import telegram as tg

    real_sleep = asyncio.sleep

    async def failing_call(method: str, payload: dict) -> dict:
        raise tg.TelegramError("сеть недоступна")

    monkeypatch.setattr(tg, "call", failing_call)
    monkeypatch.setattr(tg.asyncio, "sleep", lambda s: real_sleep(0))

    with pytest.raises(tg.TelegramError):
        await tg.create_invoice_link("Тариф Vip", "На месяц", "p-2", 99)


async def test_invoice_link_refuses_nonpositive_price():
    from app.services import telegram as tg
    with pytest.raises(tg.TelegramError):
        await tg.create_invoice_link("x", "x", "p", 0)
