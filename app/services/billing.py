"""Покупки: витрина, оформление заказа, выдача купленного, промокоды.

Здесь собран весь путь денег, чтобы «что клиентка получила за оплату» читалось
одним файлом. Инварианты:

- заказ создаётся ДО оплаты и получает уникальный payload → повторный вебхук
  Telegram не выдаёт товар дважды;
- выдача (`_apply_grant`) — единственная точка, где что-то начисляется, и она
  вызывается только из `apply_payment`, `pay_with_crystals` и `redeem_promo`;
- покупка за Кристаллы сначала списывает баланс и только потом выдаёт: обратный
  порядок при сбое оставил бы товар бесплатным.
"""
from __future__ import annotations

import logging

from ..repo import analytics, billing as repo, content, growth, users

log = logging.getLogger("oracle.billing")

# Что делает выдача для каждого вида товара.
GRANT_KINDS = ("plan", "crystals", "spread", "report", "question")


class PurchaseError(Exception):
    """Покупка невозможна — текст предназначен клиентке."""


# ─────────────────────────────── витрина ──────────────────────────────────────

async def storefront(db, user) -> dict:
    """Данные для магазина: тарифы, товары по группам, текущее состояние."""
    plans = await repo.list_plans(db)
    products = await repo.list_products(db)
    current = user["sub_level"] if users.sub_active(user) else "free"
    groups: dict[str, list] = {}
    for p in products:
        groups.setdefault(p["kind"], []).append(p)
    return {
        "current_plan": current,
        "sub_active": users.sub_active(user),
        "sub_days_left": users.sub_days_left(user),
        "crystals": user["crystals"] or 0,
        "plans": plans,
        "products": groups,
        "entitlements": await repo.list_entitlements(db, user["tg_id"]),
    }


# ──────────────────────────── оформление заказа ───────────────────────────────

async def checkout_product(db, tg_id: int, sku: str, *,
                           surface: str = "bot") -> dict:
    """Создаёт заказ на товар и возвращает данные для инвойса Stars."""
    product = await repo.get_product(db, sku)
    if not product:
        raise PurchaseError("Такого товара уже нет в лавке 🌙")
    if not product["price_stars"]:
        raise PurchaseError("Этот товар продаётся только за Кристаллы ✦")
    order = await repo.create_order(
        db, tg_id, product["kind"], sku=sku, title=product["title"],
        amount_stars=product["price_stars"], surface=surface,
        meta={"grant_kind": product["grant_kind"], "grant_code": product["grant_code"],
              "grant_qty": product["grant_qty"], "valid_days": product["valid_days"]})
    await analytics.track(db, analytics.E_INVOICE, tg_id,
                          props={"sku": sku, "stars": product["price_stars"]},
                          surface=surface)
    return {**order, "description": product["description"] or product["title"],
            "product": dict(product)}


async def checkout_plan(db, tg_id: int, plan_code: str, *,
                        surface: str = "bot") -> dict:
    """Создаёт заказ на подписку."""
    plan = await repo.get_plan(db, plan_code)
    if not plan or not plan.get("price_stars"):
        raise PurchaseError("Этот тариф нельзя оплатить здесь 🌙")
    order = await repo.create_order(
        db, tg_id, "plan", sku=plan_code, title=plan["title"],
        amount_stars=plan["price_stars"], surface=surface,
        meta={"grant_kind": "plan", "grant_code": plan_code,
              "grant_qty": 1, "valid_days": plan["period_days"]})
    await analytics.track(db, analytics.E_INVOICE, tg_id,
                          props={"plan": plan_code, "stars": plan["price_stars"]},
                          surface=surface)
    return {**order, "description": plan.get("tagline") or plan["title"], "plan": plan}


async def pay_with_crystals(db, tg_id: int, sku: str, *,
                            surface: str = "bot") -> dict:
    """Покупка товара за Кристаллы — без Telegram-инвойса, сразу."""
    product = await repo.get_product(db, sku)
    if not product:
        raise PurchaseError("Такого товара уже нет в лавке 🌙")
    price = product["price_crystals"] or 0
    if price <= 0:
        raise PurchaseError("Этот товар продаётся только за ⭐ Stars")

    order = await repo.create_order(
        db, tg_id, product["kind"], sku=sku, title=product["title"],
        amount_crystals=price, surface=surface,
        meta={"grant_kind": product["grant_kind"], "grant_code": product["grant_code"],
              "grant_qty": product["grant_qty"], "valid_days": product["valid_days"]})

    if not await repo.spend_crystals(db, tg_id, price, f"buy:{sku}",
                                     ref=order["payload"]):
        raise PurchaseError(f"Нужно ✦{price}, а у тебя меньше. Пополни запас 💎")

    granted = await _apply_grant(
        db, tg_id, product["grant_kind"], product["grant_code"],
        qty=product["grant_qty"] or 1, valid_days=product["valid_days"],
        source="purchase", order_id=order["id"])
    await repo.mark_order_paid(db, order["payload"], provider="crystals",
                               amount_stars=0)
    await analytics.track(db, analytics.E_PAID, tg_id,
                          props={"sku": sku, "crystals": price}, surface=surface)
    return {"order": order, "granted": granted, "product": dict(product)}


# ──────────────────────────── приём оплаты ────────────────────────────────────

async def apply_payment(db, payload: str, *, charge_id: str | None = None,
                        amount_stars: int | None = None) -> dict | None:
    """Обрабатывает успешную оплату Stars. None — заказ уже обработан.

    Идемпотентность целиком на стороне БД (`mark_order_paid` меняет статус только
    из `pending`), поэтому повторная доставка апдейта безопасна.
    """
    order = await repo.mark_order_paid(db, payload, charge_id=charge_id,
                                       amount_stars=amount_stars)
    if not order:
        log.info("оплата %s уже обработана или заказ не найден", payload)
        return None

    meta = _order_meta(order)
    granted = await _apply_grant(
        db, order["tg_id"], meta.get("grant_kind"), meta.get("grant_code"),
        qty=meta.get("grant_qty") or 1, valid_days=meta.get("valid_days"),
        source="purchase", order_id=order["id"])
    await analytics.track(db, analytics.E_PAID, order["tg_id"],
                          props={"sku": order["sku"], "kind": order["kind"],
                                 "stars": order["amount_stars"]},
                          surface=order["surface"] or "bot")
    await _referral_revenue_bonus(db, order["tg_id"], order["amount_stars"] or 0)
    return {"order": dict(order), "granted": granted}


def _order_meta(order) -> dict:
    import json
    try:
        return json.loads(order["meta_json"] or "{}")
    except (TypeError, ValueError):
        return {}


# ──────────────────────────────── выдача ──────────────────────────────────────

async def _apply_grant(db, tg_id: int, kind: str | None, code: str | None, *,
                       qty: int = 1, valid_days: int | None = None,
                       source: str = "purchase",
                       order_id: int | None = None) -> dict:
    """Начисляет купленное. Возвращает описание для сообщения клиентке."""
    if kind == "plan":
        plan = await repo.get_plan(db, code or "vip")
        days = valid_days or plan.get("period_days") or 30
        until = await users.extend_subscription(db, tg_id, code or "vip", days)
        bonus = plan.get("crystals_grant") or 0
        if bonus:
            await repo.add_crystals(db, tg_id, bonus, f"plan_bonus:{code}")
        return {"kind": "plan", "plan": plan, "days": days, "until": until,
                "crystals": bonus,
                "title": plan.get("title", "Подписка")}

    if kind == "crystals":
        amount = qty or 0
        balance = await repo.add_crystals(db, tg_id, amount, f"purchase:{code or 'pack'}")
        return {"kind": "crystals", "amount": amount, "balance": balance,
                "title": f"✦ {amount} Кристаллов"}

    if kind in ("spread", "report", "question"):
        await repo.grant_entitlement(db, tg_id, kind, code, qty=qty,
                                     valid_days=valid_days, source=source,
                                     order_id=order_id)
        return {"kind": kind, "code": code, "qty": qty, "valid_days": valid_days,
                "title": {"spread": "Расклад", "report": "Разбор",
                          "question": "Вопросы"}[kind]}

    log.warning("неизвестный вид выдачи: %s/%s", kind, code)
    return {"kind": "unknown", "title": "Покупка"}


async def grant_manually(db, tg_id: int, kind: str, code: str | None = None, *,
                         qty: int = 1, days: int | None = None,
                         admin_id: int | None = None) -> dict:
    """Выдача из админки (подарок, компенсация, тест)."""
    granted = await _apply_grant(db, tg_id, kind, code, qty=qty, valid_days=days,
                                 source="admin")
    await analytics.track(db, "admin_grant", tg_id,
                          props={"kind": kind, "code": code, "qty": qty,
                                 "by": admin_id}, surface="admin")
    return granted


# ─────────────────────────────── промокоды ────────────────────────────────────

async def redeem_promo(db, tg_id: int, code: str) -> dict | None:
    """Активирует промокод и выдаёт то, что в нём записано."""
    promo = await growth.redeem(db, code, tg_id)
    if not promo:
        return None
    kind = promo["kind"]
    if kind == "crystals":
        granted = await _apply_grant(db, tg_id, "crystals", promo["code"],
                                     qty=promo["crystals"], source="promo")
    elif kind == "product" and promo["sku"]:
        product = await repo.get_product(db, promo["sku"])
        if not product:
            return None
        granted = await _apply_grant(
            db, tg_id, product["grant_kind"], product["grant_code"],
            qty=product["grant_qty"] or 1, valid_days=product["valid_days"],
            source="promo")
    else:
        granted = await _apply_grant(db, tg_id, "plan", promo["plan_code"],
                                     valid_days=promo["days"], source="promo")
    await analytics.track(db, analytics.E_PROMO, tg_id,
                          props={"code": promo["code"], "batch": promo["batch"],
                                 "kind": kind})
    # партия промокода = канал привлечения: без этого нельзя посчитать,
    # какой листинг Etsy приводит платящих
    user = await users.get(db, tg_id)
    if user and not user["source"] and promo["batch"]:
        await users.update(db, tg_id, source=f"promo:{promo['batch']}")
    return {**promo, "granted": granted}


# ─────────────────────── реферальный бонус с оплаты ───────────────────────────

async def _referral_revenue_bonus(db, tg_id: int, stars: int) -> None:
    """Кристаллы пригласившей, когда приглашённая впервые платит.

    Это главный аргумент делиться ссылкой: бонус приходит не за регистрацию (её
    легко накрутить), а за реальную оплату.
    """
    if stars <= 0:
        return
    referrer = await growth.referrer_of(db, tg_id)
    if not referrer:
        return
    share = await content.get_setting(db, "referral.revenue_share_crystals", 30)
    try:
        share = int(share or 0)
    except (TypeError, ValueError):
        share = 30
    if share <= 0:
        return
    # только за первую оплату приглашённой
    orders = await repo.user_orders(db, tg_id, limit=5)
    if sum(1 for o in orders if o["status"] == "paid") > 1:
        return
    await repo.add_crystals(db, referrer, share, "referral_revenue", ref=str(tg_id))
    await analytics.track(db, "referral_revenue_bonus", referrer,
                          props={"invitee": tg_id, "crystals": share})
