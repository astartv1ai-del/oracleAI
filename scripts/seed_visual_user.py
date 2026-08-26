#!/usr/bin/env python3
"""Seed one disposable development user for local visual/E2E checks."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core import astro, tarot  # noqa: E402
from app.data.session import connect  # noqa: E402
from app.repo import dialog, readings, users  # noqa: E402


async def seed(path: str) -> None:
    db = await connect(path, seed=False)
    try:
        tg_id = 10001
        await users.ensure(db, tg_id, "Synthetic Oracle", "synthetic_oracle", lang="ru")
        chart = await astro.compute_chart_async(
            "1990-06-21", "14:30", "Казань", 55.79, 49.12,
            "Europe/Moscow", time_known=True)
        await users.update(
            db, tg_id, onboarded=1, age_confirmed=1, birth_date="1990-06-21",
            birth_time="14:30", birth_time_known=1, birth_city="Казань",
            birth_lat=55.79, birth_lon=49.12, tz="Europe/Moscow",
            chart_json=json.dumps(chart, ensure_ascii=False), memory_enabled=1,
            sub_level="vip")
        await dialog.save_memory(db, tg_id, "Любит тихие синтетические утра", kind="preference")
        await dialog.add_diary(db, tg_id, "Synthetic diary entry", mood="calm")
        cards = tarot.draw(3, seed="visual-baseline")
        await readings.save_reading(
            db, tg_id, "three", "Synthetic visual question", cards,
            "Synthetic reading answer")
    finally:
        await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    asyncio.run(seed(args.db))
    print(f"seeded synthetic visual user 10001 in {args.db}")
