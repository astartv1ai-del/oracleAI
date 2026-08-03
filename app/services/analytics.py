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
    }


async def rollup(db, day: str | None = None) -> dict:
    return await repo.rollup_day(db, day)
