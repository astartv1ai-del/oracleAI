"""Совместимый фасад над слоем данных.

Исторически весь SQL жил в этом файле. Сейчас структура БД описана в
`app/data/`, запросы — в `app/repo/`, правила продукта — в `app/services/`.
Модуль оставлен намеренно: он даёт короткие имена для самых частых операций и
не ломает внешние точки входа (скрипты, миграционные утилиты), которые уже
ссылались на `app.db`.

Новый код пишем напрямую к репозиториям и сервисам — там богаче API
(сегменты, права доступа, транзакции). Здесь только делегирование.
"""
from __future__ import annotations

from .data.session import connect, healthcheck, transaction, utcnow  # noqa: F401
from .repo import billing, dialog, growth, readings, users
from .repo.analytics import overview
from .services import billing as billing_svc
from .services import limits as limits_svc

# ---------------------------------------------------------------- users

get_user = users.get
update_user = users.update
sub_active = users.sub_active
user_today = users.user_today
touch = users.touch


async def ensure_user(db, tg_id: int, name: str | None = None,
                      username: str | None = None):
    return await users.ensure(db, tg_id, name, username)


# ---------------------------------------------------------------- лимиты

questions_left = limits_svc.questions_left


async def questions_today(db, user) -> int:
    return await dialog.questions_used_today(db, user)


# ---------------------------------------------------------------- кристаллы

add_crystals = billing.add_crystals
spend_crystals = billing.spend_crystals

# ---------------------------------------------------------------- диалог

save_message = dialog.save_message
recent_messages = dialog.history
save_memory = dialog.save_memory
get_memories = dialog.get_memories
add_diary = dialog.add_diary
get_diary = dialog.get_diary
diary_streak = dialog.diary_streak

# ---------------------------------------------------------------- прогнозы и таро

get_forecast = readings.get_forecast
save_forecast = readings.save_forecast
get_reading = readings.get_reading
finish_reading = readings.finish_reading
recent_readings = readings.recent_readings


async def start_reading(db, tg_id: int, question: str, cards: list,
                        spread: str = "") -> int:
    return await readings.start_reading(db, tg_id, spread, question, cards)


async def save_reading(db, tg_id: int, question: str, cards: list, answer: str,
                       spread: str = "") -> int:
    return await readings.save_reading(db, tg_id, spread, question, cards, answer)


# ---------------------------------------------------------------- рост

async def apply_referral(db, tg_id: int, ref_id: int, bonus: int = 0) -> bool:
    """Сохранён для совместимости; бонусы считает `services.referrals`."""
    from .services import referrals
    return bool(await referrals.apply(db, tg_id, ref_id))


async def use_promo(db, code: str, tg_id: int) -> int | None:
    """Активирует промокод. Возвращает число дней доступа или None.

    Промокод теперь может выдавать не только дни (ещё Кристаллы и товары),
    поэтому полный результат отдаёт `services.billing.redeem_promo`.
    """
    result = await billing_svc.redeem_promo(db, tg_id, code)
    if not result:
        return None
    granted = result.get("granted") or {}
    return granted.get("days") or result.get("days") or 0


# ---------------------------------------------------------------- статистика

async def stats(db) -> dict:
    """Короткая сводка для /stats в боте."""
    data = await overview(db)
    return {
        "users": data["users_total"],
        "onboarded": data["onboarded"],
        "active_7d": data["wau"],
        "questions_7d": data["questions_7d"],
        "readings": data["readings_total"],
        "subs_active": data["subs_active"],
        "stars_total": data["stars_total"],
        "payers": data["payers"],
        "crystals_bought": data["stars_total"],
        "promo_used": await _promo_used(db),
    }


async def _promo_used(db) -> int:
    codes = await growth.batch_stats(db)
    return sum(item["used"] or 0 for item in codes)
