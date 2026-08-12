"""Проверка operational сигналов для cron/monitoring.

Источник HTTP/webhook сигналов — JSONL logs, источник LLM/freshness — SQLite.
Скрипт не выводит строки сообщений, diary, memory или webhook payload.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _log_counts(path: Path, cutoff: datetime) -> dict[str, int]:
    counts = {"http_5xx": 0, "webhook_failure": 0, "llm_fallback": 0, "llm_request": 0}
    if not path.is_file():
        return counts
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        stamp = _parse_time(item.get("ts"))
        if not stamp or stamp < cutoff:
            continue
        event = item.get("event")
        if event in counts:
            counts[event] += 1
    return counts


def _db_counts(db_path: Path, cutoff: datetime) -> dict[str, float | int]:
    if not db_path.is_file():
        return {"llm_calls": 0, "llm_failed": 0, "last_backup_age_s": -1}
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
    try:
        stamp = cutoff.isoformat()
        calls = db.execute(
            "SELECT COUNT(*) FROM llm_usage WHERE created_at>=?", (stamp,)
        ).fetchone()[0]
        failed = db.execute(
            "SELECT COUNT(*) FROM llm_usage WHERE created_at>=? AND ok=0", (stamp,)
        ).fetchone()[0]
    finally:
        db.close()
    return {"llm_calls": calls, "llm_failed": failed, "last_backup_age_s": -1}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default="data/oracle.db")
    parser.add_argument("--log-file", default="")
    parser.add_argument("--backup-dir", default="backups")
    parser.add_argument("--window-minutes", type=int, default=15)
    parser.add_argument("--max-5xx", type=int, default=0)
    parser.add_argument("--max-webhook-failures", type=int, default=0)
    parser.add_argument("--max-fallback-rate", type=float, default=0.25)
    parser.add_argument("--max-backup-age-hours", type=float, default=30)
    args = parser.parse_args()
    if args.window_minutes < 1:
        parser.error("--window-minutes must be positive")

    cutoff = _now() - timedelta(minutes=args.window_minutes)
    log_counts = _log_counts(Path(args.log_file), cutoff) if args.log_file else {
        "http_5xx": 0, "webhook_failure": 0, "llm_fallback": 0, "llm_request": 0,
    }
    db_counts = _db_counts(Path(args.db_path), cutoff)
    completed_llm = log_counts["llm_fallback"] + log_counts["llm_request"]
    total_llm = max(completed_llm, int(db_counts["llm_calls"]))
    failed_llm = int(db_counts["llm_failed"])
    fallback_rate = log_counts["llm_fallback"] / completed_llm if completed_llm else 0.0

    backups = sorted(
        [*Path(args.backup_dir).glob("oracle-*.db"), *Path(args.backup_dir).glob("oracle-*.db.enc")],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    backup_age_h = ((_now().timestamp() - backups[0].stat().st_mtime) / 3600) if backups else float("inf")
    alerts: list[str] = []
    if log_counts["http_5xx"] > args.max_5xx:
        alerts.append("http_5xx_threshold")
    if log_counts["webhook_failure"] > args.max_webhook_failures:
        alerts.append("webhook_failure_threshold")
    if fallback_rate > args.max_fallback_rate:
        alerts.append("llm_fallback_rate_threshold")
    if backup_age_h > args.max_backup_age_hours:
        alerts.append("backup_stale_or_missing")

    result = {
        "ok": not alerts,
        "window_minutes": args.window_minutes,
        "http_5xx": log_counts["http_5xx"],
        "webhook_failures": log_counts["webhook_failure"],
        "llm_calls": total_llm,
        "llm_failed": failed_llm,
        "llm_fallbacks": log_counts["llm_fallback"],
        "llm_fallback_rate": round(fallback_rate, 4),
        "backup_age_hours": round(backup_age_h, 2) if backup_age_h != float("inf") else None,
        "alerts": alerts,
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
