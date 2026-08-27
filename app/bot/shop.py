"""Лавка: подписки, одиночные расклады, разборы, вопросы, Кристаллы, оплата.

Приём платежа — единственное место, где выдаётся купленное, и оно идемпотентно:
Telegram может доставить `successful_payment` повторно, и товар не должен уйти
дважды (см. `services.billing.apply_payment`).
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, LabeledPrice, Message,
                           PreCheckoutQuery)

from ..repo import admin as admin_repo
from ..repo import billing as billing_repo
from ..repo import users
from ..services import analytics
from ..services import billing as billing_svc
from .chat import _send_long
from .keyboards import (back_menu, main_menu, plans_kb, products_kb, shop_kb)

log = logging.getLogger("oracle.bot.shop")
router = Router()

KIND_TITLES = {
    "spread": ("🎴 <b>Одиночные расклады</b>",
               "Большие расклады без подписки. Открытый расклад ждёт тебя 30 дней."),
    "report": ("📜 <b>Большие разборы</b>",
               "Длинный текст, который остаётся у тебя навсегда — "
               "его можно перечитывать."),
    "question": ("💬 <b>Дополнительные вопросы</b>",
                 "Сверх дневного лимита, когда нужно именно сейчас."),
    "crystals": ("✦ <b>Кристаллы</b>",
                 "Внутренняя валюта: экстренные вопросы и расклады со скидкой."),
}


async def _menu(db, tg_id: int):
    return main_menu(is_admin=bool(await admin_repo.resolve_role(db, tg_id)))


# ─────────────────────────────── витрина ──────────────────────────────────────

@router.callback_query(F.data == "shop")
async def shop(cb: CallbackQuery, db):
    user = await users.get(db, cb.from_user.id)
    await analytics.track(db, analytics.E_SHOP_VIEW, cb.from_user.id)
    await cb.message.answer(
        f"💎 <b>Лавка Оракула</b>\n\n"
        f"У тебя ✦{user['crystals']} Кристаллов.\n\n"
        f"<i>Пополняй Кристаллы и открывай расклады, разборы и вопросы — "
        f"по одному, когда нужно.</i>",
        reply_markup=shop_kb())
    await cb.answer()


@router.callback_query(F.data == "plans")
async def plans(cb: CallbackQuery, db):
    user = await users.get(db, cb.from_user.id)
    available = await billing_repo.list_plans(db)
    current = user["sub_level"] if users.sub_active(user) else "free"

    lines = ["👑 <b>Уровни доступа</b>", ""]
    for plan in available:
        if not plan.get("price_stars"):
            continue
        mark = " ← твой" if plan["code"] == current else ""
        badge = f" · <i>{plan['badge']}</i>" if plan.get("badge") else ""
        lines.append(f"<b>{plan['title']}</b> — ⭐{plan['price_stars']}"
                     f" / {plan['period_days']} дн.{badge}{mark}")
        if plan.get("tagline"):
            lines.append(f"<i>{plan['tagline']}</i>")
        for feature in (plan.get("features") or [])[:6]:
            lines.append(f"  • {feature}")
        lines.append("")
    await _send_long(cb.message, "\n".join(lines),
                     reply_markup=plans_kb(available, current))
    await cb.answer()


async def _show_products(cb: CallbackQuery, db, kind: str) -> None:
    products = await billing_repo.list_products(db, kind)
    if not products:
        await cb.answer("Здесь пока пусто")
        return
    from ...config import settings
    crypto_on = bool(settings.cryptobot_api_token)
    title, hint = KIND_TITLES.get(kind, ("💎 <b>Товары</b>", ""))
    lines = [title, f"<i>{hint}</i>", ""]
    for product in products:
        price = []
        if product["price_stars"]:
            price.append(f"⭐{product['price_stars']}")
        if product["price_crystals"]:
            price.append(f"✦{product['price_crystals']}")
        lines.append(f"<b>{product['title']}</b> — {' или '.join(price)}")
        if product["description"]:
            lines.append(f"<i>{product['description']}</i>")
        lines.append("")
    await cb.message.answer("\n".join(lines), reply_markup=products_kb(
        products,
        crypto_skus=billing_svc.CRYSTAL_PACKS_USD if crypto_on else ()))
    await cb.answer()


@router.callback_query(F.data == "shop_spreads")
async def shop_spreads(cb: CallbackQuery, db):
    await _show_products(cb, db, "spread")


@router.callback_query(F.data == "shop_reports")
async def shop_reports(cb: CallbackQuery, db):
    await _show_products(cb, db, "report")


@router.callback_query(F.data == "shop_questions")
async def shop_questions(cb: CallbackQuery, db):
    await _show_products(cb, db, "question")


@router.callback_query(F.data == "shop_crystals")
async def shop_crystals(cb: CallbackQuery, db):
    await _show_products(cb, db, "crystals")


@router.callback_query(F.data.startswith("product:"))
async def product_card(cb: CallbackQuery, db):
    """Карточка товара — на случай, если название не влезло в кнопку."""
    sku = cb.data.split(":", 1)[1]
    product = await billing_repo.get_product(db, sku)
    if not product:
        await cb.answer("Товара больше нет")
        return
    await cb.answer(f"{product['title']}: {product['description'] or ''}"[:190],
                    show_alert=True)


# ────────────────────────────── оплата Stars ──────────────────────────────────

@router.callback_query(F.data.startswith("buy_plan:"))
async def buy_plan(cb: CallbackQuery, db):
    code = cb.data.split(":", 1)[1]
    try:
        order = await billing_svc.checkout_plan(db, cb.from_user.id, code)
    except billing_svc.PurchaseError as e:
        await cb.answer(str(e), show_alert=True)
        return
    plan = order["plan"]
    await cb.message.answer_invoice(
        title=plan["title"][:32],
        description=(plan.get("tagline") or plan["title"])[:255],
        payload=order["payload"],
        currency="XTR",
        prices=[LabeledPrice(label=plan["title"][:32],
                             amount=order["amount_stars"])])
    await cb.answer()


@router.callback_query(F.data.startswith("buy_sku:"))
async def buy_sku(cb: CallbackQuery, db):
    sku = cb.data.split(":", 1)[1]
    try:
        order = await billing_svc.checkout_product(db, cb.from_user.id, sku)
    except billing_svc.PurchaseError as e:
        await cb.answer(str(e), show_alert=True)
        return
    await cb.message.answer_invoice(
        title=order["title"][:32],
        description=order["description"][:255],
        payload=order["payload"],
        currency="XTR",
        prices=[LabeledPrice(label=order["title"][:32],
                             amount=order["amount_stars"])])
    await cb.answer()


@router.callback_query(F.data.startswith("buy_crypto:"))
async def buy_crypto(cb: CallbackQuery, db):
    """Крипто-оплата пакета Кристаллов через Crypto Pay (без юрлица)."""
    from ...config import settings
    if not settings.cryptobot_api_token:
        await cb.answer("Крипто-оплата скоро откроется 🌙")
        return
    sku = cb.data.split(":", 1)[1]
    try:
        order = await billing_svc.checkout_crypto_crystals(db, cb.from_user.id, sku)
    except billing_svc.PurchaseError as e:
        await cb.answer(str(e), show_alert=True)
        return
    await cb.answer()
    await cb.message.answer(
        f"₿ <b>{order['title']}</b> — ${order['amount_usd']:.2f}\n\n"
        f"Оплатить можно картой или криптой (USDT, TON, BTC…) через @CryptoBot. "
        f"Кристаллы придут автоматически сразу после оплаты.\n"
        f"<i>Если оплата не прошла — напиши /start и попробуй ещё раз.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="₿ Оплатить", url=order["link"])],
            [InlineKeyboardButton(text="← Лавка", callback_data="shop")]]))


@router.callback_query(F.data.startswith("buy_crystals:"))
async def buy_with_crystals(cb: CallbackQuery, db):
    """Покупка за Кристаллы — сразу, без инвойса."""
    sku = cb.data.split(":", 1)[1]
    try:
        result = await billing_svc.pay_with_crystals(db, cb.from_user.id, sku)
    except billing_svc.PurchaseError as e:
        await cb.answer(str(e), show_alert=True)
        await cb.message.answer("💎 Пополнить Кристаллы:",
                                reply_markup=shop_kb())
        return
    user = await users.get(db, cb.from_user.id)
    await cb.answer("Открыто ✨")
    await cb.message.answer(
        f"✨ <b>{result['product']['title']}</b> — открыто!\n"
        f"Осталось ✦{user['crystals']}.\n\n"
        f"{_granted_hint(result['granted'])}",
        reply_markup=await _menu(db, cb.from_user.id))


def _granted_hint(granted: dict) -> str:
    """Что делать дальше — иначе покупка выглядит как «деньги ушли, и всё»."""
    kind = granted.get("kind")
    if kind == "spread":
        return "Открой 🎴 Расклад Таро — он уже ждёт тебя в списке."
    if kind == "report":
        return "Разбор соберётся в Mini App: раздел «Карта» → «Мои разборы»."
    if kind == "question":
        return f"Тебе доступно вопросов сверх лимита: {granted.get('qty', 1)}."
    if kind == "crystals":
        return f"Баланс: ✦{granted.get('balance', 0)}."
    if kind == "plan":
        return f"Доступ продлён на {granted.get('days', 30)} дней."
    return ""


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery, db):
    """Подтверждаем оплату, если заказ существует и ещё не оплачен."""
    order = await billing_repo.order_by_payload(db, query.invoice_payload)
    if not order:
        await query.answer(ok=False, error_message="Заказ не найден, создай его заново")
        return
    if order["status"] == "paid":
        await query.answer(ok=False, error_message="Этот заказ уже оплачен")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def paid(message: Message, db):
    payment = message.successful_payment
    result = await billing_svc.apply_payment(
        db, payment.invoice_payload,
        charge_id=payment.telegram_payment_charge_id,
        amount_stars=payment.total_amount)
    if not result:
        # повторная доставка апдейта: товар уже выдан
        log.info("повторная оплата пропущена",
                 extra={"event": "payment_duplicate"})
        await message.answer("Эта оплата уже зачтена ✨",
                             reply_markup=await _menu(db, message.from_user.id))
        return

    granted = result["granted"]
    if granted.get("kind") == "plan":
        text = (f"👑 <b>{granted['title']}</b> — доступ открыт на "
                f"{granted['days']} дней.\n"
                f"Я помню всё — продолжим с того места, где остановились ✨")
        if granted.get("crystals"):
            text += f"\n\nИ подарок: +✦{granted['crystals']} Кристаллов."
    elif granted.get("kind") == "crystals":
        text = (f"✨ +✦{granted['amount']}! Вселенная приняла твой дар.\n"
                f"Баланс: ✦{granted['balance']}.")
    else:
        text = (f"✨ <b>{result['order']['title']}</b> — открыто!\n\n"
                f"{_granted_hint(granted)}")
    await message.answer(text, reply_markup=await _menu(db, message.from_user.id))


# ──────────────────────────── мои покупки ─────────────────────────────────────

@router.callback_query(F.data == "my_entitlements")
async def my_entitlements(cb: CallbackQuery, db):
    items = await billing_repo.list_entitlements(db, cb.from_user.id)
    if not items:
        await cb.answer("Открытых покупок нет", show_alert=True)
        return
    names = {"spread": "расклад", "report": "разбор", "question": "вопрос"}
    lines = ["🎁 <b>Твои открытые покупки</b>", ""]
    for item in items:
        left = item["qty_total"] - item["qty_used"]
        until = f" · до {item['expires_at'][:10]}" if item["expires_at"] else ""
        lines.append(f"• {names.get(item['kind'], item['kind'])} "
                     f"{item['code'] or ''} ×{left}{until}")
    await cb.message.answer("\n".join(lines), reply_markup=back_menu())
    await cb.answer()
