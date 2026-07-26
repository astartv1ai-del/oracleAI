"""Прямые вызовы Bot API из веб-процесса.

API-процессу нужны три вещи от Telegram: ссылка на оплату для Mini App, возврат
Stars и отправка сообщения клиентке из админки. Тянуть ради этого весь aiogram в
веб-процесс незачем — здесь тонкий HTTP-клиент на три метода.

Валюта XTR (Stars) не требует `provider_token`: цифровые товары в Telegram
продаются только так, это правило платформы.
"""
from __future__ import annotations

import logging

from ..config import settings

log = logging.getLogger("oracle.telegram")

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 20


class TelegramError(Exception):
    """Telegram отклонил запрос."""


async def call(method: str, payload: dict) -> dict:
    import aiohttp

    if not settings.bot_token:
        raise TelegramError("BOT_TOKEN не задан")
    url = API.format(token=settings.bot_token, method=method)
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
    if not data.get("ok"):
        raise TelegramError(data.get("description") or "неизвестная ошибка Telegram")
    return data["result"]


async def create_invoice_link(title: str, description: str, payload: str,
                              amount_stars: int, *, label: str | None = None) -> str:
    """Ссылка на оплату. `payload` — тот же ключ идемпотентности, что и в заказе."""
    if amount_stars <= 0:
        raise TelegramError("цена должна быть больше нуля")
    result = await call("createInvoiceLink", {
        "title": title[:32],                       # ограничения Telegram
        "description": (description or title)[:255],
        "payload": payload,
        "currency": "XTR",
        "prices": [{"label": (label or title)[:32], "amount": amount_stars}],
    })
    if isinstance(result, str):
        return result
    raise TelegramError("Telegram вернул неожиданный ответ")


async def send_message(tg_id: int, text: str, *, html: bool = True) -> bool:
    """Сообщение клиентке (ответ поддержки из панели)."""
    try:
        await call("sendMessage", {
            "chat_id": tg_id,
            "text": text[:4096],
            "parse_mode": "HTML" if html else None,
            "link_preview_options": {"is_disabled": True},
        })
        return True
    except TelegramError as e:
        log.warning("сообщение %s не доставлено: %s", tg_id, e)
        return False


async def refund_star_payment(tg_id: int, charge_id: str) -> bool:
    """Возврат Stars. Без него любой спор пришлось бы решать «на честном слове»."""
    try:
        await call("refundStarPayment",
                   {"user_id": tg_id, "telegram_payment_charge_id": charge_id})
        return True
    except TelegramError as e:
        log.warning("возврат %s для %s не прошёл: %s", charge_id, tg_id, e)
        return False


async def bot_username() -> str:
    """Имя бота — нужно для реферальных ссылок в Mini App."""
    try:
        me = await call("getMe", {})
        return me.get("username", "")
    except TelegramError:
        return ""
