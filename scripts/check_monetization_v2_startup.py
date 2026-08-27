from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.data.session import connect


async def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = await connect(str(Path(directory) / "startup.db"), seed=False)
        from app.data.seed import _seed_monetization_v2
        await _seed_monetization_v2(db)
        await db.commit()
        for table in ("catalog_versions", "price_book_items", "subscription_state", "monetization_usage", "crystal_lots", "monetization_assignments"):
            cur = await db.execute(f"SELECT COUNT(*) FROM {table}")
            print(table, (await cur.fetchone())[0])
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
