"""Слой данных: схема, миграции, сид, транзакции."""
from __future__ import annotations

import aiosqlite
import pytest

from app.data import migrations
from app.data.schema import SCHEMA
from app.data.session import connect, healthcheck, transaction
from app.repo import content, dialog, users

# Схема прошлой версии продукта: на такой базе стоит живой бот, и миграция
# обязана довести её до актуальной без потери данных.
LEGACY_SCHEMA = """
CREATE TABLE users (
    tg_id INTEGER PRIMARY KEY, name TEXT, persona TEXT DEFAULT 'friend',
    oracle_name TEXT DEFAULT 'Лилит', tz TEXT DEFAULT 'Europe/Moscow',
    birth_date TEXT, birth_time TEXT, birth_time_known INTEGER DEFAULT 1,
    birth_city TEXT, birth_lat REAL, birth_lon REAL, chart_json TEXT,
    sub_level TEXT DEFAULT 'vip', sub_until TEXT, crystals INTEGER DEFAULT 0,
    onboarded INTEGER DEFAULT 0, created_at TEXT, ref_by INTEGER
);
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT, tg_id INTEGER, role TEXT, text TEXT,
    is_question INTEGER DEFAULT 0, created_at TEXT
);
CREATE TABLE promo_codes (
    code TEXT PRIMARY KEY, days INTEGER DEFAULT 30, batch TEXT,
    used_by INTEGER, used_at TEXT
);
"""


async def test_fresh_database_has_full_schema(db):
    state = await healthcheck(db)
    assert state["ok"]
    assert state["journal_mode"].lower() == "wal"
    cur = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in await cur.fetchall()}
    for required in ("users", "messages", "threads", "orders", "payments",
                     "entitlements", "events", "settings", "content_items",
                     "feature_flags", "admins", "broadcasts", "deliveries",
                     "reports", "referrals", "promo_redemptions"):
        assert required in tables, required


async def test_seed_fills_catalog(db):
    from app.repo import billing
    plans = await billing.list_plans(db)
    assert any(p["code"] == "vip" for p in plans)
    products = await billing.list_products(db)
    assert any(p["sku"] == "spread_celtic" for p in products)
    # одиночные расклады обязаны продаваться — это отдельное требование продукта
    assert any(p["kind"] == "spread" for p in products)
    assert await content.get_setting(db, "referral.bonus") == 15
    assert await content.get_text(db, "guide", "tarot")


async def test_seed_is_idempotent_and_keeps_edits(db):
    from app.data.seed import seed_defaults
    from app.repo import billing
    await billing.upsert_plan(db, "vip", price_stars=999, title="Мой VIP")
    await seed_defaults(db)
    plan = await billing.get_plan(db, "vip")
    assert plan["price_stars"] == 999, "повторный сид перезаписал правки админа"
    assert plan["title"] == "Мой VIP"


async def test_legacy_database_is_migrated(tmp_path):
    """Главная проверка миграции: боевая база старой версии + данные в ней."""
    path = tmp_path / "legacy.db"
    raw = await aiosqlite.connect(str(path))
    await raw.executescript(LEGACY_SCHEMA)
    await raw.execute(
        "INSERT INTO users(tg_id, name, sub_until, crystals, onboarded, created_at, "
        "ref_by) VALUES(500, 'Старая', '2030-01-01T00:00:00+00:00', 40, 1, "
        "'2026-01-01T00:00:00+00:00', 501)")
    await raw.execute(
        "INSERT INTO users(tg_id, name, created_at) VALUES(501, 'Пригласившая', "
        "'2026-01-01T00:00:00+00:00')")
    await raw.execute(
        "INSERT INTO promo_codes(code, days, batch, used_by, used_at) "
        "VALUES('OLD1', 30, 'etsy-1', 500, '2026-01-02T00:00:00+00:00')")
    await raw.execute("PRAGMA user_version=7")
    await raw.commit()
    await raw.close()

    db = await connect(str(path))
    try:
        legacy = await users.get(db, 500)
        assert legacy["name"] == "Старая"
        assert legacy["crystals"] == 40, "миграция потеряла данные"
        # новые колонки появились
        assert legacy["status"] == "active"
        assert legacy["ltv_stars"] == 0
        # ref_by перенесён в таблицу referrals
        cur = await db.execute(
            "SELECT referrer_id FROM referrals WHERE invitee_id=500 AND level=1")
        assert (await cur.fetchone())["referrer_id"] == 501
        # промокод получил счётчик активаций и запись о применении
        cur = await db.execute("SELECT used_count FROM promo_codes WHERE code='OLD1'")
        assert (await cur.fetchone())["used_count"] == 1
        cur = await db.execute("SELECT tg_id FROM promo_redemptions WHERE code='OLD1'")
        assert (await cur.fetchone())["tg_id"] == 500
    finally:
        await db.close()


async def test_migration_runs_twice_without_error(tmp_path):
    path = str(tmp_path / "twice.db")
    first = await connect(path)
    await first.close()
    second = await connect(path)          # повторный старт сервиса
    try:
        added = await migrations.reconcile_columns(second)
        assert added == [], "вторая миграция снова добавляет колонки"
        applied = await migrations.apply_data_migrations(second)
        assert applied == []
    finally:
        await second.close()


async def test_schema_script_is_valid_sql(tmp_path):
    raw = await aiosqlite.connect(str(tmp_path / "schema.db"))
    try:
        await raw.executescript(SCHEMA)     # упадёт при опечатке в DDL
    finally:
        await raw.close()


async def test_transaction_rolls_back_on_error(db, user):
    with pytest.raises(RuntimeError):
        async with transaction(db):
            await db.execute("UPDATE users SET crystals=999 WHERE tg_id=?",
                             (user["tg_id"],))
            raise RuntimeError("сбой посреди операции")
    fresh = await users.get(db, user["tg_id"])
    assert fresh["crystals"] != 999, "откат транзакции не сработал"


async def test_update_user_rejects_unknown_column(db, user):
    with pytest.raises(ValueError):
        await users.update(db, user["tg_id"], nonexistent_field=1)


async def test_memory_deduplicates(db, user):
    assert await dialog.save_memory(db, user["tg_id"], "Работает дизайнером")
    assert not await dialog.save_memory(db, user["tg_id"], "работает дизайнером  ")
    facts = await dialog.get_memories(db, user["tg_id"])
    assert facts.count("Работает дизайнером") == 1
    rows = await dialog.memories_full(db, user["tg_id"])
    assert rows[0]["weight"] == 2, "повтор должен усиливать важность факта"


async def test_anonymize_keeps_row_but_clears_pii(db, user):
    await dialog.add_diary(db, user["tg_id"], "личная запись")
    await users.anonymize(db, user["tg_id"])
    fresh = await users.get(db, user["tg_id"])
    assert fresh is not None, "строка нужна для сводимости платежей"
    assert fresh["birth_date"] is None
    assert fresh["status"] == "deleted"
    assert await dialog.get_diary(db, user["tg_id"]) == []
