from __future__ import annotations

import os

import pytest

from pathlib import Path

from app.data.postgres import PostgresDatabase, _split_script, _translate_sql

BASELINE_SQL = (
    Path(__file__).resolve().parents[1] / "alembic" / "schema" / "baseline.sql"
).read_text(encoding="utf-8")


def test_postgres_sql_translation_handles_ignore_and_placeholders():
    sql, names = _translate_sql(
        "INSERT OR IGNORE INTO users(tg_id, name) VALUES(?, ?)")
    assert sql == (
        "INSERT INTO users(tg_id, name) VALUES(:p0, :p1) "
        "ON CONFLICT DO NOTHING")
    assert names == ["p0", "p1"]


def test_postgres_schema_uses_native_numeric_type():
    assert " REAL " not in BASELINE_SQL
    assert "DOUBLE PRECISION" in BASELINE_SQL


def test_postgres_baseline_has_no_sqlite_types():
    # The SQLite derivation pipeline (schema.py + pg_schema.py) is removed.
    # The canonical Alembic baseline must speak native PostgreSQL DDL.
    forbidden = ("AUTOINCREMENT", "INTEGER PRIMARY KEY AUTOINCREMENT", " BLOB")
    for token in forbidden:
        assert token not in BASELINE_SQL, f"legacy SQLite token leaked: {token!r}"


def test_postgres_script_split_ignores_comment_and_literal_semicolons():
    script = "CREATE TABLE x (note TEXT DEFAULT 'a;b'); -- comment;\nCREATE TABLE y (id INTEGER);"
    assert _split_script(script) == [
        "CREATE TABLE x (note TEXT DEFAULT 'a;b')", 
        "-- comment;\nCREATE TABLE y (id INTEGER)",
    ]


@pytest.mark.asyncio
async def test_live_postgres_adapter_smoke():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    db = PostgresDatabase(url)
    try:
        async with db.transaction():
            await db.execute(
                "CREATE TEMP TABLE messages (id BIGSERIAL PRIMARY KEY, name TEXT)")
            cur = await db.execute("INSERT INTO messages(name) VALUES(?)", ("ok",))
            assert cur.lastrowid == 1
            cur = await db.execute("SELECT id, name FROM messages WHERE id=?", (1,))
            row = await cur.fetchone()
            assert dict(row) == {"id": 1, "name": "ok"}
    finally:
        await db.close()
