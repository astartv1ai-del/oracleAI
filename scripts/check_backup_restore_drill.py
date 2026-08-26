#!/usr/bin/env python3
"""Exercise a disposable SQLite backup/restore drill with synthetic data."""
from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.data.session import connect  # noqa: E402
from app.repo import readings, users  # noqa: E402


async def seed_database(path: Path) -> None:
    db = await connect(str(path), seed=False)
    try:
        await users.ensure(db, 14001, "Synthetic owner")
        await users.ensure(db, 14002, "Synthetic other")
        await readings.save_report(db, 14001, "natal", "Owner report", "owner-private-body")
        await readings.save_report(db, 14002, "natal", "Other report", "other-private-body")
    finally:
        await db.close()


def scalar(db: sqlite3.Connection, sql: str, args: tuple = ()):
    return db.execute(sql, args).fetchone()[0]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="oracleai-backup-drill-") as tmp:
        root = Path(tmp)
        source = root / "source.db"
        snapshot = root / "snapshot.db"
        restored = root / "restored.db"
        asyncio.run(seed_database(source))

        source_db = sqlite3.connect(source)
        backup_db = sqlite3.connect(snapshot)
        source_db.backup(backup_db)
        backup_db.close()
        source_db.close()

        snap_db = sqlite3.connect(snapshot)
        integrity = scalar(snap_db, "PRAGMA integrity_check")
        owner_count = scalar(snap_db, "SELECT COUNT(*) FROM reports WHERE tg_id=14001")
        other_count = scalar(snap_db, "SELECT COUNT(*) FROM reports WHERE tg_id=14002")
        snap_db.close()

        restored_db = sqlite3.connect(restored)
        sqlite3.connect(snapshot).backup(restored_db)
        restored_integrity = scalar(restored_db, "PRAGMA integrity_check")
        owner_body = scalar(restored_db, "SELECT body FROM reports WHERE tg_id=14001")
        other_body = scalar(restored_db, "SELECT body FROM reports WHERE tg_id=14002")
        isolation = owner_body == "owner-private-body" and other_body == "other-private-body"
        restored_db.close()

        result = {
            "synthetic": True,
            "integrity_check": integrity,
            "restored_integrity_check": restored_integrity,
            "owner_report_count": owner_count,
            "other_report_count": other_count,
            "owner_isolation": isolation,
            "pass": integrity == "ok" and restored_integrity == "ok" and owner_count == 1 and other_count == 1 and isolation,
            "note": "This is a disposable local drill; production storage permissions, encryption key custody and rollback rehearsal remain external gates.",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
