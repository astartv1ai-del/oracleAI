"""Подключение к БД: PRAGMA, применение схемы, миграции, транзакции.

Почему WAL и busy_timeout обязательны. Бот и API — два процесса, которые пишут в
один файл SQLite. В журнальном режиме по умолчанию (`delete`) писатель блокирует
читателей, и второй процесс получает `database is locked` на живом трафике.
WAL разводит читателей и писателя, а `busy_timeout` заставляет ждать вместо
мгновенной ошибки, когда писатели всё же сталкиваются.

Почему нужен `transaction()`. Внутри процесса соединение одно на всё приложение,
а корутин много. `sqlite3` открывает неявную транзакцию на первом DML и закрывает
её на `commit()` — значит, любая другая корутина, вызвавшая `commit()` посреди
нашей последовательности запросов, зафиксирует нашу работу наполовину. Для
денежных операций это недопустимо, поэтому пишущие сценарии заворачиваются в
`transaction()`: он сериализует запись через asyncio-лок и делает
commit/rollback целиком.
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import aiosqlite

from ..config import settings
from . import migrations as mig
from .schema import INDEXES, TABLES

log = logging.getLogger("oracle.db")

# Ждать освободившуюся блокировку до 15 секунд: столько заведомо хватает на любую
# нашу запись, а падать с «database is locked» на пользовательском запросе нельзя.
def _env_int(name: str, default: int, *, minimum: int = 1) -> int:
    try:
        return max(int(os.getenv(name, str(default))), minimum)
    except (TypeError, ValueError):
        return default


BUSY_TIMEOUT_MS = _env_int("SQLITE_BUSY_TIMEOUT_MS", 15_000)
WAL_AUTOCHECKPOINT = _env_int("SQLITE_WAL_AUTOCHECKPOINT", 2_000)
CACHE_SIZE_KB = _env_int("SQLITE_CACHE_SIZE_KB", 16_000)

PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",      # с WAL этого достаточно: потеря только при отказе ОС
    f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}",
    "PRAGMA foreign_keys=ON",
    "PRAGMA temp_store=MEMORY",
    f"PRAGMA wal_autocheckpoint={WAL_AUTOCHECKPOINT}",
    f"PRAGMA cache_size=-{CACHE_SIZE_KB}",
)

_LOCK_ATTR = "_oracle_write_lock"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def connect(path: str | None = None, *, seed: bool = True):
    """Открывает PostgreSQL из DATABASE_URL или SQLite при явном path/fallback."""
    if path is None and settings.database_url:
        from .pg_schema import POSTGRES_BOOTSTRAP, POSTGRES_INDEXES, POSTGRES_TABLES
        from .postgres import PostgresDatabase

        db = PostgresDatabase(settings.database_url)
        await db.executescript(POSTGRES_BOOTSTRAP)
        await db.executescript(POSTGRES_TABLES)
        await db.executescript(POSTGRES_INDEXES)
        await mig.apply_postgres_data_migrations(db)
        if seed:
            from .seed import seed_defaults
            async with db.transaction():
                await seed_defaults(db)
        return db

    db = await aiosqlite.connect(path or settings.db_path)
    db.row_factory = aiosqlite.Row
    for pragma in PRAGMAS:
        await db.execute(pragma)

    # Порядок важен: таблицы → недостающие колонки → индексы. Индекс по колонке,
    # которой ещё нет в старой базе, иначе валит старт (`no such column`).
    await db.executescript(TABLES)
    await mig.reconcile_columns(db)
    await db.executescript(INDEXES)
    await mig.apply_data_migrations(db)
    await db.execute("PRAGMA optimize")
    await db.commit()

    if seed:
        from .seed import seed_defaults
        await seed_defaults(db)

    setattr(db, _LOCK_ATTR, asyncio.Lock())
    return db


def _lock(db) -> asyncio.Lock:
    lock = getattr(db, _LOCK_ATTR, None)
    if lock is None:                      # соединение открыли не через connect()
        lock = asyncio.Lock()
        setattr(db, _LOCK_ATTR, lock)
    return lock


@asynccontextmanager
async def transaction(db):
    """Атомарный пишущий блок. Внутри НЕ вызывать db.commit().

    Вложенные вызовы из той же задачи не открывают свою транзакцию — выполняются
    внутри внешней. Это нужно сервисам (деньги: оплата→выдача одним коммитом),
    которые оборачивают несколько repo-операций, каждая из которых открывает свою
    `transaction()`. Владельца храним задачей, а не флагом: иначе параллельная
    задача увидела бы «уже внутри» и вклинилась бы в чужую транзакцию.
    """
    if getattr(db, "is_postgres", False):
        async with db.transaction():
            yield db
        return

    owner = getattr(db, "_in_txn", None)
    if owner is asyncio.current_task():
        yield db
        return
    async with _lock(db):
        setattr(db, "_in_txn", asyncio.current_task())
        try:
            yield db
        except BaseException:
            # CancelledError — это BaseException, а не Exception: отменённая на
            # шатдауне задача иначе оставила бы соединение в открытой транзакции,
            # и частичная запись ушла бы в базу следующим чужим commit().
            await db.rollback()
            raise
        else:
            await db.commit()
        finally:
            setattr(db, "_in_txn", None)


async def healthcheck(db) -> dict:
    """Состояние БД для /health и админки."""
    if getattr(db, "is_postgres", False):
        return await db.healthcheck()
    async def scalar(sql: str, *args):
        cur = await db.execute(sql, args)
        row = await cur.fetchone()
        return row[0] if row else None

    integrity = await scalar("PRAGMA quick_check")
    return {
        "ok": integrity == "ok",
        "integrity": integrity,
        "journal_mode": await scalar("PRAGMA journal_mode"),
        "page_count": await scalar("PRAGMA page_count"),
        "users": await scalar("SELECT COUNT(*) FROM users"),
        "schema_tables": await scalar(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"),
    }
