"""Слой данных: схема, миграции, сид, транзакции."""
from __future__ import annotations

import asyncio

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


async def test_ensure_race_double_start_creates_user_once(db):
    """Двойной /start в один момент не должен валить UNIQUE по tg_id.

    Оба вызова успевают пройти SELECT до INSERT; INSERT OR IGNORE + rowcount
    дают одного пользователя и один welcome в журнале.
    """
    await asyncio.gather(
        users.ensure(db, 777, "Первый"),
        users.ensure(db, 777, "Второй"),
    )
    fresh = await users.get(db, 777)
    assert fresh is not None, "пользователь не создан"
    assert fresh["name"] in ("Первый", "Второй")
    cur = await db.execute(
        "SELECT COUNT(*) c FROM crystal_ledger WHERE tg_id=? AND reason='welcome'",
        (777,))
    assert (await cur.fetchone())["c"] == 1, "welcome начислен дважды"


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


async def test_recall_caches_repeated_query(db, monkeypatch):
    """Тот же вопрос в пределах окна не считает семантику заново (G15)."""
    from app.core import memory

    await users.ensure(db, 1001, "А")
    calls = []

    async def fake_semantic(db_, tg, q, limit):
        calls.append(q)
        return ["Факт про работу"]

    monkeypatch.setattr(memory, "_semantic", fake_semantic)
    r1 = await memory.recall(db, 1001, "Расскажи про работу", limit=5)
    r2 = await memory.recall(db, 1001, "расскажи про работу", limit=5)

    assert calls == ["Расскажи про работу"], "второй запрос должен прийти из кеша"
    assert r1 == r2


async def test_recall_uses_bounded_embedding_pool(db, monkeypatch):
    """Семантика сканирует окно кандидатов, а не всю историю; на 400 фактах
    результат всё равно корректный (G15)."""
    import hashlib

    from app.core import memory

    await users.ensure(db, 1001, "А")

    def _vec(text: str) -> list[float]:
        # Детерминированный, но различимый вектор на текст: иначе все факты
        # с одинаковым вектором склеились бы дедупликацией в один.
        h = hashlib.sha256(text.encode()).digest()
        return [(h[i % 32] / 255.0) * 2 - 1 for i in range(16)]

    async def fake_embed(texts):
        return [_vec(t) for t in texts]

    monkeypatch.setattr(memory, "embed", fake_embed)
    monkeypatch.setattr(memory, "embeddings_enabled", lambda: True)
    monkeypatch.setattr(memory, "RELEVANCE_FLOOR", -1.0)
    for i in range(400):
        await memory.remember(db, 1001, f"Факт номер {i}")

    facts = await memory.recall(db, 1001, "что-нибудь", limit=8)
    assert len(facts) == 8, "recall должен собрать окно из 400 фактов"
    assert all("Факт" in f for f in facts)


async def test_anonymize_keeps_row_but_clears_pii(db, user):
    await dialog.add_diary(db, user["tg_id"], "личная запись")
    await users.anonymize(db, user["tg_id"])
    fresh = await users.get(db, user["tg_id"])
    assert fresh is not None, "строка нужна для сводимости платежей"
    assert fresh["birth_date"] is None
    assert fresh["status"] == "deleted"
    assert await dialog.get_diary(db, user["tg_id"]) == []


async def test_g13_missing_indexes_exist(db):
    """Индексы под горячие выборки (G13): оплата по заказу, промо, рефералы,
    DAU/WAU по событиям, учёт LLM."""
    cur = await db.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in await cur.fetchall()}
    for required in (
        "idx_pay_order", "idx_promo_red", "idx_ref_invitee",
        "idx_events_created", "idx_usage_created",
        "idx_msg_user", "idx_msg_thread", "idx_msg_user_id",
        "idx_msg_user_thread_id", "idx_msg_user_question_id",
        "idx_thread_user", "idx_thread_user_agent", "idx_thread_user_recent",
    ):
        assert required in indexes, required


async def test_overview_dau_wau_on_day(db):
    """DAU/WAU/MAU считаются по events.day (денормализация, G13)."""
    from datetime import datetime, timedelta, timezone

    from app.repo.analytics import overview

    today = (datetime.now(timezone.utc)).date().isoformat()
    far = (datetime.now(timezone.utc) - timedelta(days=40)).date().isoformat()
    await db.executemany(
        "INSERT INTO events(tg_id, name, day, created_at) VALUES(?,?,?,?)",
        [(7001, "question", today, f"{today}T09:00:00+00:00"),
         (7001, "question", far, f"{far}T09:00:00+00:00"),
         (7002, "question", far, f"{far}T09:00:00+00:00")])
    await db.commit()

    stats = await overview(db)
    assert stats["dau"] == 1, "вчера+сегодня активна только 7001"
    assert stats["wau"] == 1
    assert stats["mau"] == 1, "40 дней назад — за пределами окна MAU"
