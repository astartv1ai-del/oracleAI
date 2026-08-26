"""Report history must preserve prior deterministic/report snapshots."""
from __future__ import annotations

import aiosqlite
import pytest

from app.repo import readings


@pytest.mark.asyncio
async def test_report_versions_are_append_only(db):
    first_id = await readings.save_report(
        db, 1001, "natal", "Первый отчёт", "old body", period=None,
        meta={"snapshot": "old"})
    second_id = await readings.save_report(
        db, 1001, "natal", "Второй отчёт", "new body", period=None,
        meta={"snapshot": "new"})

    assert second_id > first_id
    row = await readings.get_report(db, 1001, "natal")
    assert row["id"] == second_id
    assert row["body"] == "new body"

    cur = await db.execute(
        "SELECT id, body, meta_json FROM reports "
        "WHERE tg_id=? AND kind=? ORDER BY id", (1001, "natal"))
    rows = await cur.fetchall()
    assert [(row["id"], row["body"]) for row in rows] == [
        (first_id, "old body"), (second_id, "new body")
    ]
    assert '"snapshot": "old"' in rows[0]["meta_json"]

    assert await readings.get_report_by_id(db, 1001, "natal", first_id)
    assert await readings.get_report_by_id(db, 1002, "natal", first_id) is None
    assert await readings.get_report_by_id(db, 1001, "matrix", first_id) is None


@pytest.mark.asyncio
async def test_legacy_unique_reports_migrate_without_losing_history(tmp_path):
    path = str(tmp_path / "legacy.db")
    raw = await aiosqlite.connect(path)
    await raw.execute(
        "CREATE TABLE reports ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, tg_id INTEGER NOT NULL, "
        "kind TEXT NOT NULL, period TEXT, title TEXT, body TEXT, "
        "meta_json TEXT, created_at TEXT, UNIQUE (tg_id, kind, period))"
    )
    await raw.execute(
        "INSERT INTO reports(tg_id, kind, title, body, created_at) "
        "VALUES(?,?,?,?,?)", (1001, "natal", "Legacy", "legacy body", "2026-01-01")
    )
    await raw.commit()
    await raw.close()

    from app.data.session import connect

    migrated = await connect(path)
    try:
        second_id = await readings.save_report(
            migrated, 1001, "natal", "Regenerated", "new body",
            meta={"snapshot": "new"})
        cur = await migrated.execute(
            "SELECT body FROM reports WHERE tg_id=? AND kind=? ORDER BY id",
            (1001, "natal"))
        rows = await cur.fetchall()
        assert [row["body"] for row in rows] == ["legacy body", "new body"]
        assert second_id > 1

        latest = await readings.get_report(migrated, 1001, "natal")
        assert latest["body"] == "new body"
    finally:
        await migrated.close()
