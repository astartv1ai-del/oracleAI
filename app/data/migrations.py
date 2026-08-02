"""Миграции живой базы.

Две независимые механики, потому что они решают разные задачи:

1. **Сверка колонок** (`COLUMNS` + `reconcile_columns`). `CREATE TABLE IF NOT EXISTS`
   из `schema.py` создаёт таблицу целиком, но НИЧЕГО не делает с уже существующей.
   База, созданная прошлой версией кода, останется без новых колонок. Поэтому мы
   декларируем добавленные колонки и добиваем их через `ALTER TABLE ADD COLUMN`,
   сверяясь с `PRAGMA table_info`. Работает одинаково на пустой и на боевой базе,
   переживает любое число повторных запусков и не требует знать «версию» БД —
   что важно, потому что нумерация версий у старого кода своя (`PRAGMA
   user_version` дошёл до 7) и совпадать с нашей не обязана.

2. **Именованные миграции данных** (`DATA_MIGRATIONS`). Перекладывание данных
   (например, `users.ref_by` → таблица `referrals`) выполняется один раз;
   отметка об этом лежит в `migrations_applied`. Имена, а не номера: две ветки
   разработки могут добавить свою миграцию, не конфликтуя за номер.

Ограничения SQLite, которые формируют правила игры:
- `ADD COLUMN` умеет только константный DEFAULT — никаких `CURRENT_TIMESTAMP`;
- `ADD COLUMN` не умеет UNIQUE/PRIMARY KEY: такие поля вводятся только новой
  таблицей в `schema.py` (для существующих — через пересоздание, которого мы
  пока сознательно избегаем).
"""
from __future__ import annotations

import logging

log = logging.getLogger("oracle.migrations")

# ─────────────────── 1. колонки, добавленные после первой версии ───────────────
# {таблица: {колонка: определение}}. Определение — тип + константный DEFAULT.
COLUMNS: dict[str, dict[str, str]] = {
    "users": {
        "username": "TEXT",
        "lang": "TEXT DEFAULT 'ru'",
        "morning_push": "INTEGER DEFAULT 1",
        "ref_by": "INTEGER",
        "goal": "TEXT",
        "source": "TEXT",
        "status": "TEXT DEFAULT 'active'",
        "ltv_stars": "INTEGER DEFAULT 0",
        "expiry_notified": "INTEGER DEFAULT 0",
        "last_seen": "TEXT",
        "deleted_at": "TEXT",
    },
    "messages": {
        "thread_id": "INTEGER",
        "agent": "TEXT DEFAULT 'oracle'",
        "surface": "TEXT DEFAULT 'bot'",
        "tokens": "INTEGER",
    },
    "memories": {
        "weight": "INTEGER DEFAULT 1",
        "embedding": "BLOB",
        "embed_model": "TEXT",
        "last_used": "TEXT",
    },
    "forecasts": {
        "audio_file_id": "TEXT",       # file_id озвучки в Telegram (переиспользуем)
    },
    "diary": {
        "mood": "TEXT",
    },
    "tarot_readings": {
        "spread": "TEXT",
        "surface": "TEXT DEFAULT 'bot'",
        "paid_with": "TEXT",
        "outcome": "TEXT",
        "outcome_at": "TEXT",
    },
    "promo_codes": {
        "kind": "TEXT DEFAULT 'plan_days'",
        "plan_code": "TEXT DEFAULT 'vip'",
        "crystals": "INTEGER DEFAULT 0",
        "sku": "TEXT",
        "max_uses": "INTEGER DEFAULT 1",
        "used_count": "INTEGER DEFAULT 0",
        "expires_at": "TEXT",
        "created_by": "INTEGER",
        "created_at": "TEXT",
    },
    "crystal_ledger": {
        "balance": "INTEGER",
        "ref": "TEXT",
    },
    "plans": {
        "price_usd": "REAL DEFAULT 0",
        "weekly_questions": "INTEGER DEFAULT 0",
        "memory_depth": "INTEGER DEFAULT 20",
        "badge": "TEXT",
    },
}


async def _existing_columns(db, table: str) -> set[str]:
    cur = await db.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in await cur.fetchall()}


async def _table_exists(db, table: str) -> bool:
    cur = await db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return await cur.fetchone() is not None


async def reconcile_columns(db) -> list[str]:
    """Добивает отсутствующие колонки. Возвращает список добавленного."""
    added: list[str] = []
    for table, columns in COLUMNS.items():
        if not await _table_exists(db, table):
            continue  # таблицу создаст schema.py — там колонки уже полные
        present = await _existing_columns(db, table)
        for name, definition in columns.items():
            if name in present:
                continue
            await db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
            added.append(f"{table}.{name}")
    if added:
        await db.commit()
        log.info("миграция: добавлены колонки %s", ", ".join(added))
    return added


# ─────────────────────── 2. именованные миграции данных ───────────────────────

async def _m_referrals_from_ref_by(db) -> None:
    """Старая рефералка жила одной колонкой `users.ref_by` — переносим в таблицу
    `referrals`, где у приглашения есть уровень, бонус и время."""
    await db.execute(
        "INSERT OR IGNORE INTO referrals(referrer_id, invitee_id, level, bonus, created_at) "
        "SELECT ref_by, tg_id, 1, 0, COALESCE(created_at, ?) FROM users "
        "WHERE ref_by IS NOT NULL AND ref_by <> 0",
        (utcnow_str(),),
    )


async def _m_promo_used_count(db) -> None:
    """`used_by IS NOT NULL` в старой схеме означал «код активирован один раз»."""
    await db.execute(
        "UPDATE promo_codes SET used_count=1 "
        "WHERE used_by IS NOT NULL AND COALESCE(used_count, 0) = 0")
    await db.execute("UPDATE promo_codes SET max_uses=1 WHERE COALESCE(max_uses,0) = 0")
    await db.execute(
        "INSERT OR IGNORE INTO promo_redemptions(code, tg_id, created_at) "
        "SELECT code, used_by, COALESCE(used_at, ?) FROM promo_codes "
        "WHERE used_by IS NOT NULL",
        (utcnow_str(),),
    )


async def _m_reading_spread_from_question(db) -> None:
    """Раньше расклад определялся по тексту вопроса («Расклад «...»»).
    Проставляем код расклада там, где он однозначно вычисляется."""
    mapping = {
        "Одна карта": "one",
        "Прошлое · Настоящее · Будущее": "three",
        "На отношения": "love",
    }
    for title, code in mapping.items():
        await db.execute(
            "UPDATE tarot_readings SET spread=? WHERE spread IS NULL AND question=?",
            (code, f"Расклад «{title}»"))


async def _m_events_day_backfill(db) -> None:
    """`events.day` — денормализация для быстрых группировок в аналитике."""
    await db.execute(
        "UPDATE events SET day=substr(created_at,1,10) "
        "WHERE day IS NULL AND created_at IS NOT NULL")


async def _m_users_sub_level_codes(db) -> None:
    """Старый дефолт `sub_level='vip'` ставился всем, включая триальных.
    Приводим к кодам тарифов: живой триал — `trial`, истёкшие — `free`."""
    await db.execute(
        "UPDATE users SET sub_level='free' "
        "WHERE (sub_until IS NULL OR sub_until < ?) AND sub_level IN ('vip','trial')",
        (utcnow_str(),))


# (имя, функция). Имя навсегда — по нему стоит отметка о применении.
DATA_MIGRATIONS: list[tuple[str, object]] = [
    ("2026_07_referrals_from_ref_by", _m_referrals_from_ref_by),
    ("2026_07_promo_used_count", _m_promo_used_count),
    ("2026_07_reading_spread_from_question", _m_reading_spread_from_question),
    ("2026_07_events_day_backfill", _m_events_day_backfill),
    ("2026_07_users_sub_level_codes", _m_users_sub_level_codes),
]

TRACKER = """
CREATE TABLE IF NOT EXISTS migrations_applied (
    name       TEXT PRIMARY KEY,
    applied_at TEXT
);
"""


def utcnow_str() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


async def apply_data_migrations(db) -> list[str]:
    """Выполняет неприменённые миграции данных. Возвращает список выполненных."""
    await db.executescript(TRACKER)
    cur = await db.execute("SELECT name FROM migrations_applied")
    done = {r[0] for r in await cur.fetchall()}
    applied: list[str] = []
    for name, fn in DATA_MIGRATIONS:
        if name in done:
            continue
        try:
            await fn(db)
        except Exception as e:  # noqa: BLE001
            # Миграция данных не должна валить старт сервиса: продукт работает и
            # без перенесённой истории, а падение здесь означало бы, что бот не
            # поднимется вообще. Отметку не ставим — попробуем на следующем старте.
            log.error("миграция %s не выполнена: %s", name, e)
            continue
        await db.execute(
            "INSERT OR REPLACE INTO migrations_applied(name, applied_at) VALUES(?,?)",
            (name, utcnow_str()))
        applied.append(name)
    if applied:
        await db.commit()
        log.info("миграция данных: %s", ", ".join(applied))
    return applied
