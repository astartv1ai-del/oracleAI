"""Слой данных: DDL, миграции, подключение.

Разделение ответственности:
- `schema.py`     — полный DDL (единственный источник правды по структуре);
- `migrations.py` — пошаговые изменения для уже живых баз;
- `session.py`    — подключение, PRAGMA, применение схемы и миграций.

Репозитории (`app/repo/`) — единственные, кто пишет SQL поверх этого слоя.
"""
from .session import connect, healthcheck, utcnow  # noqa: F401

__all__ = ["connect", "healthcheck", "utcnow"]
