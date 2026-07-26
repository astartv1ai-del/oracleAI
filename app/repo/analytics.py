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


async def track(db, name: str, tg_id: int | None = None, *,
                props: dict | None = None, surface: str = "bot") -> None:
    now = datetime.now(timezone.utc)
    async with transaction(db):
        await db.execute(
            "INSERT INTO events(tg_id, name, props_json, surface, day, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (tg_id, name, json.dumps(props, ensure_ascii=False) if props else None,
             surface, now.strftime("%Y-%m-%d"), now.isoformat()))


async def _scalar(db, sql: str, *args):
    cur = await db.execute(sql, args)
    row = await cur.fetchone()
    return (row[0] if row else 0) or 0


def _ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


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
            db, "SELECT COUNT(DISTINCT tg_id) FROM events WHERE created_at>=?", _ago(1)),
        "wau": await _scalar(
            db, "SELECT COUNT(DISTINCT tg_id) FROM events WHERE created_at>=?", _ago(7)),
        "mau": await _scalar(
            db, "SELECT COUNT(DISTINCT tg_id) FROM events WHERE created_at>=?", _ago(30)),
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

    out = []
    for i in range(days):
        day = (date.today() - timedelta(days=days - 1 - i)).isoformat()
        out.append({"day": day,
                    "users": users.get(day, 0),
                    "questions": questions.get(day, 0),
                    "readings": readings.get(day, 0),
                    "stars": stars.get(day, 0) or 0,
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
