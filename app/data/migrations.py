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
  таблицей в `schema.py`; редкое изменение ключа существующей таблицы требует
  отдельной именованной миграции с атомарным пересозданием таблицы.
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
        "gender": "TEXT DEFAULT NULL",
        "morning_push": "INTEGER DEFAULT 1",
        "memory_enabled": "INTEGER DEFAULT 0",
        "age_confirmed": "INTEGER DEFAULT 0",
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
        "lang": "TEXT DEFAULT 'ru'",   # язык текста прогноза (ru|en)
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
    "broadcast_targets": {
        "claimed_at": "TEXT",
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
    """Добивает отсутствующие колонки. Возвращает список добавленного.

    Весь проход — в одном `BEGIN IMMEDIATE`. Бот и API стартуют как два
    процесса и могут начать миграцию одновременно: оба прочитали бы
    `PRAGMA table_info`, оба увидели бы пропавшую колонку и оба пошли в ALTER —
    второй поймал бы `database is locked`. BEGIN IMMEDIATE берёт блокировку
    записи заранее; конкурент держится в busy_timeout и после первого коммита
    видит колонки на месте.
    """
    added: list[str] = []
    await db.execute("BEGIN IMMEDIATE")
    try:
        for table, columns in COLUMNS.items():
            if not await _table_exists(db, table):
                continue  # таблицу создаст schema.py — там колонки уже полные
            present = await _existing_columns(db, table)
            for name, definition in columns.items():
                if name in present:
                    continue
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
                added.append(f"{table}.{name}")
    except Exception:
        await db.rollback()
        raise
    await db.commit()
    if added:
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


async def _m_forecasts_language_key(db) -> None:
    """Делает язык частью ключа прогнозов без потери ранее созданного кэша.

    До v80 строка `(tg_id, day)` была единственной: английский прогноз заменял
    русский и наоборот. SQLite не умеет расширять PRIMARY KEY через ALTER,
    поэтому переносим таблицу внутри одной write-транзакции. Повторный запуск
    безопасен: в новой схеме миграция сразу завершится.
    """
    cur = await db.execute("PRAGMA table_info(forecasts)")
    columns = await cur.fetchall()
    primary_key = [row[1] for row in sorted(columns, key=lambda row: row[5])
                   if row[5]]
    if primary_key == ["tg_id", "day", "lang"]:
        return

    await db.execute("BEGIN IMMEDIATE")
    try:
        await db.execute("DROP TABLE IF EXISTS forecasts_v81")
        await db.execute(
            "CREATE TABLE forecasts_v81 ("
            "tg_id INTEGER, day TEXT, text TEXT, lang TEXT DEFAULT 'ru', "
            "audio_file_id TEXT, created_at TEXT, "
            "PRIMARY KEY (tg_id, day, lang))")
        await db.execute(
            "INSERT INTO forecasts_v81(tg_id, day, text, lang, audio_file_id, created_at) "
            "SELECT tg_id, day, text, COALESCE(NULLIF(lang, ''), 'ru'), "
            "audio_file_id, created_at FROM forecasts")
        await db.execute("DROP TABLE forecasts")
        await db.execute("ALTER TABLE forecasts_v81 RENAME TO forecasts")
    except Exception:
        await db.rollback()
        raise
    await db.commit()


async def _m_legacy_messages_to_default_threads(db) -> int:
    """Мягко переносит старые сообщения в активный дефолтный тред пользователя.

    Legacy-сообщения создавались до сессионной модели и имеют ``thread_id IS NULL``.
    Для каждого существующего пользователя переиспользуем его активный oracle-тред
    или создаём один с понятным названием. Orphan-строки без users пропускаем.

    Savepoint нужен потому, что apply_data_migrations может выполнять несколько
    data-migrations в одной внешней транзакции: частичный перенос нельзя оставлять,
    если один из SQL-шагов завершился ошибкой.
    """
    savepoint = "legacy_messages_to_default_threads"
    await db.execute(f"SAVEPOINT {savepoint}")
    moved = 0
    try:
        cur = await db.execute(
            "SELECT tg_id FROM messages "
            "WHERE thread_id IS NULL AND tg_id IS NOT NULL GROUP BY tg_id")
        legacy_users = [row[0] for row in await cur.fetchall()]

        for tg_id in legacy_users:
            cur = await db.execute("SELECT 1 FROM users WHERE tg_id=?", (tg_id,))
            if await cur.fetchone() is None:
                continue

            cur = await db.execute(
                "SELECT id FROM threads WHERE tg_id=? AND agent='oracle' "
                "AND archived=0 ORDER BY id DESC LIMIT 1", (tg_id,))
            thread = await cur.fetchone()
            if thread:
                thread_id = thread[0]
            else:
                now = utcnow_str()
                cur = await db.execute(
                    "INSERT INTO threads(tg_id, agent, title, msg_count, "
                    "created_at, last_at) VALUES(?,?,?,?,?,?)",
                    (tg_id, "oracle", "Личный Оракул", 0, now, now),
                )
                thread_id = cur.lastrowid

            cur = await db.execute(
                "SELECT COUNT(*) FROM messages "
                "WHERE tg_id=? AND thread_id IS NULL", (tg_id,))
            pending = (await cur.fetchone())[0]
            if not pending:
                continue

            await db.execute(
                "UPDATE messages SET thread_id=? "
                "WHERE tg_id=? AND thread_id IS NULL", (thread_id, tg_id))
            moved += pending

            await db.execute(
                "UPDATE threads SET "
                "msg_count=(SELECT COUNT(*) FROM messages WHERE thread_id=?), "
                "last_text=(SELECT text FROM messages WHERE thread_id=? "
                "ORDER BY id DESC LIMIT 1), "
                "last_at=(SELECT created_at FROM messages WHERE thread_id=? "
                "ORDER BY id DESC LIMIT 1), "
                "title=COALESCE(NULLIF(title, ''), 'Личный Оракул') "
                "WHERE id=?",
                (thread_id, thread_id, thread_id, thread_id),
            )

        await db.execute(f"RELEASE SAVEPOINT {savepoint}")
        if moved:
            log.info("legacy messages migrated to default threads: %d", moved)
        return moved
    except Exception:
        await db.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        await db.execute(f"RELEASE SAVEPOINT {savepoint}")
        raise


async def _m_reports_append_only(db) -> None:
    """Preserve regenerated reports as history instead of replacing old rows.

    The legacy table had ``UNIQUE (tg_id, kind, period)`` and ``INSERT OR
    REPLACE`` therefore deleted the previous calculation/report snapshot. A
    table rebuild is required because SQLite cannot drop an inline constraint.
    The migration is idempotent: a table without that unique index is already
    on the new contract.
    """
    cur = await db.execute("PRAGMA index_list(reports)")
    indexes = await cur.fetchall()
    unique_report_index = False
    for index in indexes:
        if not index[2]:
            continue
        name = index[1]
        info_cur = await db.execute(f"PRAGMA index_info([{name}])")
        columns = [row[2] for row in await info_cur.fetchall()]
        if columns == ["tg_id", "kind", "period"]:
            unique_report_index = True
            break
    if not unique_report_index:
        return

    await db.execute("BEGIN IMMEDIATE")
    try:
        await db.execute("DROP TABLE IF EXISTS reports_v82")
        await db.execute(
            "CREATE TABLE reports_v82 ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "tg_id INTEGER NOT NULL, kind TEXT NOT NULL, period TEXT, "
            "title TEXT, body TEXT, meta_json TEXT, created_at TEXT)"
        )
        await db.execute(
            "INSERT INTO reports_v82(id, tg_id, kind, period, title, body, meta_json, created_at) "
            "SELECT id, tg_id, kind, period, title, body, meta_json, created_at FROM reports"
        )
        await db.execute("DROP TABLE reports")
        await db.execute("ALTER TABLE reports_v82 RENAME TO reports")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(tg_id, kind)")
    except Exception:
        await db.rollback()
        raise
    await db.commit()


async def _m_memory_explicit_opt_in(db) -> None:
    """Reset legacy implicit memory state until users explicitly opt in again.

    Older installations used DEFAULT 1 and have no consent timestamp, so a
    privacy-safe migration cannot distinguish explicit consent from a default.
    Existing users must opt in again rather than silently retaining context.
    """
    await db.execute(
        "UPDATE users SET memory_enabled=0 "
        "WHERE COALESCE(memory_enabled, 0) <> 0")


# (имя, функция). Имя навсегда — по нему стоит отметка о применении.
DATA_MIGRATIONS: list[tuple[str, object]] = [
    ("2026_07_referrals_from_ref_by", _m_referrals_from_ref_by),
    ("2026_07_promo_used_count", _m_promo_used_count),
    ("2026_07_reading_spread_from_question", _m_reading_spread_from_question),
    ("2026_07_events_day_backfill", _m_events_day_backfill),
    ("2026_07_users_sub_level_codes", _m_users_sub_level_codes),
    ("2026_08_forecasts_language_key", _m_forecasts_language_key),
    ("2026_08_legacy_messages_to_default_threads", _m_legacy_messages_to_default_threads),
    ("2026_08_reports_append_only", _m_reports_append_only),
    ("2026_08_memory_explicit_opt_in", _m_memory_explicit_opt_in),
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
