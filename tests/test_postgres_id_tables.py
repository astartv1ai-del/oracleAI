"""Characterization tests: every table in _ID_TABLES returns a valid lastrowid.

These tests are a *characterization net* — they lock in the current shim
behaviour (RETURNING id injection by PostgresDatabase.execute) so that any
DB-001 refactor that breaks it is caught immediately.

Design rules:
  - Each parametrized case inserts the *minimal* row (only NOT NULL columns
    without a DEFAULT or with a DEFAULT that is sufficient).
  - No app/ code changes: the tests call PostgresDatabase.execute directly.
  - Tests must pass on the current master without touching app/.
  - For tables that have a UNIQUE constraint we use a per-test-run unique
    value (uuid4 suffix) to avoid conflicts across parallel / repeated runs.
  - For tables where a parent row is theoretically needed (FK in the app,
    not in DDL), none exists in this schema — PostgreSQL does not enforce FKs
    here, so we insert directly.

Reference: app/data/postgres.py  _ID_TABLES (31 tables).
"""
from __future__ import annotations

import uuid

import pytest

# ── helpers ───────────────────────────────────────────────────────────────────
_NOW = "2024-01-01T00:00:00+00:00"


def _uid() -> str:
    """Short unique suffix to avoid UNIQUE conflicts between test runs."""
    return uuid.uuid4().hex[:12]


# ── per-table INSERT specifications ──────────────────────────────────────────
# Each entry: (table_name, sql, params_factory)
# params_factory is a zero-arg callable → tuple, so unique values are fresh.

def _cases():  # noqa: C901 – intentionally long list
    u = _uid  # shortcut

    # 1. admin_audit — NOT NULL: action
    yield pytest.param(
        "admin_audit",
        "INSERT INTO admin_audit(action, created_at) VALUES(?,?)",
        lambda: ("test_action", _NOW),
        id="admin_audit",
    )

    # 2. broadcasts — no mandatory NOT NULL besides implicit NOT NULL PKs
    yield pytest.param(
        "broadcasts",
        "INSERT INTO broadcasts(title, created_at) VALUES(?,?)",
        lambda: (f"test_broadcast_{u()}", _NOW),
        id="broadcasts",
    )

    # 3. content_items — NOT NULL: kind, code; UNIQUE(kind, code)
    yield pytest.param(
        "content_items",
        "INSERT INTO content_items(kind, code, title, created_at, updated_at) "
        "VALUES(?,?,?,?,?)",
        lambda: ("test_kind", f"test_code_{u()}", "Test title", _NOW, _NOW),
        id="content_items",
    )

    # 4. crystal_ledger — all nullable
    yield pytest.param(
        "crystal_ledger",
        "INSERT INTO crystal_ledger(tg_id, delta, reason, balance, created_at) "
        "VALUES(?,?,?,?,?)",
        lambda: (99001, 10, "test", 10, _NOW),
        id="crystal_ledger",
    )

    # 5. crystal_lots — NOT NULL: tg_id, source, original_qty, remaining_qty, created_at
    yield pytest.param(
        "crystal_lots",
        "INSERT INTO crystal_lots(tg_id, source, original_qty, remaining_qty, created_at) "
        "VALUES(?,?,?,?,?)",
        lambda: (99001, "purchased", 100, 100, _NOW),
        id="crystal_lots",
    )

    # 6. diary — all nullable
    yield pytest.param(
        "diary",
        "INSERT INTO diary(tg_id, text, created_at) VALUES(?,?,?)",
        lambda: (99001, "diary entry", _NOW),
        id="diary",
    )

    # 7. entitlements — NOT NULL: tg_id, kind
    yield pytest.param(
        "entitlements",
        "INSERT INTO entitlements(tg_id, kind, code, created_at) VALUES(?,?,?,?)",
        lambda: (99001, "spread", "*", _NOW),
        id="entitlements",
    )

    # 8. events — NOT NULL: name
    yield pytest.param(
        "events",
        "INSERT INTO events(name, tg_id, created_at) VALUES(?,?,?)",
        lambda: ("test_event", 99001, _NOW),
        id="events",
    )

    # 9. llm_usage — all nullable/defaulted (tg_id nullable)
    yield pytest.param(
        "llm_usage",
        "INSERT INTO llm_usage(tg_id, provider, model, purpose, created_at) "
        "VALUES(?,?,?,?,?)",
        lambda: (99001, "test", "gpt-test", "answer", _NOW),
        id="llm_usage",
    )

    # 10. memories — all nullable
    yield pytest.param(
        "memories",
        "INSERT INTO memories(tg_id, fact, created_at) VALUES(?,?,?)",
        lambda: (99001, "test fact", _NOW),
        id="memories",
    )

    # 11. messages — all nullable
    yield pytest.param(
        "messages",
        "INSERT INTO messages(tg_id, role, text, created_at) VALUES(?,?,?,?)",
        lambda: (99001, "user", "hello", _NOW),
        id="messages",
    )

    # 12. monetization_usage — NOT NULL: tg_id, operation_key, capability,
    #     charged_source, status, created_at, updated_at; UNIQUE(tg_id, operation_key)
    yield pytest.param(
        "monetization_usage",
        "INSERT INTO monetization_usage("
        "tg_id, operation_key, capability, charged_source, status, created_at, updated_at"
        ") VALUES(?,?,?,?,?,?,?)",
        lambda: (99001, f"op_{u()}", "spread", "included", "reserved", _NOW, _NOW),
        id="monetization_usage",
    )

    # 13. orders — NOT NULL: tg_id, kind
    yield pytest.param(
        "orders",
        "INSERT INTO orders(tg_id, kind, created_at) VALUES(?,?,?)",
        lambda: (99001, "plan", _NOW),
        id="orders",
    )

    # 14. palm_readings — NOT NULL: tg_id, status DEFAULT 'complete' (so tg_id sufficient)
    yield pytest.param(
        "palm_readings",
        "INSERT INTO palm_readings(tg_id, created_at, updated_at) VALUES(?,?,?)",
        lambda: (99001, _NOW, _NOW),
        id="palm_readings",
    )

    # 15. partners — all nullable
    yield pytest.param(
        "partners",
        "INSERT INTO partners(tg_id, name, created_at) VALUES(?,?,?)",
        lambda: (99001, "partner_name", _NOW),
        id="partners",
    )

    # 16. payment_webhook_failures — NOT NULL: provider, code, created_at
    yield pytest.param(
        "payment_webhook_failures",
        "INSERT INTO payment_webhook_failures(provider, code, created_at) "
        "VALUES(?,?,?)",
        lambda: ("telegram", "test_code", _NOW),
        id="payment_webhook_failures",
    )

    # 17. payments — NOT NULL: tg_id
    yield pytest.param(
        "payments",
        "INSERT INTO payments(tg_id, amount_stars, created_at) VALUES(?,?,?)",
        lambda: (99001, 100, _NOW),
        id="payments",
    )

    # 18. practices — NOT NULL: tg_id, code
    yield pytest.param(
        "practices",
        "INSERT INTO practices(tg_id, code, started_at) VALUES(?,?,?)",
        lambda: (99001, f"prac_{u()}", _NOW),
        id="practices",
    )

    # 19. price_book_items — NOT NULL: catalog_version, price_book_version,
    #     item_type, code, title, channel, currency, effective_from, created_at
    #     UNIQUE(price_book_version, item_type, code, channel)
    yield pytest.param(
        "price_book_items",
        "INSERT INTO price_book_items("
        "catalog_version, price_book_version, item_type, code, title, "
        "channel, currency, effective_from, created_at"
        ") VALUES(?,?,?,?,?,?,?,?,?)",
        lambda: (
            "test_cat", f"pbv_{u()}", "plan", f"code_{u()}", "Test Plan",
            "stars", "XTR", _NOW, _NOW,
        ),
        id="price_book_items",
    )

    # 20. product_cost_events — NOT NULL: event_kind, sku, created_at
    yield pytest.param(
        "product_cost_events",
        "INSERT INTO product_cost_events(event_kind, sku, created_at) VALUES(?,?,?)",
        lambda: ("llm", f"sku_{u()}", _NOW),
        id="product_cost_events",
    )

    # 21. promo_redemptions — NOT NULL: code, tg_id
    yield pytest.param(
        "promo_redemptions",
        "INSERT INTO promo_redemptions(code, tg_id, created_at) VALUES(?,?,?)",
        lambda: (f"CODE_{u()}", 99001, _NOW),
        id="promo_redemptions",
    )

    # 22. referrals — NOT NULL: referrer_id, invitee_id; UNIQUE(referrer_id, invitee_id, level)
    yield pytest.param(
        "referrals",
        "INSERT INTO referrals(referrer_id, invitee_id, level, created_at) "
        "VALUES(?,?,?,?)",
        # Use different invitee per run to avoid unique conflict
        lambda: (99001, int(uuid.uuid4().int % 10**9) + 1, 1, _NOW),
        id="referrals",
    )

    # 23. reports — NOT NULL: tg_id, kind
    yield pytest.param(
        "reports",
        "INSERT INTO reports(tg_id, kind, created_at) VALUES(?,?,?)",
        lambda: (99001, "natal", _NOW),
        id="reports",
    )

    # 24. safety_events — all nullable
    yield pytest.param(
        "safety_events",
        "INSERT INTO safety_events(tg_id, category, created_at) VALUES(?,?,?)",
        lambda: (99001, "crisis", _NOW),
        id="safety_events",
    )

    # 25. shared_context_events — NOT NULL: tg_id, event_type, agent, content, created_at
    yield pytest.param(
        "shared_context_events",
        "INSERT INTO shared_context_events("
        "tg_id, event_type, agent, content, created_at"
        ") VALUES(?,?,?,?,?)",
        lambda: (99001, "recommendation", "oracle", "test content", _NOW),
        id="shared_context_events",
    )

    # 26. shared_context_snapshots — NOT NULL: tg_id, snapshot_type, snapshot_key,
    #     payload_json, created_at; UNIQUE(tg_id, snapshot_type, snapshot_key)
    yield pytest.param(
        "shared_context_snapshots",
        "INSERT INTO shared_context_snapshots("
        "tg_id, snapshot_type, snapshot_key, payload_json, created_at"
        ") VALUES(?,?,?,?,?)",
        lambda: (99001, "transits", f"key_{u()}", "{}", _NOW),
        id="shared_context_snapshots",
    )

    # 27. synastry_cache — all nullable
    yield pytest.param(
        "synastry_cache",
        "INSERT INTO synastry_cache(tg_id, partner_key, score, created_at) "
        "VALUES(?,?,?,?)",
        lambda: (99001, f"pkey_{u()}", 80, _NOW),
        id="synastry_cache",
    )

    # 28. tarot_readings — all nullable
    yield pytest.param(
        "tarot_readings",
        "INSERT INTO tarot_readings(tg_id, spread, question, created_at) "
        "VALUES(?,?,?,?)",
        lambda: (99001, "one", "test?", _NOW),
        id="tarot_readings",
    )

    # 29. threads — NOT NULL: tg_id, agent DEFAULT 'oracle'
    yield pytest.param(
        "threads",
        "INSERT INTO threads(tg_id, agent, created_at) VALUES(?,?,?)",
        lambda: (99001, "oracle", _NOW),
        id="threads",
    )

    # 30. user_notes — NOT NULL: tg_id
    yield pytest.param(
        "user_notes",
        "INSERT INTO user_notes(tg_id, text, created_at) VALUES(?,?,?)",
        lambda: (99001, "note text", _NOW),
        id="user_notes",
    )

    # 31. user_notifications — NOT NULL: tg_id, kind, title, body, dedupe_key, created_at
    #     UNIQUE(tg_id, dedupe_key)
    yield pytest.param(
        "user_notifications",
        "INSERT INTO user_notifications("
        "tg_id, kind, title, body, dedupe_key, created_at"
        ") VALUES(?,?,?,?,?,?)",
        lambda: (99001, "test", "Test Title", "Test body", f"dk_{u()}", _NOW),
        id="user_notifications",
    )


# ── parametrized test ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("table,sql,params_factory", list(_cases()))
async def test_lastrowid_for_id_table(db, table, sql, params_factory):
    """Each _ID_TABLES member must return a positive integer lastrowid on INSERT.

    This test is a characterization net: it documents the current behaviour of
    PostgresDatabase.execute (RETURNING id injection by the shim) so that any
    DB-001 migration that removes or changes the injection logic is caught.
    """
    from app.data.postgres import _ID_TABLES

    # Sanity: the table must still be in _ID_TABLES (catches accidental drift)
    assert table in _ID_TABLES, (
        f"Table '{table}' was removed from _ID_TABLES — "
        "update this test accordingly"
    )

    params = params_factory()
    cur = await db.execute(sql, params)

    assert cur.lastrowid is not None, (
        f"INSERT into '{table}' returned lastrowid=None — "
        "RETURNING id injection may be broken"
    )
    assert isinstance(cur.lastrowid, int), (
        f"lastrowid for '{table}' is not an int: {cur.lastrowid!r}"
    )
    assert cur.lastrowid > 0, (
        f"lastrowid for '{table}' is not positive: {cur.lastrowid}"
    )
