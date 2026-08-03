"""Liveness-чек бота для docker-compose.

Бот не поднимает HTTP — постучать в него нельзя напрямую. Доверяем хартбиту:
планировщик бота пишет `settings.system.heartbeat` каждый тик. Метка протухла —
процесс жив, а цикл мёртв, пусть Docker перезапустит контейнер.

Никаких зависимостей: только stdlib sqlite3, чтобы чек работал в любом образе.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

DB = os.getenv("DB_PATH") or os.path.join(os.getenv("DATA_DIR", "data"), "oracle.db")
STALE_S = float(os.getenv("HEARTBEAT_STALE_S", "1800"))   # 3 × тик по 10 минут


def main() -> int:
    try:
        # read-only: чек не должен конкурировать за write-замок с ботом
        db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)
    except sqlite3.Error:
        return 1
    row = db.execute(
        "SELECT value_json FROM settings WHERE key='system.heartbeat'").fetchone()
    if not row or not row[0]:
        return 1                                  # хартбита ещё нет — бот не дошёл до тика
    try:
        stamp = json.loads(row[0])
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(stamp)).total_seconds()
    except (ValueError, TypeError, json.JSONDecodeError):
        return 1
    return 0 if age <= STALE_S else 1


if __name__ == "__main__":
    sys.exit(main())
