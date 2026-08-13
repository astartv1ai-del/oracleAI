"""Трекинг событий — обёртка, которая никогда не ломает пользовательский путь.

Аналитика полезна, но не важнее ответа клиентке. Если запись события упала
(заблокированная БД, битые props), продукт продолжает работать, а мы видим это
в логах. Поэтому все имена событий и `track` живут здесь, а не вызываются из
хендлеров напрямую.
"""
from __future__ import annotations

import asyncio
import logging

from ..repo import analytics as repo

log = logging.getLogger("oracle.analytics")

#: Фоновые записи событий. Сильная ссылка, чтобы задача не умерла по сборке мусора.
_pending: set[asyncio.Task] = set()

# Реэкспорт имён событий: хендлеры импортируют их отсюда, а не из репозитория.
E_START = repo.E_START
E_ONBOARD_DONE = repo.E_ONBOARD_DONE
E_QUESTION = repo.E_QUESTION
E_TAROT = repo.E_TAROT
E_FORECAST = repo.E_FORECAST
E_LIMIT_HIT = repo.E_LIMIT_HIT
E_SHOP_VIEW = repo.E_SHOP_VIEW
E_INVOICE = repo.E_INVOICE
E_PAID = repo.E_PAID
E_PROMO = repo.E_PROMO
E_REFERRAL = repo.E_REFERRAL
E_MINIAPP_OPEN = repo.E_MINIAPP_OPEN
E_CHURN_WARN = repo.E_CHURN_WARN
E_AGE_CONFIRMED = repo.E_AGE_CONFIRMED
E_FIRST_RITUAL = repo.E_FIRST_RITUAL
E_FIRST_QUESTION = repo.E_FIRST_QUESTION
E_RETURN_D1 = repo.E_RETURN_D1
E_RETURN_D7 = repo.E_RETURN_D7
E_PAYWALL_VIEW = repo.E_PAYWALL_VIEW
E_PAYWALL_CHOICE = repo.E_PAYWALL_CHOICE
E_CREDIT_PACK_CHECKOUT_STARTED = repo.E_CREDIT_PACK_CHECKOUT_STARTED
E_CREDIT_PACK_PAID = repo.E_CREDIT_PACK_PAID
E_CREDIT_SPENT = repo.E_CREDIT_SPENT
E_CREDIT_BALANCE_LOW = repo.E_CREDIT_BALANCE_LOW
E_REPORT_DELIVERED = repo.E_REPORT_DELIVERED
E_REFUND_REQUESTED = repo.E_REFUND_REQUESTED
E_REFUND_COMPLETED = repo.E_REFUND_COMPLETED

_MONETIZATION_EVENTS = {
    E_PAYWALL_VIEW, E_PAYWALL_CHOICE, E_CREDIT_PACK_CHECKOUT_STARTED,
    E_CREDIT_PACK_PAID, E_CREDIT_SPENT, E_CREDIT_BALANCE_LOW,
    E_REPORT_DELIVERED, E_REFUND_REQUESTED, E_REFUND_COMPLETED,
}
_ALLOWED_SURFACES = {"bot", "miniapp", "admin", "system"}
_ALLOWED_CATEGORIES = _ALLOWED_SURFACES | {"web"}
_ALLOWED_CREDIT_BANDS = {"micro", "small", "medium", "large"}
_ALLOWED_RESULT_CATEGORIES = {"report", "spread", "question", "crystals", "plan", "daily", "tarot", "natal", "compatibility"}
_ALLOWED_REASONS = {"threshold_20", "support_request", "provider_refund", "delivery_failed"}


def credit_band(amount: int | None) -> str:
    value = max(0, int(amount or 0))
    if value <= 10:
        return "micro"
    if value <= 50:
        return "small"
    if value <= 150:
        return "medium"
    return "large"


async def track_monetization(db, name: str, tg_id: int | None = None, *,
                             surface: str = "system", sku: str | None = None,
                             channel: str | None = None,
                             price_variant: str | None = None,
                             credit_band_name: str | None = None,
                             result_category: str | None = None,
                             reason: str | None = None) -> bool:
    """Write an allowlisted monetization event without free-form payloads."""
    if name not in _MONETIZATION_EVENTS or surface not in _ALLOWED_SURFACES:
        return False
    values = {
        "sku": sku,
        "channel": channel,
        "price_variant": price_variant,
        "credit_band": credit_band_name,
        "result_category": result_category,
        "reason": reason,
    }
    props = {}
    for key, value in values.items():
        if value is None:
            continue
        if key == "channel" and value in _ALLOWED_CATEGORIES:
            props[key] = value
        elif key == "credit_band" and value in _ALLOWED_CREDIT_BANDS:
            props[key] = value
        elif key == "result_category" and value in _ALLOWED_RESULT_CATEGORIES:
            props[key] = value
        elif key == "reason" and value in _ALLOWED_REASONS:
            props[key] = value
        elif key in {"sku", "price_variant"} and isinstance(value, str):
            if 0 < len(value) <= 48 and all(char.isalnum() or char in "_-.:" for char in value):
                props[key] = value
    return await track_now(db, name, tg_id, props=props, surface=surface)


async def track(db, name: str, tg_id: int | None = None, *,
                props: dict | None = None, surface: str = "bot") -> None:
    """Ставит запись события в фон и возвращается сразу.

    Хендлеры ждут `await track(...)`, но тело не делает ни одной await-паузы:
    INSERT уходит в отдельную задачу, а пользовательский запрос не держится ради
    аналитики. `drain()` даёт тестам и шатдауну дождаться фоновых записей.
    """
    task = asyncio.get_running_loop().create_task(
        _record(db, name, tg_id, props, surface))
    _pending.add(task)
    task.add_done_callback(_pending.discard)


async def _record(db, name: str, tg_id: int | None, props, surface: str) -> None:
    try:
        await repo.track(db, name, tg_id, props=props, surface=surface)
    except Exception as e:  # noqa: BLE001
        log.warning("событие %s не записано: %s", name, e)


async def track_now(db, name: str, tg_id: int | None = None, *,
                   props: dict | None = None, surface: str = "system") -> bool:
    """Синхронная запись для server-side milestone, где важен read-after-write."""
    try:
        await repo.track(db, name, tg_id, props=props, surface=surface)
    except Exception as e:  # noqa: BLE001
        log.warning("событие %s не записано: %s", name, e)
        return False
    return True


async def track_once(db, name: str, tg_id: int, *,
                     props: dict | None = None, surface: str = "miniapp") -> bool:
    """Атомарно записывает milestone один раз; имена задаются сервером."""
    try:
        return await repo.track_once(db, name, tg_id, props=props, surface=surface)
    except Exception as e:  # noqa: BLE001
        log.warning("milestone %s не записан: %s", name, e)
        return False


async def drain() -> None:
    """Ждёт фоновые записи событий. Тесты и корректный шатдаун."""
    if _pending:
        await asyncio.gather(*_pending, return_exceptions=True)


async def prune(db, days: int = 120) -> int:
    """Чистит события и учёт LLM старее окна. Дашборд живёт на rolling-окнах,
    история на годы только раздувает базу."""
    return await repo.prune_analytics(db, days)


async def dashboard(db, *, days: int = 30) -> dict:
    """Единый ответ для главного экрана админки."""
    from ..repo import billing, growth
    return {
        "overview": await repo.overview(db),
        "funnel": await repo.funnel(db, days),
        "activation": await repo.activation_funnel(db, days),
        "timeseries": await repo.timeseries(db, days),
        "retention": await repo.retention(db),
        "top_events": await repo.top_events(db, days=7),
        "surfaces": await repo.surface_split(db, days),
        "sources": await repo.source_split(db, days),
        "revenue": await billing.revenue(db, days=days),
        "top_products": await billing.top_products(db, days=days),
        "top_referrers": await growth.top_referrers(db, limit=10),
        "promo_batches": await growth.batch_stats(db),
        # себестоимость рядом с выручкой: маржа должна быть видна одним взглядом
        "llm_costs": await repo.llm_costs(db, days=days),
        "monetization": await repo.monetization_kpis(db, days=days),
    }


async def rollup(db, day: str | None = None) -> dict:
    return await repo.rollup_day(db, day)
