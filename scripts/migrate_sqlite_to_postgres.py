"""Migrate a SQLite snapshot into PostgreSQL without mutating the source.

Usage:
  python -m scripts.migrate_sqlite_to_postgres \
    --sqlite data/oracle.db \
    --database-url postgresql+asyncpg://user:pass@host/db
"""
from __future__ import annotations

import argparse
import array
import asyncio
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.pg_schema import POSTGRES_BOOTSTRAP, POSTGRES_INDEXES, POSTGRES_TABLES
from app.data.postgres import PostgresDatabase


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _vector_literal(value):
    if value is None or isinstance(value, str):
        return value
    values = array.array("f")
    try:
        values.frombytes(bytes(value))
    except (TypeError, ValueError):
        return None
    return "[" + ",".join(format(item, ".9g") for item in values) + "]"


def _convert(table: str, column: str, value):
    if table == "memories" and column == "embedding":
        return _vector_literal(value)
    return value


def _source_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    return [row[0] for row in rows]


async def _target_columns(db: PostgresDatabase, table: str) -> set[str]:
    cur = await db.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=?", (table,))
    return {row[0] for row in await cur.fetchall()}


async def migrate(source_path: Path, database_url: str, batch_size: int) -> dict:
    source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    db = PostgresDatabase(database_url)
    counts: dict[str, int] = {}
    try:
        await db.executescript(POSTGRES_BOOTSTRAP)
        await db.executescript(POSTGRES_TABLES)
        await db.executescript(POSTGRES_INDEXES)
        async with db.transaction():
            for table in _source_tables(source):
                columns = [row[1] for row in source.execute(
                    f"PRAGMA table_info({_quote(table)})").fetchall()]
                columns = [name for name in columns if name in await _target_columns(db, table)]
                if not columns:
                    continue
                target = _quote(table)
                fields = ", ".join(_quote(name) for name in columns)
                placeholders = ", ".join("?" for _ in columns)
                sql = f"INSERT INTO {target} ({fields}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                rows = source.execute(
                    f"SELECT {fields} FROM {_quote(table)}").fetchall()
                count = 0
                for offset in range(0, len(rows), batch_size):
                    batch = [tuple(_convert(table, column, row[column])
                                   for column in columns)
                             for row in rows[offset:offset + batch_size]]
                    await db.executemany(sql, batch)
                    count += len(batch)
                counts[table] = count

            async def reset_sequences() -> None:
                for table in _source_tables(source):
                    if "id" not in await _target_columns(db, table):
                        continue
                    quoted = _quote(table)
                    await db.execute(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                        f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {quoted}")

            # Imported SQLite IDs are explicit; sync sequences before any backfill
            # that may create a new row, then once more after the backfill.
            await reset_sequences()
            from app.data.migrations import apply_postgres_data_migrations
            await apply_postgres_data_migrations(db)
            await reset_sequences()
        return counts
    finally:
        source.close()
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", required=True, type=Path)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--batch-size", type=int, default=1_000)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    counts = asyncio.run(migrate(args.sqlite, args.database_url, args.batch_size))
    print({"tables": len(counts), "rows": counts})


if __name__ == "__main__":
    main()
