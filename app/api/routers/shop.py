"""Лавка: тарифы, товары, оплата Stars и Кристаллами, промокоды.

Оплата Stars из Mini App идёт через `createInvoiceLink`: ссылку открывает
`Telegram.WebApp.openInvoice`, а зачисление приходит боту апдейтом
`successful_payment` — там же и выдача. Поэтому здесь мы только создаём заказ
и ссылку, но ничего не выдаём.
"""
from __future__ import annotations

import json
import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...repo import billing as billing_repo
from ...services import analytics
from ...services import billing as billing_svc
from ...services import invoices
from ..deps import current_user, get_db, rate_limit

log = logging.getLogger("oracle.api.shop")

router = APIRouter(prefix="/api/shop", tags=["shop"])


@router.get("")
async def storefront(user=Depends(current_user), db=Depends(get_db)):
    await analytics.track(db, analytics.E_SHOP_VIEW, user["tg_id"], surface="miniapp")
    return await billing_svc.storefront(db, user)


class InvoiceIn(BaseModel):
    sku: str | None = None
    plan: str | None = None


@router.post("/invoice", dependencies=[Depends(rate_limit("write"))])
async def create_invoice(item: InvoiceIn, user=Depends(current_user),
                         db=Depends(get_db)):
    """Ссылка на оплату Stars для `openInvoice`."""
    if not item.sku and not item.plan:
        raise HTTPException(400, "нужен sku товара или код тарифа")
    try:
        order = (await billing_svc.checkout_plan(db, user["tg_id"], item.plan,
                                                 surface="miniapp")
                 if item.plan else
                 await billing_svc.checkout_product(db, user["tg_id"], item.sku,
                                                    surface="miniapp"))
    except billing_svc.PurchaseError as e:
        raise HTTPException(400, str(e)) from e

    try:
        link = await invoices.create_link(
            order["title"], order["description"], order["payload"],
            order["amount_stars"])
    except invoices.InvoiceError as e:
        log.error("ссылка на оплату не создана: %s", e)
        raise HTTPException(503, "Оплата сейчас недоступна, попробуй чуть позже 🌙")
    return {"link": link, "payload": order["payload"],
            "amount_stars": order["amount_stars"], "title": order["title"]}


@router.post("/web-checkout", dependencies=[Depends(rate_limit("write"))])
async def web_checkout(item: InvoiceIn, user=Depends(current_user),
                       db=Depends(get_db)):
    """Ссылка на оплату подписки вне Telegram.

    Комиссия web-платёжки — единицы процентов против ~30-40% у Stars, поэтому
    основной чек (месячная подписка) по бизнес-плану идёт именно так. Кто она и
    какой тариф выбрала, передаём в `custom_data`: вебхук вернёт это обратно.
    """
    from ...config import settings
    from ...repo import content

    if not await content.is_on(db, "web_payments", user["tg_id"], default=False):
        raise HTTPException(404, "web-оплата пока недоступна")
    if not settings.paddle_checkout_url:
        raise HTTPException(503, "web-оплата не настроена")

    plan_code = item.plan or "vip"
    plan = await billing_repo.get_plan(db, plan_code)
    if not plan or not plan.get("price_usd"):
        raise HTTPException(400, "у этого тарифа нет web-цены")

    payload = json.dumps({"tg_id": user["tg_id"], "plan": plan_code},
                         ensure_ascii=False)
    link = (f"{settings.paddle_checkout_url}"
            f"?custom_data={quote(payload)}&plan={quote(plan_code)}")
    await analytics.track(db, "web_checkout", user["tg_id"],
                          props={"plan": plan_code}, surface="miniapp")
    return {"link": link, "plan": plan_code, "price_usd": plan["price_usd"]}


class CrystalsIn(BaseModel):
    sku: str = Field(min_length=1, max_length=40)


@router.post("/crystals", dependencies=[Depends(rate_limit("write"))])
async def buy_with_crystals(item: CrystalsIn, user=Depends(current_user),
                            db=Depends(get_db)):
    """Покупка за Кристаллы — мгновенно, без Telegram-инвойса."""
    try:
        result = await billing_svc.pay_with_crystals(db, user["tg_id"], item.sku,
                                                    surface="miniapp")
    except billing_svc.PurchaseError as e:
        raise HTTPException(402, str(e)) from e
    fresh = await billing_repo.list_entitlements(db, user["tg_id"])
    return {"ok": True, "granted": result["granted"], "entitlements": fresh}


class PromoIn(BaseModel):
    code: str = Field(min_length=3, max_length=40)


@router.post("/promo", dependencies=[Depends(rate_limit("write"))])
async def redeem_promo(item: PromoIn, user=Depends(current_user), db=Depends(get_db)):
    result = await billing_svc.redeem_promo(db, user["tg_id"], item.code)
    if not result:
        raise HTTPException(400, "Этот код не отзывается... проверь написание 🌙")
    return {"ok": True, **result}


@router.get("/orders")
async def orders(user=Depends(current_user), db=Depends(get_db)):
    return await billing_repo.user_orders(db, user["tg_id"], limit=30)


@router.get("/crystals/history")
async def crystals_history(user=Depends(current_user), db=Depends(get_db)):
    return await billing_repo.crystal_history(db, user["tg_id"], limit=40)
