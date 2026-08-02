"""Лимиты вопросов: сколько осталось, чем можно доплатить, что списать.

Лимит — центральная механика монетизации («дефицит как ценность»), поэтому
решение «пустить или нет» собрано в одном месте, а не размазано по хендлерам.

Порядок источников доступа, от бесплатного к платному:
    1. уточнение к предыдущему вопросу (окно 10 минут) — не тратит ничего;
    2. дневной/недельный лимит тарифа;
    3. купленное право `question` (пакеты «+1 вопрос», «+5 вопросов»);
    4. Кристаллы ✦ (экстренный расклад вне лимита).

Порядок именно такой: сначала то, за что клиентка уже заплатила подпиской, и
только потом разовые покупки — иначе купленные вопросы сгорали бы раньше
включённых в тариф.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ..repo import billing, content, dialog, users

# Сколько уточнений подряд считаются частью того же вопроса.
FOLLOWUP_MAX = 2


@dataclass
class Allowance:
    plan: dict
    limit: int
    used: int
    period: str                 # day | week | none
    extra_questions: int = 0    # купленные права
    crystals: int = 0
    emergency_cost: int = 20
    followup: bool = False      # текущий вопрос — уточнение, лимит не тратит
    features: list = field(default_factory=list)

    @property
    def left(self) -> int:
        return max(0, self.limit - self.used)

    @property
    def can_ask_free(self) -> bool:
        return self.followup or self.left > 0

    @property
    def can_ask_paid(self) -> bool:
        return self.extra_questions > 0 or self.crystals >= self.emergency_cost

    def as_dict(self) -> dict:
        return {
            "plan": self.plan.get("code"),
            "plan_title": self.plan.get("title"),
            "limit": self.limit,
            "used": self.used,
            "left": self.left,
            "period": self.period,
            "extra_questions": self.extra_questions,
            "crystals": self.crystals,
            "emergency_cost": self.emergency_cost,
            "can_ask": self.can_ask_free or self.can_ask_paid,
        }


async def active_plan(db, user) -> dict:
    """Тариф, который действует прямо сейчас.

    Истёкшая подписка не удаляет `sub_level` из профиля (он нужен, чтобы понимать,
    что продлевать), поэтому уровень пересчитывается по сроку, а не по колонке.
    """
    if not users.sub_active(user):
        return await billing.get_plan(db, "free")
    return await billing.get_plan(db, user["sub_level"] or "free")


async def _is_followup(db, user) -> bool:
    """Уточнение к только что заданному вопросу.

    Иначе диалог получался неестественным: клиентка спрашивала «а что это
    значит?» — и теряла второй вопрос из трёх.
    """
    window = await content.get_setting(db, "limits.followup_window_minutes", 10)
    try:
        window = int(window)
    except (TypeError, ValueError):
        window = 10
    if window <= 0:
        return False
    last = await dialog.last_question_at(db, user["tg_id"])
    if not last:
        return False
    try:
        last_dt = datetime.fromisoformat(last)
    except ValueError:
        return False
    if datetime.now(timezone.utc) - last_dt > timedelta(minutes=window):
        return False
    # сколько уточнений уже было после последнего «платного» вопроса
    used = await dialog.followups_since(db, user["tg_id"], last)
    return used < FOLLOWUP_MAX


async def allowance(db, user, *, check_followup: bool = True) -> Allowance:
    plan = await active_plan(db, user)
    daily = plan.get("daily_questions") or 0
    weekly = plan.get("weekly_questions") or 0

    if daily > 0:
        period, limit = "day", daily
        used = await dialog.questions_used_today(db, user)
    elif weekly > 0:
        period, limit = "week", weekly
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        used = await dialog.questions_used_since(db, user["tg_id"], since)
    else:
        period, limit, used = "none", 0, 0

    cost = await content.get_setting(db, "limits.emergency_cost", 20)
    # Бесплатное уточнение — продолжение вопроса, за который лимит уже уплачен.
    # Когда лимит исчерпан, уточнять «бесплатно» нельзя: иначе одна фраза «а что
    # это значит?» открывала бы неограниченный доступ в обход тарифа и покупок.
    followup = False
    if check_followup and limit - used > 0:
        followup = await _is_followup(db, user)
    return Allowance(
        plan=plan, limit=limit, used=used, period=period,
        extra_questions=await billing.available_entitlements(
            db, user["tg_id"], "question"),
        crystals=user["crystals"] or 0,
        emergency_cost=int(cost or 20),
        followup=followup,
        features=plan.get("features") or [],
    )


async def questions_left(db, user) -> int:
    """Совместимость со старым API: остаток по тарифу без учёта покупок."""
    return (await allowance(db, user)).left


#: Источники доступа. Код списания однозначен, потому что от него зависит, что
#: именно уменьшать — иначе купленный расклад мог бы съесть купленный вопрос.
FOLLOWUP = "followup"
PLAN = "plan"
ENT_QUESTION = "ent_question"
ENT_SPREAD = "ent_spread"
CRYSTALS = "crystals"
DENIED = "denied"


@dataclass
class Verdict:
    allowed: bool
    charge: str
    reason: str = ""
    allowance: Allowance | None = None
    code: str | None = None      # код расклада/отчёта для ENT_SPREAD


async def check(db, user) -> Verdict:
    """Можно ли задать вопрос и за счёт чего — без списания."""
    a = await allowance(db, user)
    if not users.sub_active(user) and a.limit == 0 and not a.can_ask_paid:
        return Verdict(False, DENIED, "sub_over", a)
    if a.followup:
        return Verdict(True, FOLLOWUP, allowance=a)
    if a.left > 0:
        return Verdict(True, PLAN, allowance=a)
    if a.extra_questions > 0:
        return Verdict(True, ENT_QUESTION, allowance=a)
    if a.crystals >= a.emergency_cost:
        return Verdict(True, CRYSTALS, "needs_confirm", a)
    return Verdict(False, DENIED, "limit_reached", a)


async def consume(db, user, verdict: Verdict) -> bool:
    """Списывает то, что решил `check`. Возвращает False, если списать не удалось.

    Ответ выдаётся ТОЛЬКО после успешного списания: иначе при гонке двух
    устройств клиентка получала два ответа, заплатив за один.
    """
    if verdict.charge in (FOLLOWUP, PLAN):
        return True            # лимит тарифа считается по сообщениям, не счётчиком
    if verdict.charge == ENT_QUESTION:
        return await billing.consume_entitlement(db, user["tg_id"], "question")
    if verdict.charge == ENT_SPREAD:
        return await billing.consume_entitlement(
            db, user["tg_id"], "spread", verdict.code)
    if verdict.charge == CRYSTALS:
        cost = verdict.allowance.emergency_cost if verdict.allowance else 20
        return await billing.spend_crystals(
            db, user["tg_id"], cost, "emergency_question")
    return False


def counts_toward_limit(verdict: Verdict) -> bool:
    """Помечать ли сообщение как «вопрос» (то есть тратить лимит тарифа)."""
    return verdict.charge == PLAN


#: Как называется источник оплаты в истории раскладов (`tarot_readings.paid_with`).
PAID_WITH = {FOLLOWUP: "daily", PLAN: "daily", ENT_QUESTION: "entitlement",
             ENT_SPREAD: "entitlement", CRYSTALS: "crystals"}


# ───────────────────────── доступ к раскладам ────────────────────────────────

async def spread_access(db, user, spread_code: str) -> Verdict:
    """Доступ к конкретному раскладу.

    Расклад открывается тремя путями: входит в тариф (тратит вопрос дня), куплен
    разово (право `spread`) или оплачен Кристаллами. Купленное право проверяем
    первым — за него заплатили именно за этот расклад, и оно имеет срок.
    """
    if await billing.available_entitlements(db, user["tg_id"], "spread", spread_code):
        return Verdict(True, ENT_SPREAD, allowance=await allowance(db, user),
                       code=spread_code)
    return await check(db, user)
