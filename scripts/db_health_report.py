"""Read-only SQLite health report for scale triggers and restore drills."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from app.config import settings

AGGREGATE_TABLES = (
    "users", "messages", "threads", "diary", "orders", "events", "llm_usage",
)


def _scalar(conn: sqlite3.Connection, pragma: str):
    return conn.execute(f"PRAGMA {pragma}").fetchone()[0]


def collect(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2.0) as conn:
        conn.row_factory = sqlite3.Row
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        tables = {
            table: int(conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()[0])
            for table in AGGREGATE_TABLES
        }
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table, exists in tables.items() if exists
        }
        return {
            "db_name": path.name,
            "db_bytes": path.stat().st_size,
            "wal_bytes": path.with_name(path.name + "-wal").stat().st_size
            if path.with_name(path.name + "-wal").exists() else 0,
            "shm_bytes": path.with_name(path.name + "-shm").stat().st_size
            if path.with_name(path.name + "-shm").exists() else 0,
            "journal_mode": str(_scalar(conn, "journal_mode")),
            "page_size": int(_scalar(conn, "page_size")),
            "page_count": int(_scalar(conn, "page_count")),
            "freelist_count": int(_scalar(conn, "freelist_count")),
            "user_version": int(_scalar(conn, "user_version")),
            "integrity_check": integrity,
            "aggregate_counts": counts,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=settings.db_path, type=Path)
    parser.add_argument("--max-db-mb", type=float, default=2048)
    parser.add_argument("--max-wal-mb", type=float, default=256)
    args = parser.parse_args()
    report = collect(args.db)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["integrity_check"] != "ok":
        return 2
    if report["db_bytes"] > args.max_db_mb * 1024 * 1024:
        return 3
    if report["wal_bytes"] > args.max_wal_mb * 1024 * 1024:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
