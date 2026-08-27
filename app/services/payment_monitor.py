"""Безопасный мониторинг платёжного контура.

Сервис намеренно отделён от billing: он только читает состояние, сохраняет
агрегированный snapshot без PII/raw webhook payload и отправляет owner alert
при переходе состояния. Выдача прав, изменение балансов и обработка платежей
здесь невозможны.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from ..config import settings
from ..repo import content
from . import cryptobot, telegram

log = logging.getLogger("oracle.payment_monitor")

SETTING_KEY = "system.payment_monitor"
STALE_PENDING_HOURS = 2
ALERT_COOLDOWN_HOURS = 6


def _now(value: datetime | None = None) -> datetime:
    return value or datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


async def _scalar(db, sql: str, *params) -> int:
    cur = await db.execute(sql, params)
    row = await cur.fetchone()
    return int((row[0] if row else 0) or 0)


async def _webhook_activity(db, since: str) -> dict:
    cur = await db.execute(
        "SELECT provider, COUNT(*) AS n, MAX(created_at) AS last_at "
        "FROM webhook_events WHERE created_at>=? GROUP BY provider", (since,))
    return {
        str(row["provider"] or "unknown"): {
            "events_24h": int(row["n"] or 0),
            "last_event_at": row["last_at"],
        }
        for row in await cur.fetchall()
    }


async def _webhook_failures(db, since: str) -> dict:
    cur = await db.execute(
        "SELECT provider, COUNT(*) AS n FROM payment_webhook_failures "
        "WHERE created_at>=? GROUP BY provider", (since,))
    return {str(row["provider"] or "unknown"): int(row["n"] or 0)
            for row in await cur.fetchall()}


async def _database_checks(db, now: datetime) -> dict:
    since = _iso(now - timedelta(hours=24))
    stale_before = _iso(now - timedelta(hours=STALE_PENDING_HOURS))
    webhook_activity = await _webhook_activity(db, since)
    failures = await _webhook_failures(db, since)

    stale_pending = await _scalar(
        db, "SELECT COUNT(*) FROM orders WHERE status='pending' AND created_at<?",
        stale_before)
    failed_orders = await _scalar(
        db, "SELECT COUNT(*) FROM orders WHERE status='failed' AND created_at>=?", since)
    orphan_payments = await _scalar(
        db, "SELECT COUNT(*) FROM payments p LEFT JOIN orders o ON o.id=p.order_id "
        "WHERE o.id IS NULL")
    paid_without_payment = await _scalar(
        db, "SELECT COUNT(*) FROM orders o LEFT JOIN payments p ON p.order_id=o.id "
        "AND p.status='succeeded' WHERE o.status='paid' AND p.id IS NULL")
    duplicate_paid_orders = await _scalar(
        db, "SELECT COUNT(*) FROM (SELECT order_id FROM payments "
        "WHERE status='succeeded' AND order_id IS NOT NULL GROUP BY order_id "
        "HAVING COUNT(*)>1)")
    ledger_mismatches = await _scalar(
        db, "SELECT COUNT(*) FROM users u JOIN crystal_ledger l ON l.id=("
        "SELECT MAX(l2.id) FROM crystal_ledger l2 WHERE l2.tg_id=u.tg_id) "
        "WHERE u.crystals != l.balance")

    return {
        "pending_orders_stale": stale_pending,
        "failed_orders_24h": failed_orders,
        "webhook_events_24h": webhook_activity,
        "webhook_failures_24h": failures,
        "reconciliation": {
            "orphan_payments": orphan_payments,
            "paid_orders_without_payment": paid_without_payment,
            "duplicate_paid_orders": duplicate_paid_orders,
            "crystal_ledger_mismatches": ledger_mismatches,
        },
    }


async def _provider_checks(db, now: datetime, *, external: bool) -> dict:
    since = _iso(now - timedelta(hours=24))
    activity = await _webhook_activity(db, since)
    providers: dict[str, dict] = {
        "telegram_stars": {
            "configured": bool(settings.bot_token),
            "transport": "bot_polling",
            "status": "ok" if settings.bot_token else "not_configured",
            "payments_24h": await _scalar(
                db, "SELECT COUNT(*) FROM payments WHERE provider='telegram_stars' "
                "AND status='succeeded' AND created_at>=?", since),
        },
        "cryptobot": {
            "configured": bool(settings.cryptobot_api_token),
            "transport": "crypto_pay_webhook",
            "status": "ok" if settings.cryptobot_api_token else "not_configured",
            "events_24h": activity.get("cryptobot", {}).get("events_24h", 0),
            "last_event_at": activity.get("cryptobot", {}).get("last_event_at"),
        },
        "paddle": {
            "configured": bool(settings.paddle_webhook_secret),
            "transport": "paddle_webhook",
            "status": "ok" if settings.paddle_webhook_secret else "not_configured",
            "events_24h": activity.get("paddle", {}).get("events_24h", 0),
            "last_event_at": activity.get("paddle", {}).get("last_event_at"),
        },
    }

    if external and settings.cryptobot_api_token:
        try:
            balances = await cryptobot.get_balance()
            providers["cryptobot"]["balances"] = [
                {"asset": str(item.get("currency_code") or "")[:16],
                 "available": str(item.get("available") or "0")[:64],
                 "onhold": str(item.get("onhold") or "0")[:64]}
                for item in balances if isinstance(item, dict)
            ]
        except Exception as exc:  # noqa: BLE001
            providers["cryptobot"]["status"] = "degraded"
            providers["cryptobot"]["balance_error"] = "provider_unavailable"
            log.warning("Crypto Pay health check failed: %s", type(exc).__name__)
    elif settings.cryptobot_api_token:
        providers["cryptobot"]["balances"] = []

    return providers


def _overall_status(db_checks: dict, providers: dict) -> str:
    reconciliation = db_checks["reconciliation"]
    if any(reconciliation.values()):
        return "critical"
    if db_checks["pending_orders_stale"] or db_checks["failed_orders_24h"]:
        return "degraded"
    if any(item.get("status") == "degraded" for item in providers.values()):
        return "degraded"
    return "ok"


async def build_snapshot(db, *, now: datetime | None = None,
                         external: bool = False) -> dict:
    checked = _now(now)
    db_checks = await _database_checks(db, checked)
    providers = await _provider_checks(db, checked, external=external)
    return {
        "status": _overall_status(db_checks, providers),
        "checked_at": _iso(checked),
        "stale_pending_threshold_hours": STALE_PENDING_HOURS,
        "checks": db_checks,
        "providers": providers,
    }


async def latest(db) -> dict | None:
    value = await content.get_setting(db, SETTING_KEY)
    return value if isinstance(value, dict) else None


def _alert_text(snapshot: dict, *, recovered: bool = False) -> str:
    status = snapshot.get("status")
    if recovered:
        title = "✅ Платёжный контур восстановлен"
    else:
        title = "🚨 Платёжный мониторинг: " + ("CRITICAL" if status == "critical" else "DEGRADED")
    checks = snapshot.get("checks") or {}
    recon = checks.get("reconciliation") or {}
    return (
        f"{title}\n"
        f"Состояние: {status}\n"
        f"Зависшие заказы: {checks.get('pending_orders_stale', 0)}\n"
        f"Ошибки заказов за 24 ч: {checks.get('failed_orders_24h', 0)}\n"
        f"Ошибки webhook за 24 ч: {sum((checks.get('webhook_failures_24h') or {}).values())}\n"
        f"Аномалии сверки: {sum(recon.values())}\n"
        f"Проверено: {snapshot.get('checked_at')}"
    )


async def run(bot, db, *, now: datetime | None = None) -> dict:
    """Run one bounded check, save only aggregate state and alert on transitions."""
    snapshot = await build_snapshot(db, now=now, external=True)
    previous = await latest(db)
    previous_status = previous.get("status") if previous else None
    previous_alert_at = previous.get("last_alert_at") if previous else None
    current = dict(snapshot)
    current["last_alert_at"] = previous_alert_at

    checked = _now(now)
    should_alert = False
    recovered = previous_status in {"critical", "degraded"} and snapshot["status"] == "ok"
    if previous_status is not None and previous_status != snapshot["status"]:
        should_alert = True
    elif snapshot["status"] in {"critical", "degraded"} and previous_alert_at:
        try:
            last_alert = datetime.fromisoformat(previous_alert_at)
            should_alert = checked - last_alert >= timedelta(hours=ALERT_COOLDOWN_HOURS)
        except ValueError:
            should_alert = True
    elif snapshot["status"] in {"critical", "degraded"}:
        should_alert = True

    if should_alert and settings.admin_id and settings.bot_token:
        delivered = await telegram.send_message(
            settings.admin_id, _alert_text(snapshot, recovered=recovered), html=False)
        if delivered:
            current["last_alert_at"] = snapshot["checked_at"]
    await content.set_setting(db, SETTING_KEY, current)
    return current


async def admin_snapshot(db) -> dict:
    """Return latest persisted snapshot, or a DB-only safe view before first tick."""
    value = await latest(db)
    if value:
        return value
    return await build_snapshot(db, external=False)
