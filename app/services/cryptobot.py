"""Клиент Crypto Pay (@CryptoBot) — приём крипты без юрлица и KYC.

Поток тот же, что у Stars: заказ с уникальным payload создаётся до оплаты,
payload уезжает в инвойс, подтверждение приходит вебхуком — и выдача идёт через
тот же `services.billing.apply_payment`. Отличие одно: вебхук надо один раз
прописать руками в @CryptoBot → Crypto Pay → Create App → Webhook URL.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from urllib.parse import quote

import aiohttp

from ..config import settings

log = logging.getLogger("oracle.cryptobot")

API = "https://pay.crypt.bot/api/"


class CryptoPayError(RuntimeError):
    """Crypto Pay недоступен или вернул некорректный ответ."""


def verify_webhook(raw: bytes, header: str | None) -> bool:
    """Подпись Crypto Pay: HMAC-SHA256 тела ключом API-токена приложения."""
    secret = settings.cryptobot_api_token
    if not secret or not header:
        return False
    calc = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(calc, header.strip())


async def _call(method: str, payload: dict) -> dict:
    if not settings.cryptobot_api_token:
        raise CryptoPayError("CRYPTOBOT_API_TOKEN не задан")
    headers = {
        "Authorization": f"Bearer {settings.cryptobot_api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{API}{method}", headers=headers,
                                    json=payload) as response:
                if response.status >= 400:
                    raise CryptoPayError(
                        f"Crypto Pay вернул HTTP {response.status}")
                body = await response.text()
    except CryptoPayError:
        raise
    except (aiohttp.ClientError, TimeoutError) as exc:
        raise CryptoPayError("Crypto Pay временно недоступен") from exc
    try:
        data = json.loads(body)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CryptoPayError("Crypto Pay вернул некорректный ответ") from exc
    if not data.get("ok"):
        raise CryptoPayError(str(data.get("error") or "неизвестная ошибка"))
    return data.get("result") or {}


async def create_invoice(*, amount_usd: float, payload: str,
                         description: str) -> dict:
    """Инвойс в USD — пользователь платит любой монетой по курсу Crypto Bot."""
    result = await _call("createInvoice", {
        "currency_type": "fiat",
        "fiat": "USD",
        "amount": f"{amount_usd:.2f}",
        "description": description[:1024],
        "payload": payload[:4096],
        # одноразовый инвойс: оплачен — больше не открывается
        "allow_anonymous": False,
    })
    pay_url = str(result.get("pay_url") or "")
    invoice_id = result.get("invoice_id")
    if not pay_url or not invoice_id:
        raise CryptoPayError("Crypto Pay не вернул invoice_id/pay_url")
    return {"invoice_id": int(invoice_id), "link": pay_url,
            "bot": settings.cryptobot_app_name and
                   quote(settings.cryptobot_app_name, safe="")}


async def get_invoice(invoice_id: int) -> dict | None:
    """Статус инвойса — для ручного перепровера и тестов."""
    result = await _call("getInvoices", {
        "invoice_ids": str(invoice_id), "status": "all"})
    items = result.get("items") or []
    return items[0] if items else None
