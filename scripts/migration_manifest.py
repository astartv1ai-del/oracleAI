"""Emit a deterministic, data-free SQLite schema manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings


def collect(path: Path) -> dict:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2.0) as conn:
        objects = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE type IN ('table', 'index', 'trigger', 'view') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY type, name"
        ).fetchall()
        schema = [
            {"type": str(kind), "name": str(name), "sql": " ".join((sql or "").split())}
            for kind, name, sql in objects
        ]
        payload = {
            "user_version": int(conn.execute("PRAGMA user_version").fetchone()[0]),
            "schema": schema,
        }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        **payload,
        "schema_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=settings.db_path, type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    current = collect(args.db)
    if args.compare:
        expected = json.loads(args.compare.read_text(encoding="utf-8"))
        current["matches_compare"] = current["schema_sha256"] == expected.get("schema_sha256")
        if not current["matches_compare"]:
            print(json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
    print(json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
