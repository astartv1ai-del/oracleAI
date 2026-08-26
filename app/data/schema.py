"""Полный DDL проекта — единственный источник правды по структуре БД.

Все таблицы объявлены через `CREATE TABLE IF NOT EXISTS`, поэтому этот скрипт
безопасно выполняется при каждом старте: свежая база получает всю структуру,
живая — только новые таблицы. Изменения в УЖЕ существующих таблицах (ALTER)
живут в `migrations.py`, потому что IF NOT EXISTS их не покрывает.

SQL держим переносимым (без специфики SQLite сверх необходимого): при переезде
на PostgreSQL меняется только этот файл и тип автоинкремента.
"""
from __future__ import annotations

# ─────────────────────────────── пользователи ───────────────────────────────

USERS = """
CREATE TABLE IF NOT EXISTS users (
    tg_id            INTEGER PRIMARY KEY,
    name             TEXT,
    username         TEXT,
    lang             TEXT DEFAULT 'ru',
    gender           TEXT DEFAULT NULL,       -- f|m; NULL = нейтральные обращения
    persona          TEXT DEFAULT 'friend',
    oracle_name      TEXT DEFAULT 'Лилит',
    tz               TEXT DEFAULT 'Europe/Moscow',

    birth_date       TEXT,
    birth_time       TEXT,
    birth_time_known INTEGER DEFAULT 1,
    birth_city       TEXT,
    birth_lat        REAL,
    birth_lon        REAL,
    chart_json       TEXT,

    sub_level        TEXT DEFAULT 'trial',   -- код тарифа из plans
    sub_until        TEXT,
    crystals         INTEGER DEFAULT 0,

    onboarded        INTEGER DEFAULT 0,
    morning_push     INTEGER DEFAULT 1,
    memory_enabled   INTEGER DEFAULT 0,   -- память включается только явным согласием
    age_confirmed    INTEGER DEFAULT 0,   -- добровольное самоподтверждение «мне есть 16 лет»
    ref_by           INTEGER,
    goal             TEXT,                   -- главный запрос: love|career|practice
    source           TEXT,                   -- канал привлечения (utm/ref/organic)
    status           TEXT DEFAULT 'active',  -- active|blocked
    ltv_stars        INTEGER DEFAULT 0,      -- денормализация для CRM
    expiry_notified  INTEGER DEFAULT 0,
    last_seen        TEXT,
    deleted_at       TEXT,                   -- «удали мои данные»: анонимизация
    created_at       TEXT
);
"""

# ─────────────────────────── диалог, память, дневник ────────────────────────

DIALOG = """
CREATE TABLE IF NOT EXISTS threads (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id        INTEGER NOT NULL,
    agent        TEXT NOT NULL DEFAULT 'oracle',   -- код агента из core/agents
    title        TEXT,
    msg_count    INTEGER DEFAULT 0,
    last_text    TEXT,                             -- превью для списка чатов
    last_at      TEXT,
    archived     INTEGER DEFAULT 0,
    created_at   TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id       INTEGER NOT NULL,
    thread_id   INTEGER,                     -- NULL — исторические сообщения бота
    agent       TEXT DEFAULT 'oracle',
    role        TEXT,
    text        TEXT,
    is_question INTEGER DEFAULT 0,
    surface     TEXT DEFAULT 'bot',          -- bot|miniapp
    tokens      INTEGER,
    created_at  TEXT
);
CREATE TABLE IF NOT EXISTS memories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    fact       TEXT,
    kind       TEXT DEFAULT 'fact',
    weight     INTEGER DEFAULT 1,
    embedding  BLOB,                        -- float32-вектор для поиска по смыслу
    embed_model TEXT,                       -- какой моделью посчитан (миграция векторов)
    last_used  TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS profile_summaries (
    tg_id       INTEGER PRIMARY KEY,
    summary     TEXT,                       -- «кто она» одним абзацем для промпта
    facts_count INTEGER DEFAULT 0,          -- на скольких фактах собрана
    built_at    TEXT
);
CREATE TABLE IF NOT EXISTS diary (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    text       TEXT,
    mood       TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS forecasts (
    tg_id         INTEGER,
    day           TEXT,
    text          TEXT,
    lang          TEXT DEFAULT 'ru',     -- язык текста прогноза (ru|en)
    audio_file_id TEXT,                   -- озвучка прогноза: file_id Telegram
    created_at    TEXT,
    PRIMARY KEY (tg_id, day, lang)
);
CREATE TABLE IF NOT EXISTS reports (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    kind       TEXT NOT NULL,                -- natal|matrix|synastry|solar|monthly
    period     TEXT,                         -- YYYY-MM для месячных, год для соляра
    title      TEXT,
    body       TEXT,
    meta_json  TEXT,
    created_at TEXT
    -- Reports are immutable history entries. The latest row for a kind/period
    -- remains the cache; regeneration appends a new version.
);
CREATE TABLE IF NOT EXISTS deliveries (
    tg_id      INTEGER NOT NULL,
    kind       TEXT NOT NULL,                -- forecast|weekly|expiry|winback|broadcast
    key        TEXT NOT NULL,                -- день/идентификатор повода
    created_at TEXT,
    PRIMARY KEY (tg_id, kind, key)
);
"""

# ────────────────────────────── таро и практики ─────────────────────────────

READINGS = """
CREATE TABLE IF NOT EXISTS tarot_readings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    spread     TEXT,
    question   TEXT,
    cards_json TEXT,
    answer     TEXT,
    surface    TEXT DEFAULT 'bot',
    paid_with  TEXT,                          -- daily|crystals|stars|entitlement
    outcome    TEXT,                           -- came_true|partly|no (отметка клиентки)
    outcome_at TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS palm_readings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id         INTEGER NOT NULL,
    status        TEXT NOT NULL DEFAULT 'complete', -- complete|needs_photo|failed|deleted
    hand_side     TEXT,                              -- left|right|unknown
    image_sha256  TEXT,
    image_size    INTEGER,
    analysis_json TEXT,
    error_code    TEXT,
    surface       TEXT DEFAULT 'miniapp',
    created_at    TEXT,
    updated_at    TEXT,
    deleted_at    TEXT
);
CREATE TABLE IF NOT EXISTS partners (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    name       TEXT,
    relation   TEXT DEFAULT 'partner',        -- partner|crush|colleague|friend
    birth_date TEXT,
    birth_time TEXT,
    birth_city TEXT,
    birth_lat  REAL,
    birth_lon  REAL,
    tz         TEXT,
    chart_json TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS synastry_cache (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id         INTEGER NOT NULL,
    partner_key   TEXT NOT NULL,              -- дата/идентификатор партнёра
    score         INTEGER,
    breakdown_json TEXT,
    answer        TEXT,
    created_at    TEXT
);
CREATE TABLE IF NOT EXISTS practices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id       INTEGER NOT NULL,
    code        TEXT NOT NULL,                -- код практики из content_items
    day_index   INTEGER DEFAULT 0,
    streak      INTEGER DEFAULT 0,
    last_done   TEXT,
    started_at  TEXT,
    finished_at TEXT
);
"""

# ─────────────────────────── тарифы, заказы, платежи ────────────────────────

BILLING = """
CREATE TABLE IF NOT EXISTS plans (
    code             TEXT PRIMARY KEY,
    title            TEXT NOT NULL,
    tagline          TEXT,
    price_stars      INTEGER DEFAULT 0,
    price_usd        REAL DEFAULT 0,          -- витрина web-оплаты (Paddle)
    period_days      INTEGER DEFAULT 30,
    daily_questions  INTEGER DEFAULT 3,
    weekly_questions INTEGER DEFAULT 0,       -- для free-уровня «1 вопрос в неделю»
    memory_depth     INTEGER DEFAULT 20,      -- сколько фактов памяти в промпте
    crystals_grant   INTEGER DEFAULT 0,       -- бонус ✦ при покупке
    features_json    TEXT,                    -- список фич для витрины
    badge            TEXT,                    -- «выбор большинства» и т.п.
    sort             INTEGER DEFAULT 100,
    is_active        INTEGER DEFAULT 1,
    is_public        INTEGER DEFAULT 1,
    created_at       TEXT,
    updated_at       TEXT
);
CREATE TABLE IF NOT EXISTS products (
    sku            TEXT PRIMARY KEY,
    kind           TEXT NOT NULL,             -- spread|report|crystals|plan
    title          TEXT NOT NULL,
    description    TEXT,
    price_stars    INTEGER DEFAULT 0,
    price_crystals INTEGER DEFAULT 0,
    grant_kind     TEXT,                      -- что выдаём: spread|report|crystals|plan
    grant_code     TEXT,                      -- код расклада/отчёта/тарифа
    grant_qty      INTEGER DEFAULT 1,
    valid_days     INTEGER,                   -- срок жизни права (NULL — бессрочно)
    sort           INTEGER DEFAULT 100,
    is_active      INTEGER DEFAULT 1,
    created_at     TEXT,
    updated_at     TEXT
);
CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id          INTEGER NOT NULL,
    kind           TEXT NOT NULL,             -- plan|product|crystals
    sku            TEXT,
    title          TEXT,
    amount_stars   INTEGER DEFAULT 0,
    amount_crystals INTEGER DEFAULT 0,
    status         TEXT DEFAULT 'pending',    -- pending|paid|failed|refunded
    payload        TEXT UNIQUE,               -- invoice payload (идемпотентность)
    surface        TEXT DEFAULT 'bot',
    meta_json      TEXT,
    created_at     TEXT,
    paid_at        TEXT
);
CREATE TABLE IF NOT EXISTS payments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER,
    tg_id         INTEGER NOT NULL,
    amount_stars  INTEGER DEFAULT 0,
    currency      TEXT DEFAULT 'XTR',
    charge_id     TEXT,
    provider      TEXT DEFAULT 'telegram_stars',
    status        TEXT DEFAULT 'succeeded',   -- succeeded|refunded
    created_at    TEXT
);
CREATE TABLE IF NOT EXISTS entitlements (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    kind       TEXT NOT NULL,                 -- spread|report|question
    code       TEXT,                          -- конкретный расклад/отчёт ('*' — любой)
    qty_total  INTEGER DEFAULT 1,
    qty_used   INTEGER DEFAULT 0,
    expires_at TEXT,
    source     TEXT DEFAULT 'purchase',       -- purchase|promo|gift|referral|admin
    order_id   INTEGER,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS crystal_ledger (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    delta      INTEGER,
    reason     TEXT,
    balance    INTEGER,                       -- баланс после операции (аудит)
    ref        TEXT,
    created_at TEXT
);
"""

# ─────────────────────────── промокоды и рефералы ───────────────────────────

GROWTH = """
CREATE TABLE IF NOT EXISTS promo_codes (
    code       TEXT PRIMARY KEY,
    kind       TEXT DEFAULT 'plan_days',      -- plan_days|crystals|product
    days       INTEGER DEFAULT 30,
    plan_code  TEXT DEFAULT 'vip',
    crystals   INTEGER DEFAULT 0,
    sku        TEXT,
    batch      TEXT,
    max_uses   INTEGER DEFAULT 1,
    used_count INTEGER DEFAULT 0,
    expires_at TEXT,
    created_by INTEGER,
    created_at TEXT,
    used_by    INTEGER,                       -- legacy: первый активировавший
    used_at    TEXT
);
CREATE TABLE IF NOT EXISTS promo_redemptions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT NOT NULL,
    tg_id      INTEGER NOT NULL,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS referrals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    invitee_id  INTEGER NOT NULL,
    level       INTEGER DEFAULT 1,            -- 1 — подруга, 2 — подруга подруги
    bonus       INTEGER DEFAULT 0,
    created_at  TEXT,
    UNIQUE (referrer_id, invitee_id, level)
);
"""

# ──────────────── справочники и служебные кеши ──────────────────────────────

INFRA = """
CREATE TABLE IF NOT EXISTS geocache (
    city_key   TEXT PRIMARY KEY,            -- нормализованное название города
    lat        REAL,
    lon        REAL,
    tz         TEXT,
    source     TEXT,                        -- builtin|nominatim
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS horoscopes (
    day        TEXT NOT NULL,               -- YYYY-MM-DD
    sign       TEXT NOT NULL,               -- знак зодиака (рус.)
    text       TEXT,
    posted_at  TEXT,                        -- когда ушло в канал-спутник
    created_at TEXT,
    PRIMARY KEY (day, sign)
);
CREATE TABLE IF NOT EXISTS llm_usage (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id             INTEGER,
    provider          TEXT,
    model             TEXT,
    purpose           TEXT,                 -- answer|forecast|report|memory|horoscope
    prompt_tokens     INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    cost_usd          REAL DEFAULT 0,
    latency_ms        INTEGER DEFAULT 0,
    ok                INTEGER DEFAULT 1,
    day               TEXT,
    created_at        TEXT
);
CREATE TABLE IF NOT EXISTS safety_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER,
    category   TEXT,                        -- crisis|violence|medical|stop_topic
    excerpt    TEXT,
    action     TEXT,                        -- support|soften|blocked
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS scheduler_leases (
    name             TEXT PRIMARY KEY,
    owner            TEXT,
    acquired_at      TEXT,
    lease_until      TEXT,
    last_started_at  TEXT,
    last_finished_at TEXT,
    last_status      TEXT DEFAULT 'never', -- never|running|ok|error
    last_error       TEXT,
    run_count        INTEGER DEFAULT 0,
    failure_count    INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS webhook_events (
    event_id   TEXT PRIMARY KEY,            -- id от провайдера: ключ идемпотентности
    provider   TEXT,
    kind       TEXT,
    payload    TEXT,
    created_at TEXT
);
"""

ANALYTICS = """
CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER,
    name       TEXT NOT NULL,
    props_json TEXT,
    surface    TEXT DEFAULT 'bot',            -- bot|miniapp|admin|system
    day        TEXT,                          -- YYYY-MM-DD (UTC) для быстрых группировок
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS daily_stats (
    day        TEXT PRIMARY KEY,
    stats_json TEXT,
    updated_at TEXT
);
"""

# ──────────────── настройки, контент, фиче-флаги, админка, CRM ──────────────

ADMIN = """
CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value_json TEXT,
    updated_at TEXT,
    updated_by INTEGER
);
CREATE TABLE IF NOT EXISTS content_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT NOT NULL,                 -- persona|spread|practice|copy|faq
    code       TEXT NOT NULL,
    title      TEXT,
    body       TEXT,
    meta_json  TEXT,
    is_active  INTEGER DEFAULT 1,
    sort       INTEGER DEFAULT 100,
    updated_by INTEGER,
    updated_at TEXT,
    created_at TEXT,
    UNIQUE (kind, code)
);
CREATE TABLE IF NOT EXISTS feature_flags (
    code        TEXT PRIMARY KEY,
    is_on       INTEGER DEFAULT 0,
    rollout_pct INTEGER DEFAULT 100,
    description TEXT,
    updated_by  INTEGER,
    updated_at  TEXT
);
CREATE TABLE IF NOT EXISTS admins (
    tg_id      INTEGER PRIMARY KEY,
    role       TEXT DEFAULT 'admin',          -- owner|admin|support|analyst
    title      TEXT,
    added_by   INTEGER,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS admin_audit (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id     INTEGER,
    action       TEXT NOT NULL,
    target       TEXT,
    payload_json TEXT,
    created_at   TEXT
);
CREATE TABLE IF NOT EXISTS user_notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    author_id  INTEGER,
    text       TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS user_tags (
    tg_id      INTEGER NOT NULL,
    tag        TEXT NOT NULL,
    author_id  INTEGER,
    created_at TEXT,
    PRIMARY KEY (tg_id, tag)
);
CREATE TABLE IF NOT EXISTS broadcasts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT,
    body         TEXT,
    button_text  TEXT,
    button_url   TEXT,
    segment_json TEXT,
    status       TEXT DEFAULT 'draft',        -- draft|scheduled|running|done|cancelled
    total        INTEGER DEFAULT 0,
    sent         INTEGER DEFAULT 0,
    failed       INTEGER DEFAULT 0,
    scheduled_at TEXT,
    started_at   TEXT,
    finished_at  TEXT,
    created_by   INTEGER,
    created_at   TEXT
);
CREATE TABLE IF NOT EXISTS broadcast_targets (
    broadcast_id INTEGER NOT NULL,
    tg_id        INTEGER NOT NULL,
    status       TEXT DEFAULT 'pending',      -- pending|claiming|sent|failed|skipped
    error        TEXT,
    sent_at      TEXT,
    claimed_at   TEXT,                        -- момент захвата (G9: атомарный claim)
    PRIMARY KEY (broadcast_id, tg_id)
);
CREATE TABLE IF NOT EXISTS task_jobs (
    id           TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'queued', -- queued|running|succeeded|failed|retry
    tg_id        INTEGER,
    payload_json TEXT,
    result_json  TEXT,
    error        TEXT,
    attempts     INTEGER NOT NULL DEFAULT 0,
    available_at TEXT,
    started_at   TEXT,
    finished_at  TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
    """

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_msg_user            ON messages(tg_id, is_question, created_at);
CREATE INDEX IF NOT EXISTS idx_msg_created         ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_msg_thread          ON messages(thread_id, id);
CREATE INDEX IF NOT EXISTS idx_msg_user_id          ON messages(tg_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_msg_user_thread_id   ON messages(tg_id, thread_id, id);
CREATE INDEX IF NOT EXISTS idx_msg_user_question_id ON messages(tg_id, is_question, id DESC);
CREATE INDEX IF NOT EXISTS idx_thread_user         ON threads(tg_id, archived, last_at);
CREATE INDEX IF NOT EXISTS idx_thread_user_agent   ON threads(tg_id, agent, archived, id DESC);
CREATE INDEX IF NOT EXISTS idx_thread_user_recent  ON threads(
    tg_id, archived, COALESCE(last_at, created_at) DESC, id DESC
);
CREATE INDEX IF NOT EXISTS idx_reports_user  ON reports(tg_id, kind);
CREATE INDEX IF NOT EXISTS idx_mem_user        ON memories(tg_id);
CREATE INDEX IF NOT EXISTS idx_mem_user_rank   ON memories(tg_id, weight DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_diary_user      ON diary(tg_id, created_at);
CREATE INDEX IF NOT EXISTS idx_read_user     ON tarot_readings(tg_id, created_at);
CREATE INDEX IF NOT EXISTS idx_read_created  ON tarot_readings(created_at);
CREATE INDEX IF NOT EXISTS idx_palm_user     ON palm_readings(tg_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_name   ON events(name, day);
CREATE INDEX IF NOT EXISTS idx_events_user       ON events(tg_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_user_name  ON events(tg_id, name);
CREATE INDEX IF NOT EXISTS idx_events_day        ON events(day);
CREATE INDEX IF NOT EXISTS idx_task_jobs_status_available ON task_jobs(status, available_at);
CREATE INDEX IF NOT EXISTS idx_task_jobs_user_created ON task_jobs(tg_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_created_name
    ON events(created_at, name, tg_id);
CREATE INDEX IF NOT EXISTS idx_orders_user        ON orders(tg_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status_paid ON orders(status, paid_at);
CREATE INDEX IF NOT EXISTS idx_pay_created        ON payments(created_at);
CREATE INDEX IF NOT EXISTS idx_pay_status_created ON payments(status, created_at);
CREATE INDEX IF NOT EXISTS idx_ent_user      ON entitlements(tg_id, kind, code);
CREATE INDEX IF NOT EXISTS idx_ledger_user   ON crystal_ledger(tg_id, created_at);
CREATE INDEX IF NOT EXISTS idx_users_seen         ON users(last_seen);
CREATE INDEX IF NOT EXISTS idx_users_created      ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_created_source ON users(created_at, source);
CREATE INDEX IF NOT EXISTS idx_users_sub     ON users(sub_until);
CREATE INDEX IF NOT EXISTS idx_partners_user ON partners(tg_id);
CREATE INDEX IF NOT EXISTS idx_syn_user      ON synastry_cache(tg_id, partner_key);
CREATE INDEX IF NOT EXISTS idx_notes_user    ON user_notes(tg_id, created_at);
CREATE INDEX IF NOT EXISTS idx_ref_referrer  ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_ref_invitee   ON referrals(invitee_id, level);
CREATE INDEX IF NOT EXISTS idx_promo_batch   ON promo_codes(batch);
CREATE INDEX IF NOT EXISTS idx_promo_red     ON promo_redemptions(code, tg_id);
CREATE INDEX IF NOT EXISTS idx_promo_created  ON promo_redemptions(created_at);
CREATE INDEX IF NOT EXISTS idx_pay_order     ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_bt_status     ON broadcast_targets(broadcast_id, status);
CREATE INDEX IF NOT EXISTS idx_usage_day     ON llm_usage(day, purpose);
CREATE INDEX IF NOT EXISTS idx_usage_user    ON llm_usage(tg_id, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_created ON llm_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_safety_user   ON safety_events(tg_id, created_at);
CREATE INDEX IF NOT EXISTS idx_horo_day      ON horoscopes(day);
CREATE INDEX IF NOT EXISTS idx_practice_user ON practices(tg_id, code);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
"""

#: Только таблицы, без индексов. Разделение нужно из-за порядка на старой базе:
#: `CREATE TABLE IF NOT EXISTS` не добавляет колонки в уже существующую таблицу,
#: поэтому индекс по новой колонке (например, `messages.thread_id`) упадёт, если
#: строить его до `migrations.reconcile_columns`. Порядок: таблицы → колонки →
#: индексы (см. `session.connect`).
TABLES = "\n".join([USERS, DIALOG, READINGS, BILLING, GROWTH, INFRA,
                    ANALYTICS, ADMIN])

SCHEMA = "\n".join([TABLES, INDEXES])
