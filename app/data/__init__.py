"""Слой данных: DDL, подключение.

Разделение ответственности:
- `schema.py`     — полный DDL (единственный источник правды по структуре);
- `pg_schema.py`  — пострельский рендер схемы;
- `postgres.py`   — PostgreSQL-адаптер репозиторного DB-протокола;
- `session.py`    — подключение, применение схемы и транзакции.

Репозитории (`app/repo/`) — единственные, кто пишет SQL поверх этого слоя.
"""
from .session import connect, healthcheck, utcnow  # noqa: F401

__all__ = ["connect", "healthcheck", "utcnow"]
