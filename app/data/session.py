"""Подключение к БД: схема, сиды, транзакции.

Единственный бэкенд — PostgreSQL через `postgres.PostgresDatabase`. Схема и
индексы создаются при каждом старте (`IF NOT EXISTS`), структурные изменения
ведутся через alembic-миграции.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from ..config import settings

log = logging.getLogger("oracle.db")


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def connect(*, seed: bool = True):
    """Открывает PostgreSQL из DATABASE_URL и применяет схему."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL не задан")
    from .pg_schema import POSTGRES_BOOTSTRAP, POSTGRES_INDEXES, POSTGRES_TABLES
    from .postgres import PostgresDatabase

    db = PostgresDatabase(settings.database_url)
    await db.executescript(POSTGRES_BOOTSTRAP)
    await db.executescript(POSTGRES_TABLES)
    await db.executescript(POSTGRES_INDEXES)
    if seed:
        from .seed import seed_defaults
        async with db.transaction():
            await seed_defaults(db)
    return db


@asynccontextmanager
async def transaction(db):
    """Атомарный пишущий блок. Внутри НЕ вызывать db.commit().

    Вложенные вызовы из той же задачи выполняются внутри внешней транзакции —
    это нужно сервисам (деньги: оплата→выдача одним коммитом), которые
    оборачивают несколько repo-операций в свои `transaction()`.
    """
    async with db.transaction():
        yield db


async def healthcheck(db) -> dict:
    """Состояние БД для /health и админки."""
    return await db.healthcheck()
