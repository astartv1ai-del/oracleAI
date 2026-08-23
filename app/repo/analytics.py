"""Аналитика: события воронки, временные ряды, удержание, агрегаты для админки.

События пишутся из бота и API через `services.analytics.track`. Здесь только
чтение и запись строк — вся интерпретация в сервисном слое и панели.

Колонка `day` дублирует дату из `created_at` намеренно: группировка по
`substr(created_at,1,10)` не может использовать индекс, и на сотнях тысяч
событий дашборд начинал ощутимо тормозить.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from ..data.session import transaction, utcnow

# Ключевые события воронки — фиксированные имена, чтобы дашборд не разъезжался
# с кодом при опечатке.
E_START = "start"
E_ONBOARD_DONE = "onboard_done"
E_QUESTION = "question"
E_TAROT = "tarot_draw"
E_FORECAST = "forecast_view"
E_LIMIT_HIT = "limit_reached"
E_SHOP_VIEW = "shop_view"
E_INVOICE = "invoice_created"
E_PAID = "payment_success"
E_PROMO = "promo_redeemed"
E_REFERRAL = "referral_joined"
E_MINIAPP_OPEN = "miniapp_open"
E_CHURN_WARN = "expiry_notified"
# Privacy-safe activation/retention milestones. Props for these events must stay
# categorical and never contain user text, memory, birth data or model output.
E_AGE_CONFIRMED = "age_confirmed"
E_FIRST_RITUAL = "first_ritual"
E_FIRST_QUESTION = "first_question"
E_RETURN_D1 = "return_d1"
E_RETURN_D7 = "return_d7"

# Monetization milestones. These names and props are server-owned; clients cannot
# create arbitrary revenue events or attach payment/content data.
E_PAYWALL_VIEW = "paywall_view"
E_PAYWALL_CHOICE = "paywall_choice"
E_CREDIT_PACK_CHECKOUT_STARTED = "credit_pack_checkout_started"
E_CREDIT_PACK_PAID = "credit_pack_paid"
E_CREDIT_SPENT = "credit_spent"
E_CREDIT_BALANCE_LOW = "credit_balance_low"
E_REPORT_DELIVERED = "report_delivered"
E_REFUND_REQUESTED = "refund_requested"
E_REFUND_COMPLETED = "refund_completed"


async def track(db, name: str, tg_id: int | None = None, *,
                props: dict | None = None, surface: str = "bot") -> None:
    now = datetime.now(timezone.utc)
    async with transaction(db):
        await db.execute(
            "INSERT INTO events(tg_id, name, props_json, surface, day, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (tg_id, name, json.dumps(props, ensure_ascii=False) if props else None,
             surface, now.strftime("%Y-%m-%d"), now.isoformat()))


async def track_once(db, name: str, tg_id: int, *,
                     props: dict | None = None, surface: str = "miniapp") -> bool:
    """Записывает milestone только один раз для владельца события.

    SELECT и INSERT выполняются в одной транзакции через aiosqlite connection;
    milestone names не зависят от client-supplied event names и props остаются
    ограниченными вызывающим server-side кодом.
    """
    now = datetime.now(timezone.utc)
    async with transaction(db):
        cur = await db.execute(
            "SELECT 1 FROM events WHERE tg_id=? AND name=? LIMIT 1",
            (tg_id, name),
        )
        if await cur.fetchone():
            return False
        await db.execute(
            "INSERT INTO events(tg_id, name, props_json, surface, day, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (tg_id, name, json.dumps(props, ensure_ascii=False) if props else None,
             surface, now.strftime("%Y-%m-%d"), now.isoformat()),
        )
    return True


async def _scalar(db, sql: str, *args):
    cur = await db.execute(sql, args)
    row = await cur.fetchone()
    return (row[0] if row else 0) or 0


async def prune_analytics(db, days: int = 120) -> int:
    """События и учёт LLM старее окна — в архив некому, только удалять.

    Дашборд считает DAU/WAU и расходы по rolling-окнам, а вот детальный хвост
    за месяцы пользы не несёт и раздувает базу. 120 дней между 90 и 180 из ТЗ.
    """
    before = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    total = 0
    async with transaction(db):
        for table in ("events", "llm_usage"):
            cur = await db.execute(f"DELETE FROM {table} WHERE created_at < ?",
                                   (before,))
            total += cur.rowcount or 0
    return total


def _ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _ago_day(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


async def overview(db) -> dict:
    """Верхние KPI: люди, активность, контент, деньги."""
    return {
        "users_total": await _scalar(db, "SELECT COUNT(*) FROM users"),
        "users_today": await _scalar(
            db, "SELECT COUNT(*) FROM users WHERE created_at>=?", _ago(1)),
        "users_7d": await _scalar(
            db, "SELECT COUNT(*) FROM users WHERE created_at>=?", _ago(7)),
        "users_30d": await _scalar(
            db, "SELECT COUNT(*) FROM users WHERE created_at>=?", _ago(30)),
        "onboarded": await _scalar(db, "SELECT COUNT(*) FROM users WHERE onboarded=1"),
        "subs_active": await _scalar(
            db, "SELECT COUNT(*) FROM users WHERE sub_until>?", utcnow()),
        "dau": await _scalar(
            db, "SELECT COUNT(DISTINCT tg_id) FROM events WHERE day>=?", _ago_day(1)),
        "wau": await _scalar(
            db, "SELECT COUNT(DISTINCT tg_id) FROM events WHERE day>=?", _ago_day(7)),
        "mau": await _scalar(
            db, "SELECT COUNT(DISTINCT tg_id) FROM events WHERE day>=?", _ago_day(30)),
        "questions_today": await _scalar(
            db, "SELECT COUNT(*) FROM messages WHERE is_question=1 AND created_at>=?",
            _ago(1)),
        "questions_7d": await _scalar(
            db, "SELECT COUNT(*) FROM messages WHERE is_question=1 AND created_at>=?",
            _ago(7)),
        "readings_total": await _scalar(db, "SELECT COUNT(*) FROM tarot_readings"),
        "readings_7d": await _scalar(
            db, "SELECT COUNT(*) FROM tarot_readings WHERE created_at>=?", _ago(7)),
        "diary_7d": await _scalar(
            db, "SELECT COUNT(*) FROM diary WHERE created_at>=?", _ago(7)),
        "stars_total": await _scalar(
            db, "SELECT SUM(amount_stars) FROM payments WHERE status='succeeded'"),
        "stars_30d": await _scalar(
            db, "SELECT SUM(amount_stars) FROM payments WHERE status='succeeded' "
                "AND created_at>=?", _ago(30)),
        "payers": await _scalar(
            db, "SELECT COUNT(DISTINCT tg_id) FROM payments WHERE status='succeeded'"),
        "crystals_outstanding": await _scalar(
            db, "SELECT SUM(crystals) FROM users"),
    }


async def activation_funnel(db, days: int = 30) -> dict:
    """Privacy-safe Mini App activation/return funnel by first-open cohort."""
    since = _ago(days)
    cohort_sql = (
        "SELECT DISTINCT tg_id FROM events "
        "WHERE name=? AND tg_id IS NOT NULL AND created_at>=?"
    )
    cohort = await _scalar(db, f"SELECT COUNT(*) FROM ({cohort_sql})", E_MINIAPP_OPEN, since)
    names = [
        ("age_gate", E_AGE_CONFIRMED),
        ("first_ritual", E_FIRST_RITUAL),
        ("first_question", E_FIRST_QUESTION),
        ("d1_return", E_RETURN_D1),
        ("d7_return", E_RETURN_D7),
    ]
    steps = []
    for label, event_name in names:
        value = await _scalar(
            db,
            "SELECT COUNT(DISTINCT tg_id) FROM events WHERE name=? "
            "AND tg_id IN (" + cohort_sql + ")",
            event_name, E_MINIAPP_OPEN, since,
        )
        steps.append({
            "step": label,
            "event": event_name,
            "value": value,
            "of_cohort": round(value * 100 / cohort, 1) if cohort else 0.0,
        })
    return {"days": days, "cohort": cohort, "steps": steps}


async def funnel(db, days: int = 30) -> list[dict]:
    """Воронка: пришла → прошла онбординг → задала вопрос → вернулась → заплатила.

    Считаем по пользователям, зарегистрированным в окне: иначе «заплатившие»
    прошлого года завышали бы конверсию свежего трафика.
    """
    since = _ago(days)
    total = await _scalar(db, "SELECT COUNT(*) FROM users WHERE created_at>=?", since)
    onboarded = await _scalar(
        db, "SELECT COUNT(*) FROM users WHERE created_at>=? AND onboarded=1", since)
    asked = await _scalar(
        db, "SELECT COUNT(DISTINCT m.tg_id) FROM messages m JOIN users u "
            "ON u.tg_id=m.tg_id WHERE u.created_at>=? AND m.is_question=1", since)
    retained = await _scalar(
        db, "SELECT COUNT(*) FROM (SELECT m.tg_id FROM messages m JOIN users u "
            "ON u.tg_id=m.tg_id WHERE u.created_at>=? AND m.is_question=1 "
            "GROUP BY m.tg_id HAVING COUNT(DISTINCT substr(m.created_at,1,10)) >= 2)",
        since)
    paid = await _scalar(
        db, "SELECT COUNT(DISTINCT p.tg_id) FROM payments p JOIN users u "
            "ON u.tg_id=p.tg_id WHERE u.created_at>=? AND p.status='succeeded'", since)

    steps = [("Пришли", total), ("Прошли знакомство", onboarded),
             ("Задали вопрос", asked), ("Вернулись на 2-й день", retained),
             ("Заплатили", paid)]
    out = []
    for title, value in steps:
        out.append({
            "step": title,
            "value": value,
            "of_total": round(value * 100 / total, 1) if total else 0.0,
        })
    return out


async def timeseries(db, days: int = 30) -> list[dict]:
    """Ряды по дням для графиков: регистрации, вопросы, расклады, Stars."""
    start = (date.today() - timedelta(days=days - 1)).isoformat()

    async def by_day(sql: str, *args) -> dict:
        cur = await db.execute(sql, args)
        return {r[0]: r[1] for r in await cur.fetchall()}

    users = await by_day(
        "SELECT substr(created_at,1,10) d, COUNT(*) FROM users "
        "WHERE substr(created_at,1,10)>=? GROUP BY d", start)
    questions = await by_day(
        "SELECT substr(created_at,1,10) d, COUNT(*) FROM messages "
        "WHERE is_question=1 AND substr(created_at,1,10)>=? GROUP BY d", start)
    readings = await by_day(
        "SELECT substr(created_at,1,10) d, COUNT(*) FROM tarot_readings "
        "WHERE substr(created_at,1,10)>=? GROUP BY d", start)
    stars = await by_day(
        "SELECT substr(created_at,1,10) d, SUM(amount_stars) FROM payments "
        "WHERE status='succeeded' AND substr(created_at,1,10)>=? GROUP BY d", start)
    active = await by_day(
        "SELECT day d, COUNT(DISTINCT tg_id) FROM events WHERE day>=? GROUP BY day",
        start)
    promos = await by_day(
        "SELECT substr(created_at,1,10) d, COUNT(*) FROM promo_redemptions "
        "WHERE substr(created_at,1,10)>=? GROUP BY d", start)

    out = []
    for i in range(days):
        day = (date.today() - timedelta(days=days - 1 - i)).isoformat()
        out.append({"day": day,
                    "users": users.get(day, 0),
                    "questions": questions.get(day, 0),
                    "readings": readings.get(day, 0),
                    "stars": stars.get(day, 0) or 0,
                    "promos": promos.get(day, 0),
                    "active": active.get(day, 0)})
    return out


async def retention(db, cohort_days: int = 7) -> list[dict]:
    """Удержание по недельным когортам: доля вернувшихся на день 1/3/7/14/30."""
    out = []
    for week in range(cohort_days):
        start = (date.today() - timedelta(days=(week + 1) * 7)).isoformat()
        end = (date.today() - timedelta(days=week * 7)).isoformat()
        size = await _scalar(
            db, "SELECT COUNT(*) FROM users WHERE substr(created_at,1,10)>=? "
                "AND substr(created_at,1,10)<?", start, end)
        if not size:
            continue
        row = {"cohort": start, "size": size}
        for day_n in (1, 3, 7, 14, 30):
            back = await _scalar(
                db,
                "SELECT COUNT(DISTINCT u.tg_id) FROM users u JOIN events e "
                "ON e.tg_id=u.tg_id WHERE substr(u.created_at,1,10)>=? "
                "AND substr(u.created_at,1,10)<? "
                "AND julianday(e.created_at) - julianday(u.created_at) BETWEEN ? AND ?",
                start, end, day_n, day_n + 1)
            row[f"d{day_n}"] = round(back * 100 / size, 1)
        out.append(row)
    return out


async def top_events(db, days: int = 7, limit: int = 25) -> list[dict]:
    cur = await db.execute(
        "SELECT name, COUNT(*) n, COUNT(DISTINCT tg_id) users FROM events "
        "WHERE created_at>=? GROUP BY name ORDER BY n DESC LIMIT ?", (_ago(days), limit))
    return [dict(r) for r in await cur.fetchall()]


async def surface_split(db, days: int = 30) -> list[dict]:
    """Где живёт активность — в боте или в Mini App. Решает, куда вкладываться."""
    cur = await db.execute(
        "SELECT COALESCE(surface,'bot') surface, COUNT(*) n, COUNT(DISTINCT tg_id) users "
        "FROM events WHERE created_at>=? GROUP BY surface ORDER BY n DESC",
        (_ago(days),))
    return [dict(r) for r in await cur.fetchall()]


async def user_events(db, tg_id: int, limit: int = 100) -> list[dict]:
    cur = await db.execute(
        "SELECT name, props_json, surface, created_at FROM events WHERE tg_id=? "
        "ORDER BY id DESC LIMIT ?", (tg_id, limit))
    return [dict(r) for r in await cur.fetchall()]


async def source_split(db, days: int = 30) -> list[dict]:
    """Каналы привлечения: сколько пришло и сколько из них заплатило."""
    cur = await db.execute(
        "SELECT COALESCE(source,'organic') source, COUNT(*) users, "
        "SUM(CASE WHEN ltv_stars > 0 THEN 1 ELSE 0 END) payers, "
        "COALESCE(SUM(ltv_stars),0) stars FROM users WHERE created_at>=? "
        "GROUP BY source ORDER BY users DESC", (_ago(days),))
    return [dict(r) for r in await cur.fetchall()]


# ─────────────────────── себестоимость и безопасность ────────────────────────

async def llm_costs(db, days: int = 30) -> dict:
    """Сколько стоит продукт в токенах.

    Вся юнит-экономика построена на цифре «≤ $2.5 на платящую в месяц» — без
    этого запроса она остаётся предположением. `per_paying` считаем от числа
    активных подписок: именно они окупают всех остальных.
    """
    since = _ago(days)
    total_cost = await _scalar(
        db, "SELECT SUM(cost_usd) FROM llm_usage WHERE created_at>=?", since)
    calls = await _scalar(
        db, "SELECT COUNT(*) FROM llm_usage WHERE created_at>=?", since)
    failed = await _scalar(
        db, "SELECT COUNT(*) FROM llm_usage WHERE ok=0 AND created_at>=?", since)
    subs = await _scalar(
        db, "SELECT COUNT(*) FROM users WHERE sub_until>?", utcnow())

    cur = await db.execute(
        "SELECT purpose, COUNT(*) calls, COALESCE(SUM(prompt_tokens),0) tokens_in, "
        "COALESCE(SUM(completion_tokens),0) tokens_out, "
        "COALESCE(SUM(cost_usd),0) cost, "
        "COALESCE(AVG(latency_ms),0) avg_ms FROM llm_usage "
        "WHERE created_at>=? GROUP BY purpose ORDER BY cost DESC", (since,))
    by_purpose = [dict(r) for r in await cur.fetchall()]

    cur = await db.execute(
        "SELECT provider, model, COUNT(*) calls, COALESCE(SUM(cost_usd),0) cost "
        "FROM llm_usage WHERE created_at>=? GROUP BY provider, model "
        "ORDER BY cost DESC LIMIT 10", (since,))
    by_model = [dict(r) for r in await cur.fetchall()]

    return {
        "days": days,
        "cost_usd": round(total_cost, 4),
        "calls": calls,
        "failed": failed,
        "fail_rate": round(failed * 100 / calls, 1) if calls else 0.0,
        "per_paying_usd": round(total_cost / subs, 3) if subs else 0.0,
        "by_purpose": by_purpose,
        "by_model": by_model,
    }


async def monetization_kpis(db, days: int = 30) -> dict:
    """Revenue/cost KPI block with an explicit no-fabrication net boundary.

    Stars are reported in their native unit. Net revenue and contribution margin
    stay unavailable until settlement/tax/refund assumptions are reviewed; a
    gross number must never be presented as profit.
    """
    since = _ago(days)
    gross_stars = await _scalar(
        db, "SELECT SUM(amount_stars) FROM payments "
        "WHERE status='succeeded' AND created_at>=?", since)
    payers = await _scalar(
        db, "SELECT COUNT(DISTINCT tg_id) FROM payments "
        "WHERE status='succeeded' AND created_at>=?", since)
    paid_orders = await _scalar(
        db, "SELECT COUNT(*) FROM orders WHERE status='paid' AND paid_at>=?", since)
    refunded_orders = await _scalar(
        db, "SELECT COUNT(*) FROM orders WHERE status='refunded' AND created_at>=?", since)
    repeat_payers = await _scalar(
        db, "SELECT COUNT(*) FROM (SELECT tg_id FROM payments "
        "WHERE status='succeeded' AND created_at>=? GROUP BY tg_id HAVING COUNT(*)>=2)",
        since,
    )

    async def event_count(name: str) -> int:
        return await _scalar(db, "SELECT COUNT(*) FROM events WHERE name=? AND created_at>=?", name, since)

    by_sku_cur = await db.execute(
        "SELECT COALESCE(sku, kind) sku, COUNT(*) orders, "
        "COUNT(DISTINCT tg_id) payers, COALESCE(SUM(amount_stars),0) gross_stars "
        "FROM orders WHERE status='paid' AND paid_at>=? "
        "GROUP BY COALESCE(sku, kind) ORDER BY gross_stars DESC, orders DESC", (since,))
    by_sku = [dict(row) for row in await by_sku_cur.fetchall()]

    cost_cur = await db.execute(
        "SELECT purpose, provider, model, COUNT(*) calls, "
        "COALESCE(SUM(cost_usd),0) cost_usd, "
        "COALESCE(AVG(latency_ms),0) avg_latency_ms "
        "FROM llm_usage WHERE created_at>=? GROUP BY purpose, provider, model "
        "ORDER BY cost_usd DESC", (since,))
    provider_cost = [dict(row) for row in await cost_cur.fetchall()]
    llm_cost = await _scalar(
        db, "SELECT SUM(cost_usd) FROM llm_usage WHERE created_at>=?", since)

    return {
        "days": days,
        "status": "estimated_requires_settlement_inputs",
        "gross_booking_stars": int(gross_stars),
        "paid_orders": int(paid_orders),
        "paid_payers": int(payers),
        "paid_arppu_stars": round(gross_stars / payers, 2) if payers else 0.0,
        "repeat_payers": int(repeat_payers),
        "repeat_payer_rate": round(repeat_payers * 100 / payers, 1) if payers else 0.0,
        "refund_orders": int(refunded_orders),
        "refund_rate": round(refunded_orders * 100 / paid_orders, 1) if paid_orders else 0.0,
        "credit_pack_checkout_started": await event_count(E_CREDIT_PACK_CHECKOUT_STARTED),
        "credit_pack_paid": await event_count(E_CREDIT_PACK_PAID),
        "credit_spent": await event_count(E_CREDIT_SPENT),
        "reports_delivered": await event_count(E_REPORT_DELIVERED),
        "llm_variable_cost_usd": round(float(llm_cost), 6),
        "net_revenue_estimate": None,
        "contribution_margin_estimate": None,
        "required_inputs": [
            "effective_platform_realization", "tax_and_withholding_rate",
            "refund_rate_by_channel", "voice_tool_cost", "support_referral_cost",
            "fixed_opex", "paid_marketing",
        ],
        "by_sku": by_sku,
        "provider_cost_by_purpose": provider_cost,
    }


async def safety_events(db, days: int = 30, limit: int = 100) -> dict:
    """Срабатывания кризисного протокола: сводка и последние обращения.

    Это не метрика роста — это то, что нужно перечитывать глазами: по ней
    настраивается фильтр и видно, не блокирует ли он обычные вопросы.
    """
    since = _ago(days)
    cur = await db.execute(
        "SELECT category, action, COUNT(*) n FROM safety_events "
        "WHERE created_at>=? GROUP BY category, action ORDER BY n DESC", (since,))
    summary = [dict(r) for r in await cur.fetchall()]
    cur = await db.execute(
        "SELECT s.tg_id, s.category, s.action, s.excerpt, s.created_at, u.name "
        "FROM safety_events s LEFT JOIN users u ON u.tg_id = s.tg_id "
        "WHERE s.created_at>=? ORDER BY s.id DESC LIMIT ?", (since, limit))
    return {"summary": summary,
            "recent": [dict(r) for r in await cur.fetchall()]}


async def rollup_day(db, day: str | None = None) -> dict:
    """Складывает снимок метрик за день в `daily_stats` — история не зависит от
    того, что старые события когда-нибудь подчистят ретеншеном."""
    day = day or date.today().isoformat()
    stats = {
        "users_new": await _scalar(
            db, "SELECT COUNT(*) FROM users WHERE substr(created_at,1,10)=?", day),
        "active": await _scalar(
            db, "SELECT COUNT(DISTINCT tg_id) FROM events WHERE day=?", day),
        "questions": await _scalar(
            db, "SELECT COUNT(*) FROM messages WHERE is_question=1 "
                "AND substr(created_at,1,10)=?", day),
        "readings": await _scalar(
            db, "SELECT COUNT(*) FROM tarot_readings WHERE substr(created_at,1,10)=?",
            day),
        "stars": await _scalar(
            db, "SELECT SUM(amount_stars) FROM payments WHERE status='succeeded' "
                "AND substr(created_at,1,10)=?", day),
        "orders": await _scalar(
            db, "SELECT COUNT(*) FROM orders WHERE status='paid' "
                "AND substr(paid_at,1,10)=?", day),
    }
    async with transaction(db):
        await db.execute(
            "INSERT OR REPLACE INTO daily_stats(day, stats_json, updated_at) "
            "VALUES(?,?,?)", (day, json.dumps(stats, ensure_ascii=False), utcnow()))
    return stats
