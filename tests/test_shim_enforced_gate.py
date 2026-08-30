"""Characterization + gate tests for the SHIM_ENFORCED feature flag.

ADR-0003 defines this flag as the DB-001 shim-removal gate:
- ``SHIM_ENFORCED=0`` (default): legacy SQL still translates, warns via
  ``oracle.db.shim`` logger.
- ``SHIM_ENFORCED=1`` (CI + staging): legacy SQL raises
  ``LegacyShimUsageError``; native-dialect SQL passes through unchanged.

These tests are the mechanical proof that:
  1. ADR-0001 native dialect (named :params + ON CONFLICT (<col>) DO NOTHING
     + explicit RETURNING id) is a no-op through the shim.
  2. Legacy dialect (? placeholders or INSERT OR IGNORE) is correctly
     translated when the flag is off, and rejected when the flag is on.
"""
from __future__ import annotations

import logging

import pytest

from app.data.postgres import (
    LegacyShimUsageError,
    _needs_translation,
    _translate_sql,
)


# ── 1. Native dialect passes through untouched ──────────────────────────────

@pytest.mark.parametrize("sql", [
    "SELECT tg_id FROM users WHERE tg_id = :tg_id",
    "INSERT INTO users(tg_id, name) VALUES(:tg_id, :name) "
    "ON CONFLICT (tg_id) DO NOTHING",
    "UPDATE orders SET status='paid' WHERE id = :id RETURNING id, tg_id",
    "INSERT INTO memories(tg_id, fact) VALUES(:tg_id, :fact) RETURNING id",
])
def test_native_dialect_is_a_noop(sql: str) -> None:
    """A native-dialect string round-trips through _translate_sql unchanged."""
    assert not _needs_translation(sql)
    translated, names = _translate_sql(sql)
    # names must be empty for native dialect (no ? -> no positional binds)
    assert names == []
    # The only rewrite _translate_sql applies to native SQL is stripping a
    # trailing semicolon and whitespace. The rest is identical.
    assert translated == sql.strip().rstrip(";")


# ── 2. Legacy dialect is detected ───────────────────────────────────────────

@pytest.mark.parametrize("sql", [
    "SELECT * FROM users WHERE tg_id = ?",
    "INSERT INTO users(tg_id, name) VALUES(?, ?)",
    "INSERT OR IGNORE INTO plans(code) VALUES(?)",
    "UPDATE orders SET status=? WHERE id=?",
])
def test_legacy_dialect_is_detected(sql: str) -> None:
    assert _needs_translation(sql)


def test_question_mark_inside_string_literal_is_not_detected() -> None:
    """A ? inside a quoted literal is NOT a placeholder — it stays untouched.

    This guards the exact class of bugs the plan warns about in Etap 1
    ("строковые литералы с ? внутри SQL — шим сейчас молча их ломал бы").
    """
    sql = "SELECT * FROM users WHERE username = 'is this you?'"
    assert not _needs_translation(sql)


# ── 3. Shim translates when flag is OFF ─────────────────────────────────────

def test_shim_translates_when_flag_off(monkeypatch, caplog) -> None:
    monkeypatch.delenv("SHIM_ENFORCED", raising=False)
    caplog.set_level(logging.WARNING, logger="oracle.db.shim")
    sql = "INSERT OR IGNORE INTO plans(code, title) VALUES(?, ?)"
    translated, names = _translate_sql(sql)
    assert "ON CONFLICT DO NOTHING" in translated
    assert ":p0" in translated and ":p1" in translated
    assert names == ["p0", "p1"]
    # Legacy call MUST leave a WARNING breadcrumb for prod auditing.
    assert any(
        "legacy SQL" in record.getMessage() for record in caplog.records
    ), "expected 'legacy SQL' warning on oracle.db.shim logger"


# ── 4. Shim REJECTS when flag is ON ─────────────────────────────────────────

def test_shim_rejects_when_flag_on_question_marks(monkeypatch) -> None:
    monkeypatch.setenv("SHIM_ENFORCED", "1")
    with pytest.raises(LegacyShimUsageError) as excinfo:
        _translate_sql("SELECT * FROM users WHERE tg_id = ?")
    assert "SHIM_ENFORCED=1" in str(excinfo.value)
    assert "ADR-0001" in str(excinfo.value)


def test_shim_rejects_when_flag_on_insert_or_ignore(monkeypatch) -> None:
    monkeypatch.setenv("SHIM_ENFORCED", "1")
    with pytest.raises(LegacyShimUsageError):
        _translate_sql("INSERT OR IGNORE INTO plans(code) VALUES(?)")


def test_shim_flag_on_lets_native_sql_pass(monkeypatch) -> None:
    """The gate must be surgical: native SQL never trips it, even in strict mode."""
    monkeypatch.setenv("SHIM_ENFORCED", "1")
    translated, names = _translate_sql(
        "INSERT INTO users(tg_id, name) VALUES(:tg_id, :name) "
        "ON CONFLICT (tg_id) DO NOTHING"
    )
    assert names == []
    assert "ON CONFLICT (tg_id) DO NOTHING" in translated
