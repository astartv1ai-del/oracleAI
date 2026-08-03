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
from ...repo import users as users_repo
from ...services import analytics
from ...services import billing as billing_svc
from ..deps import get_db

log = logging.getLogger("oracle.api.webhooks")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

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


def _parse_signature(header: str) -> tuple[str, str]:
    """`ts=1700000000;h1=abc...` → (ts, h1)."""
    ts = digest = ""
    for chunk in (header or "").split(";"):
        key, _, value = chunk.partition("=")
        if key.strip() == "ts":
            ts = value.strip()
        elif key.strip() == "h1":
            digest = value.strip()
    return ts, digest


def verify_paddle(raw: bytes, header: str, secret: str) -> bool:
    """Проверяет подпись Paddle: HMAC-SHA256 от «ts:тело» с секретом вебхука."""
    if not secret:
        return False
    ts, digest = _parse_signature(header)
    if not ts or not digest:
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
    return hmac.compare_digest(calc, digest)


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
    if not settings.paddle_webhook_secret:
        log.warning("вебхук Paddle пришёл, но PADDLE_WEBHOOK_SECRET не задан")
        raise HTTPException(503, "web-оплата не настроена")
    if not verify_paddle(raw, paddle_signature or "", settings.paddle_webhook_secret):
        log.warning("вебхук Paddle с неверной подписью")
        raise HTTPException(401, "подпись не подтверждена")

    try:
        body = json.loads(raw.decode("utf-8"))
    except ValueError as e:
        raise HTTPException(400, "тело не JSON") from e

    event_id = str(body.get("event_id") or body.get("notification_id") or "")
    kind = str(body.get("event_type") or "")
    if not event_id:
        raise HTTPException(400, "нет event_id")
    if await _already_seen(db, event_id, "paddle", kind, raw.decode("utf-8", "ignore")):
        log.info("вебхук %s уже обработан", event_id)
        return {"ok": True, "duplicate": True}

    if kind not in GRANTING_EVENTS:
        return {"ok": True, "ignored": kind}

    custom = _custom_data(body)
    try:
        tg_id = int(custom.get("tg_id") or 0)
    except (TypeError, ValueError):
        tg_id = 0
    plan_code = str(custom.get("plan") or "vip")
    if not tg_id or not await users_repo.get(db, tg_id):
        log.error("вебхук %s без известной клиентки (tg_id=%s)", event_id, tg_id)
        return {"ok": True, "unmatched": True}

    plan = await billing_repo.get_plan(db, plan_code)
    order = await billing_repo.create_order(
        db, tg_id, "plan", sku=plan_code, title=plan.get("title", "Подписка"),
        amount_stars=0, surface="web",
        meta={"grant_kind": "plan", "grant_code": plan_code, "grant_qty": 1,
              "valid_days": plan.get("period_days") or 30,
              "provider": "paddle", "event_id": event_id})
    result = await billing_svc.apply_payment(db, order["payload"],
                                             charge_id=event_id, amount_stars=0)
    await analytics.track(db, "web_payment", tg_id,
                          props={"plan": plan_code, "event": kind}, surface="web")
    log.info("web-оплата: клиентка %s, тариф %s", tg_id, plan_code)
    return {"ok": True, "granted": bool(result)}
