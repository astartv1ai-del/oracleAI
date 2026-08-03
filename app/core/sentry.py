"""Sentry (G31): опциональный мониторинг падений бота и API.

Пустой `SENTRY_DSN` — модуль молчит, продукт работает как раньше. С DSN оба
процесса отправляют необработанные исключения и долгие ответы. `capture_exception`
используется там, где исключение гасится ради пользовательского пути (например,
500-обёртка middleware), но не должно теряться для диагностики.
"""
from __future__ import annotations

import logging

log = logging.getLogger("oracle.sentry")

_initialized = False


def init() -> None:
    global _initialized
    if _initialized:
        return
    from ..config import settings
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
    except ImportError:
        log.warning("SENTRY_DSN задан, но sentry-sdk не установлен")
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.05,        # дашборд перфоманса без лишнего расхода
        send_default_pii=False,         # в события не тащим личные данные клиенток
        environment="production",
    )
    _initialized = True
    log.info("Sentry подключён")


def capture_exception(exc: BaseException) -> None:
    if not _initialized:
        return
    import sentry_sdk
    sentry_sdk.capture_exception(exc)
