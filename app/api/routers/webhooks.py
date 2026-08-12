"""Вебхуки внешних платёжных систем (web-оплата подписки).

Зачем это нужно, если есть Telegram Stars. Stars обязательны для покупок внутри
бота (правило платформы), но их эффективная комиссия ~30-40%. Основной чек —
месячная подписка — по бизнес-плану проводится через web-платёжку с комиссией
3-5%: разница в марже кратная. Здесь принимающая сторона этого потока.

Инварианты, без которых деньги теряются или задваиваются:

- подпись проверяется по СЫРОМУ телу запроса: любой повторный `json.dumps`
  меняет байты и ломает HMAC;
- каждое событие пишется в `webhook_events` по своему id — провайдеры честно
  ретраят доставку, и без этой таблицы подписка продлевалась бы дважды;
- выдача идёт через тот же `services.billing`, что и Stars, поэтому «что именно
  клиентка получила» описано в одном месте.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from ...config import settings
from ...data.session import transaction, utcnow
from ...repo import billing as billing_repo
from ...services import analytics
from ...services import billing as billing_svc
from ...core.observability import log_event
from ..deps import get_db

log = logging.getLogger("oracle.api.webhooks")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _failure(message: str, *, status_code: int | None = None) -> None:
    log_event(
        log, logging.WARNING, "webhook_failure", message,
        operation="paddle", status_code=status_code,
    )

#: Насколько старую подпись принимаем. Защита от переигрывания перехваченного
#: запроса: подпись сама по себе бессрочна.
MAX_SIGNATURE_AGE = 300

#: События, после которых доступ открывается. Только то, где реально прошли
#: деньги: `subscription.updated` (смена плана/перенос даты) и
#: `subscription.activated` (старт без нового списания) выдавали бы дни
#: бесплатно при каждом пинге Paddle (review-фикс G37).
GRANTING_EVENTS = {
    "transaction.completed",
}


def _parse_signature(header: str) -> tuple[str, tuple[str, ...]]:
    """`ts=1700000000;h1=abc...;h1=old...` → timestamp and signatures."""
    ts = ""
    digests: list[str] = []
    for chunk in (header or "").split(";"):
        key, _, value = chunk.partition("=")
        if key.strip() == "ts":
            ts = value.strip()
        elif key.strip() == "h1" and value.strip():
            digests.append(value.strip())
    return ts, tuple(digests)


def verify_paddle(raw: bytes, header: str, secret: str) -> bool:
    """Проверяет подпись Paddle: HMAC-SHA256 от «ts:тело» с секретом вебхука."""
    if not secret:
        return False
    ts, digests = _parse_signature(header)
    if not ts or not digests:
        return False
    try:
        age = time.time() - int(ts)
    except ValueError:
        return False
    if age > MAX_SIGNATURE_AGE or age < -MAX_SIGNATURE_AGE:
        log.warning("подпись вебхука просрочена (%.0f с)", age)
        return False
    calc = hmac.new(secret.encode(), f"{ts}:".encode() + raw,
                    hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(calc, digest) for digest in digests)


async def _already_seen(db, event_id: str, provider: str, kind: str,
                        payload: str) -> bool:
    """True — событие уже обработано. Ключ идемпотентности на стороне БД."""
    try:
        async with transaction(db):
            cur = await db.execute(
                "INSERT OR IGNORE INTO webhook_events(event_id, provider, kind, "
                "payload, created_at) VALUES(?,?,?,?,?)",
                (event_id, provider, kind, payload[:8000], utcnow()))
        return not cur.rowcount
    except Exception as e:  # noqa: BLE001
        _failure("webhook idempotency journal unavailable", status_code=503)
        log.error("журнал вебхуков недоступен: %s", e)
        return False          # лучше обработать дважды, чем потерять оплату


def _custom_data(body: dict) -> dict:
    data = (body.get("data") or {})
    custom = data.get("custom_data") or {}
    if isinstance(custom, str):
        try:
            custom = json.loads(custom)
        except ValueError:
            custom = {}
    return custom if isinstance(custom, dict) else {}


@router.post("/paddle")
async def paddle(request: Request, db=Depends(get_db),
                 paddle_signature: str | None = Header(default=None,
                                                       alias="Paddle-Signature")):
    """Приём оплаты подписки через web. Возвращает 200 на всё, что уже учтено."""
    raw = await request.body()
    if len(raw) > 512 * 1024:
        raise HTTPException(413, "тело вебхука слишком большое")
    if not settings.paddle_webhook_secret:
        _failure("webhook secret is not configured", status_code=503)
        raise HTTPException(503, "web-оплата не настроена")
    if not verify_paddle(raw, paddle_signature or "", settings.paddle_webhook_secret):
        _failure("webhook signature rejected", status_code=401)
        raise HTTPException(401, "подпись не подтверждена")

    try:
        body = json.loads(raw.decode("utf-8"))
    except ValueError as e:
        _failure("webhook body is not JSON", status_code=400)
        raise HTTPException(400, "тело не JSON") from e

    event_id = str(body.get("event_id") or body.get("notification_id") or "")
    kind = str(body.get("event_type") or "")
    if not event_id:
        _failure("webhook event id is missing", status_code=400)
        raise HTTPException(400, "нет event_id")
    # Do not claim the event before the entitlement transaction. If billing
    # fails, Paddle must be able to retry rather than seeing a false duplicate.
    if kind not in GRANTING_EVENTS:
        duplicate = await _already_seen(
            db, event_id, "paddle", kind, raw.decode("utf-8", "ignore"))
        return {"ok": True, "duplicate": True} if duplicate else {"ok": True, "ignored": kind}

    data = body.get("data") or {}
    if data.get("status") != "completed":
        log.warning("вебхук %s имеет неожиданный статус %s", event_id,
                    data.get("status"))
        duplicate = await _already_seen(
            db, event_id, "paddle", kind, raw.decode("utf-8", "ignore"))
        return {"ok": True, "duplicate": True} if duplicate else {"ok": True, "ignored": "status"}

    custom = _custom_data(body)
    payload = str(custom.get("order_payload") or "")
    if not payload or len(payload) > 120:
        _failure("webhook order payload is invalid")
        return {"ok": True, "unmatched": True}
    order = await billing_repo.order_by_payload(db, payload)
    if not order or order["status"] != "pending":
        duplicate = await _already_seen(
            db, event_id, "paddle", kind, raw.decode("utf-8", "ignore"))
        _failure("webhook pending order binding failed")
        return {"ok": True, "duplicate": True} if duplicate else {"ok": True, "unmatched": True}
    if order["surface"] != "web" or order["kind"] != "plan":
        log.error("вебхук %s с недопустимым типом заказа", event_id)
        return {"ok": True, "unmatched": True}
    tg_id = int(order["tg_id"])
    plan = await billing_repo.get_plan(db, order["sku"] or "")
    if not plan or not plan.get("is_active"):
        log.error("вебхук %s для неактивного тарифа %s", event_id, order["sku"])
        return {"ok": True, "unmatched": True}
    order_meta = billing_svc._order_meta(order)
    expected_transaction = str(order_meta.get("paddle_transaction_id") or "")
    actual_transaction = str(data.get("id") or "")
    if expected_transaction and actual_transaction != expected_transaction:
        log.error("вебхук %s не совпал с transaction_id заказа", event_id)
        return {"ok": True, "unmatched": True}
    expected_price = settings.paddle_price_id(order["sku"] or "")
    if expected_price:
        price_ids = {
            str((item.get("price") or {}).get("id") or item.get("price_id") or "")
            for item in (data.get("items") or []) if isinstance(item, dict)
        }
        if expected_price not in price_ids:
            log.error("вебхук %s не совпал с price_id тарифа", event_id)
            return {"ok": True, "unmatched": True}
    result = await billing_svc.apply_payment(
        db, order["payload"], charge_id=event_id, amount_stars=0,
        provider="paddle", currency=str(data.get("currency_code") or "USD"))
    await analytics.track(db, "web_payment", tg_id,
                          props={"plan": order["sku"], "event": kind}, surface="web")
    duplicate = await _already_seen(
        db, event_id, "paddle", kind, raw.decode("utf-8", "ignore"))
    if duplicate:
        log.info("вебхук %s уже записан после идемпотентной обработки", event_id)
    log.info("web-оплата: клиентка %s, тариф %s", tg_id, order["sku"])
    return {"ok": True, "granted": bool(result), "duplicate": duplicate}
