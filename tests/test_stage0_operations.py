from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.observability import JsonRedactingFormatter, redact_text
from scripts import check_cache_busting, ops_alerts

ROOT = Path(__file__).resolve().parent.parent


def test_redact_text_removes_secrets_email_and_numeric_ids():
    value = "tg_id=123456789 api_key=sk-secret email=test@example.com Bearer abc.def"
    redacted = redact_text(value)
    assert "123456789" not in redacted
    assert "sk-secret" not in redacted
    assert "test@example.com" not in redacted
    assert "Bearer abc.def" not in redacted


def test_json_formatter_emits_operational_fields_without_pii():
    record = logging.LogRecord(
        "oracle.test", logging.WARNING, __file__, 1,
        "failed for tg_id=123456789", (), None,
    )
    record.event = "webhook_failure"
    record.status_code = 401
    record.path = "/api/webhooks/paddle"
    payload = json.loads(JsonRedactingFormatter().format(record))
    assert payload["event"] == "webhook_failure"
    assert payload["status_code"] == 401
    assert payload["path"] == "/api/webhooks/paddle"
    assert "123456789" not in payload["message"]
    assert "request_id" in payload
    assert "release_id" in payload


def test_ops_alert_log_counts_are_windowed(tmp_path):
    now = datetime.now(timezone.utc).isoformat()
    log_file = tmp_path / "oracle.jsonl"
    log_file.write_text(
        "\n".join([
            json.dumps({"ts": now, "event": "http_5xx"}),
            json.dumps({"ts": now, "event": "webhook_failure"}),
            json.dumps({"ts": now, "event": "llm_fallback"}),
            json.dumps({"ts": now, "event": "llm_request"}),
        ]) + "\n",
        encoding="utf-8",
    )
    counts = ops_alerts._log_counts(
        log_file, ops_alerts._now() - timedelta(minutes=1)
    )
    assert counts == {
        "http_5xx": 1,
        "webhook_failure": 1,
        "llm_fallback": 1,
        "llm_request": 1,
    }


def test_cache_busting_policy_and_public_legal_pages():
    assert check_cache_busting.main() == 0
    for name in ("privacy.html", "terms.html", "privacy-en.html", "terms-en.html"):
        assert (ROOT / "web" / name).is_file()


def test_ops_alert_db_counts_include_scheduler_status(tmp_path):
    db_path = tmp_path / "ops.db"
    import sqlite3

    db = sqlite3.connect(db_path)
    db.executescript(
        """
        CREATE TABLE llm_usage (created_at TEXT, ok INTEGER);
        CREATE TABLE scheduler_leases (
            name TEXT PRIMARY KEY,
            last_status TEXT,
            last_finished_at TEXT,
            failure_count INTEGER,
            last_error TEXT
        );
        """
    )
    stamp = datetime.now(timezone.utc).isoformat()
    db.execute(
        "INSERT INTO scheduler_leases VALUES ('main', 'ok', ?, 0, NULL)", (stamp,)
    )
    db.commit()
    db.close()

    counts = ops_alerts._db_counts(
        db_path, ops_alerts._now() - timedelta(minutes=15)
    )
    assert counts["scheduler_status"] == "ok"
    assert counts["scheduler_age_s"] >= 0
    assert counts["scheduler_failures"] == 0
