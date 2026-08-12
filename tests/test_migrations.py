"""Миграции: сериализация на старте (G11).

Бот и API — два процесса, стартующие одновременно. Если оба видят одну и ту же
пропавшую колонку и оба идут в ALTER TABLE, второй ловит `database is locked`.
BEGIN IMMEDIATE в reconcile_columns берёт блокировку записи заранее: конкурент
ждёт в busy_timeout и после первого коммита видит колонки на месте.
"""
from __future__ import annotations

import asyncio

import aiosqlite

from app.data import migrations as mig


async def test_concurrent_reconcile_columns_no_lock_error(tmp_path):
    """Два процесса на одном файле мигрируют без «database is locked»."""
    path = str(tmp_path / "old.db")
    raw = await aiosqlite.connect(path)
    # Старая схема: users без большинства колонок — reconcile добавит их.
    await raw.execute("CREATE TABLE users (tg_id INTEGER PRIMARY KEY, name TEXT)")
    await raw.commit()
    await raw.close()

    conn1 = await aiosqlite.connect(path)
    conn2 = await aiosqlite.connect(path)
    for c in (conn1, conn2):
        c.row_factory = aiosqlite.Row
        await c.execute("PRAGMA journal_mode=WAL")
        await c.execute("PRAGMA busy_timeout=5000")
    try:
        added1, added2 = await asyncio.gather(
            mig.reconcile_columns(conn1),
            mig.reconcile_columns(conn2),
        )
    finally:
        await conn1.close()
        await conn2.close()

    # Никто не поймал «database is locked»; работу сделал ровно один процесс,
    # второй увидел колонки уже добавленными и не стал ничего менять.
    assert (added1 and not added2) or (not added1 and added2), \
        "миграцию должен выполнить ровно один из двух процессов"
    assert len(added1) + len(added2) == len(mig.COLUMNS["users"]), \
        "колонки добавлены за один проход, без двойной работы"
    assert "users.gender" in {*added1, *added2}
