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
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import aiosqlite

from ..config import settings
from . import migrations as mig
from .schema import INDEXES, TABLES

log = logging.getLogger("oracle.db")

# Ждать освободившуюся блокировку до 15 секунд: столько заведомо хватает на любую
# нашу запись, а падать с «database is locked» на пользовательском запросе нельзя.
BUSY_TIMEOUT_MS = 15_000

PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",      # с WAL этого достаточно: потеря только при отказе ОС
    f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}",
    "PRAGMA foreign_keys=ON",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA cache_size=-16000",       # ~16 МБ страничного кеша
)

_LOCK_ATTR = "_oracle_write_lock"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def connect(path: str | None = None, *, seed: bool = True) -> aiosqlite.Connection:
    """Открывает соединение, приводит БД к актуальной структуре и отдаёт её."""
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
    """Атомарный пишущий блок. Внутри НЕ вызывать db.commit()."""
    async with _lock(db):
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
        await db.commit()


async def healthcheck(db) -> dict:
    """Состояние БД для /health и админки."""
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
