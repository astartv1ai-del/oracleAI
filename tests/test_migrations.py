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


async def test_legacy_messages_move_to_default_threads_idempotently(tmp_path):
    """Legacy NULL-сообщения привязываются к oracle-треду ровно один раз."""
    from app.data.session import connect

    path = str(tmp_path / "legacy_messages.db")
    raw = await aiosqlite.connect(path)
    await raw.executescript(
        """
        CREATE TABLE users (
            tg_id INTEGER PRIMARY KEY,
            name TEXT,
            username TEXT,
            lang TEXT DEFAULT 'ru',
            gender TEXT,
            persona TEXT DEFAULT 'friend',
            oracle_name TEXT DEFAULT 'Лилит',
            tz TEXT DEFAULT 'Europe/Moscow',
            birth_date TEXT,
            birth_time TEXT,
            birth_time_known INTEGER DEFAULT 1,
            birth_city TEXT,
            birth_lat REAL,
            birth_lon REAL,
            chart_json TEXT,
            sub_level TEXT DEFAULT 'trial',
            sub_until TEXT,
            crystals INTEGER DEFAULT 0,
            onboarded INTEGER DEFAULT 0,
            morning_push INTEGER DEFAULT 1,
            memory_enabled INTEGER DEFAULT 1,
            age_confirmed INTEGER DEFAULT 0,
            ref_by INTEGER,
            goal TEXT,
            source TEXT,
            status TEXT DEFAULT 'active',
            ltv_stars INTEGER DEFAULT 0,
            expiry_notified INTEGER DEFAULT 0,
            last_seen TEXT,
            deleted_at TEXT,
            created_at TEXT
        );
        CREATE TABLE threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL,
            agent TEXT NOT NULL DEFAULT 'oracle',
            title TEXT,
            msg_count INTEGER DEFAULT 0,
            last_text TEXT,
            last_at TEXT,
            archived INTEGER DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL,
            thread_id INTEGER,
            agent TEXT DEFAULT 'oracle',
            role TEXT,
            text TEXT,
            is_question INTEGER DEFAULT 0,
            created_at TEXT
        );
        INSERT INTO users(tg_id, name, created_at)
            VALUES (700, 'Есть тред', '2026-01-01T00:00:00+00:00'),
                   (701, 'Без треда', '2026-01-01T00:00:00+00:00');
        INSERT INTO threads(tg_id, agent, title, msg_count, created_at, last_at)
            VALUES (700, 'oracle', 'Существующий чат', 0,
                    '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00');
        INSERT INTO messages(tg_id, thread_id, agent, role, text, is_question, created_at)
            VALUES (700, NULL, 'oracle', 'user', 'Старый вопрос', 1,
                    '2025-12-01T10:00:00+00:00'),
                   (700, NULL, 'oracle', 'assistant', 'Старый ответ', 0,
                    '2025-12-01T10:00:01+00:00'),
                   (701, NULL, 'oracle', 'user', 'Ещё старый вопрос', 1,
                    '2025-12-02T10:00:00+00:00'),
                   (999, NULL, 'oracle', 'user', 'Orphan message', 1,
                    '2025-12-03T10:00:00+00:00');
        """)
    await raw.commit()
    await raw.close()

    db = await connect(path, seed=False)
    try:
        cur = await db.execute(
            "SELECT id, title, msg_count, last_text, last_at FROM threads "
            "WHERE tg_id=700 AND agent='oracle' AND archived=0")
        existing = await cur.fetchone()
        assert existing["title"] == "Существующий чат"
        assert existing["msg_count"] == 2
        assert existing["last_text"] == "Старый ответ"
        assert existing["last_at"] == "2025-12-01T10:00:01+00:00"

        cur = await db.execute(
            "SELECT id, agent, title, msg_count FROM threads "
            "WHERE tg_id=701 AND agent='oracle' AND archived=0")
        created = await cur.fetchone()
        assert created["title"] == "Личный Оракул"
        assert created["msg_count"] == 1

        cur = await db.execute(
            "SELECT COUNT(*) c FROM messages WHERE tg_id IN (700, 701) "
            "AND thread_id IS NULL")
        assert (await cur.fetchone())["c"] == 0
        cur = await db.execute(
            "SELECT COUNT(*) c FROM messages WHERE tg_id=999 AND thread_id IS NULL")
        assert (await cur.fetchone())["c"] == 1, "orphan нельзя приписывать пользователю"

        cur = await db.execute(
            "SELECT COUNT(*) c FROM migrations_applied "
            "WHERE name='2026_08_legacy_messages_to_default_threads'")
        assert (await cur.fetchone())["c"] == 1

        assert await mig.apply_data_migrations(db) == []
        cur = await db.execute(
            "SELECT COUNT(*) c FROM threads WHERE tg_id=701 AND agent='oracle'")
        assert (await cur.fetchone())["c"] == 1, "повторный старт создал дубль треда"
    finally:
        await db.close()


async def test_failed_data_migration_rolls_back_partial_writes(tmp_path, monkeypatch):
    """A failed migration must not leak DML into a later startup commit."""
    from app.data import schema

    path = str(tmp_path / "failed_migration.db")
    db = await aiosqlite.connect(path)
    try:
        await db.executescript(schema.TABLES)
        await db.execute("CREATE TABLE migration_probe (value TEXT)")
        await db.commit()

        async def failing_migration(connection):
            await connection.execute("INSERT INTO migration_probe(value) VALUES('leak')")
            raise RuntimeError("synthetic migration failure")

        monkeypatch.setattr(mig, "DATA_MIGRATIONS", [("synthetic_failure", failing_migration)])
        assert await mig.apply_data_migrations(db) == []

        row = await (await db.execute("SELECT COUNT(*) FROM migration_probe")).fetchone()
        assert row[0] == 0
        marker = await (
            await db.execute(
                "SELECT COUNT(*) FROM migrations_applied WHERE name='synthetic_failure'"
            )
        ).fetchone()
        assert marker[0] == 0
    finally:
        await db.close()


async def test_concurrent_legacy_message_migration_is_single_owner(tmp_path):
    """Два стартующих процесса не дублируют тред и не делят перенос пополам."""
    from app.data.schema import INDEXES, TABLES

    path = str(tmp_path / "legacy_messages_concurrent.db")
    raw = await aiosqlite.connect(path)
    await raw.executescript(TABLES)
    await raw.executescript(INDEXES)
    await raw.execute(
        "INSERT INTO users(tg_id, name) VALUES (703, 'Concurrent')")
    await raw.executemany(
        "INSERT INTO messages(tg_id, thread_id, agent, role, text, created_at) "
        "VALUES(?, NULL, 'oracle', ?, ?, ?)",
        [(703, "user", "Первый", "2026-01-01"),
         (703, "assistant", "Второй", "2026-01-02")],
    )
    await raw.commit()
    await raw.close()

    conn1 = await aiosqlite.connect(path)
    conn2 = await aiosqlite.connect(path)
    for conn in (conn1, conn2):
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA busy_timeout=5000")
    try:
        applied1, applied2 = await asyncio.gather(
            mig.apply_data_migrations(conn1),
            mig.apply_data_migrations(conn2),
        )
        assert (
            "2026_08_legacy_messages_to_default_threads" in applied1
            or "2026_08_legacy_messages_to_default_threads" in applied2
        )
        cur = await conn1.execute(
            "SELECT COUNT(*) c FROM messages WHERE tg_id=703 AND thread_id IS NULL")
        assert (await cur.fetchone())["c"] == 0
        cur = await conn1.execute(
            "SELECT COUNT(*) c FROM threads WHERE tg_id=703 AND agent='oracle'")
        assert (await cur.fetchone())["c"] == 1
        cur = await conn1.execute(
            "SELECT COUNT(*) c FROM migrations_applied "
            "WHERE name='2026_08_legacy_messages_to_default_threads'")
        assert (await cur.fetchone())["c"] == 1
    finally:
        await conn1.close()
        await conn2.close()
