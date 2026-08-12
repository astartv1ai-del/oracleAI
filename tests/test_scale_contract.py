from __future__ import annotations

import sqlite3

from scripts.db_health_report import collect as collect_health
from scripts.migration_manifest import collect as collect_manifest


def _make_db(path):
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA user_version=7;
            CREATE TABLE users (id INTEGER PRIMARY KEY, tg_id INTEGER);
            CREATE TABLE messages (id INTEGER PRIMARY KEY, text TEXT);
            CREATE INDEX messages_id_idx ON messages(id);
            INSERT INTO users(tg_id) VALUES (1001);
            INSERT INTO messages(text) VALUES ('synthetic fixture');
            """
        )


def test_db_health_report_is_aggregate_and_integrity_checked(tmp_path):
    path = tmp_path / "oracle.db"
    _make_db(path)
    report = collect_health(path)
    assert report["integrity_check"] == "ok"
    assert report["journal_mode"] == "wal"
    assert report["aggregate_counts"] == {"users": 1, "messages": 1}
    assert "text" not in report


def test_migration_manifest_is_deterministic_and_data_free(tmp_path):
    path = tmp_path / "oracle.db"
    _make_db(path)
    first = collect_manifest(path)
    second = collect_manifest(path)
    assert first == second
    assert first["user_version"] == 7
    assert first["schema_sha256"]
    assert "synthetic fixture" not in str(first)
