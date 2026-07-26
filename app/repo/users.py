"""Пользователи: создание, профиль, тарифный уровень, сегменты для CRM."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..config import settings
from ..data.session import transaction, utcnow

DEFAULT_TZ = "Europe/Moscow"

# Колонки, которые разрешено писать через update(): защита от опечатки в имени
# поля, которая иначе молча улетела бы в SQL и уронила запрос на живом трафике.
WRITABLE = {
    "name", "username", "lang", "persona", "oracle_name", "tz",
    "birth_date", "birth_time", "birth_time_known", "birth_city",
    "birth_lat", "birth_lon", "chart_json",
    "sub_level", "sub_until", "crystals",
    "onboarded", "morning_push", "ref_by", "goal", "source", "status",
    "ltv_stars", "expiry_notified", "last_seen", "deleted_at",
}


async def get(db, tg_id: int):
    cur = await db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
    return await cur.fetchone()


async def by_username(db, username: str):
    cur = await db.execute(
        "SELECT * FROM users WHERE lower(username)=lower(?)",
        (username.lstrip("@"),))
    return await cur.fetchone()


async def ensure(db, tg_id: int, name: str | None = None,
                 username: str | None = None, source: str | None = None):
    """Создаёт пользователя с триалом и стартовыми Кристаллами (однократно)."""
    user = await get(db, tg_id)
    if user:
        if username and user["username"] != username:
            await update(db, tg_id, username=username)
            return await get(db, tg_id)
        return user

    trial_days = settings.trial_days
    crystals = settings.crystals_start
    sub_until = (datetime.now(timezone.utc) + timedelta(days=trial_days)).isoformat()
    async with transaction(db):
        await db.execute(
            "INSERT INTO users(tg_id, name, username, sub_level, sub_until, crystals, "
            "source, created_at) VALUES(?,?,?,'trial',?,?,?,?)",
            (tg_id, name, username, sub_until, crystals, source, utcnow()))
        await db.execute(
            "INSERT INTO crystal_ledger(tg_id, delta, reason, balance, created_at) "
            "VALUES(?,?,'welcome',?,?)", (tg_id, crystals, crystals, utcnow()))
    return await get(db, tg_id)


async def update(db, tg_id: int, **fields) -> None:
    unknown = set(fields) - WRITABLE
    if unknown:
        raise ValueError(f"нельзя писать в колонки users: {', '.join(sorted(unknown))}")
    if not fields:
        return
    keys = ", ".join(f"{k}=?" for k in fields)
    async with transaction(db):
        await db.execute(f"UPDATE users SET {keys} WHERE tg_id=?",
                         (*fields.values(), tg_id))


async def touch(db, tg_id: int) -> None:
    async with transaction(db):
        await db.execute("UPDATE users SET last_seen=? WHERE tg_id=?", (utcnow(), tg_id))


# ─────────────────────────── подписка и тариф ────────────────────────────────

def sub_active(user) -> bool:
    """Живая ли подписка. Пустой/битый `sub_until` трактуем как «нет доступа»."""
    if not user or not user["sub_until"]:
        return False
    try:
        return datetime.fromisoformat(user["sub_until"]) > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False


def sub_days_left(user) -> int:
    if not sub_active(user):
        return 0
    until = datetime.fromisoformat(user["sub_until"])
    return max(0, (until - datetime.now(timezone.utc)).days)


def user_tz(user) -> ZoneInfo:
    """Таймзона клиентки. Битое значение из БД не должно ломать расчёт дня."""
    try:
        return ZoneInfo(user["tz"] or DEFAULT_TZ)
    except Exception:  # noqa: BLE001
        return ZoneInfo(DEFAULT_TZ)


def user_today(user) -> str:
    return datetime.now(user_tz(user)).strftime("%Y-%m-%d")


def day_start_utc(user) -> str:
    """Начало сегодняшних суток клиентки в UTC — для оконных запросов."""
    local = datetime.now(user_tz(user)).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return local.astimezone(timezone.utc).isoformat()


async def extend_subscription(db, tg_id: int, plan_code: str, days: int) -> str:
    """Продлевает подписку от максимума (сейчас, текущий конец) — оплата не сгорает."""
    user = await get(db, tg_id)
    base = datetime.now(timezone.utc)
    if user and user["sub_until"]:
        try:
            base = max(base, datetime.fromisoformat(user["sub_until"]))
        except (TypeError, ValueError):
            pass
    until = (base + timedelta(days=days)).isoformat()
    async with transaction(db):
        await db.execute(
            "UPDATE users SET sub_until=?, sub_level=?, expiry_notified=0 WHERE tg_id=?",
            (until, plan_code, tg_id))
    return until


async def set_status(db, tg_id: int, status: str) -> None:
    await update(db, tg_id, status=status)


async def anonymize(db, tg_id: int) -> None:
    """«Удали мои данные»: чистим PII и историю, счётчики платежей оставляем.

    Строку не удаляем: на неё ссылаются заказы и платежи, а финансовая история
    должна оставаться сводимой. Персональные данные при этом стираются.
    """
    async with transaction(db):
        await db.execute(
            "UPDATE users SET name='удалено', username=NULL, birth_date=NULL, "
            "birth_time=NULL, birth_city=NULL, birth_lat=NULL, birth_lon=NULL, "
            "chart_json=NULL, goal=NULL, status='deleted', deleted_at=?, "
            "onboarded=0 WHERE tg_id=?", (utcnow(), tg_id))
        for table in ("messages", "memories", "diary", "forecasts",
                      "tarot_readings", "partners", "synastry_cache",
                      "reports", "threads", "user_notes"):
            await db.execute(f"DELETE FROM {table} WHERE tg_id=?", (tg_id,))


# ─────────────────────────── выборки и сегменты ──────────────────────────────

SEGMENTS = {
    "all": "1=1",
    "active_sub": "sub_until > :now",
    "expired": "(sub_until IS NULL OR sub_until <= :now)",
    "onboarded": "onboarded = 1",
    "not_onboarded": "onboarded = 0",
    "paying": "ltv_stars > 0",
    "never_paid": "ltv_stars = 0",
    "push_on": "morning_push = 1",
    "active_7d": "last_seen >= :week_ago",
    "sleeping_14d": "(last_seen IS NULL OR last_seen < :two_weeks_ago)",
    "expiring_3d": "sub_until > :now AND sub_until <= :in_3d",
}


def _segment_params() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "now": now.isoformat(),
        "week_ago": (now - timedelta(days=7)).isoformat(),
        "two_weeks_ago": (now - timedelta(days=14)).isoformat(),
        "in_3d": (now + timedelta(days=3)).isoformat(),
    }


def _segment_sql(segment: str) -> tuple[str, list]:
    """Разворачивает имя сегмента в SQL-условие с позиционными параметрами."""
    where = SEGMENTS.get(segment or "all", SEGMENTS["all"])
    params: list = []
    values = _segment_params()
    # именованные :placeholder → ? в порядке появления (aiosqlite любит позиционные)
    for name, value in values.items():
        token = f":{name}"
        while token in where:
            where = where.replace(token, "?", 1)
            params.append(value)
    return where, params


async def segment_ids(db, segment: str, *, exclude_deleted: bool = True) -> list[int]:
    where, params = _segment_sql(segment)
    extra = " AND status <> 'deleted'" if exclude_deleted else ""
    cur = await db.execute(
        f"SELECT tg_id FROM users WHERE ({where}){extra}", params)
    return [r["tg_id"] for r in await cur.fetchall()]


async def segment_count(db, segment: str) -> int:
    where, params = _segment_sql(segment)
    cur = await db.execute(
        f"SELECT COUNT(*) c FROM users WHERE ({where}) AND status <> 'deleted'", params)
    return (await cur.fetchone())["c"]


async def search(db, query: str = "", segment: str = "all", *,
                 limit: int = 50, offset: int = 0,
                 order: str = "created_at") -> list[dict]:
    """Список пользователей для CRM: поиск по имени/username/id + сегмент."""
    where, params = _segment_sql(segment)
    sql = [f"SELECT * FROM users WHERE ({where})"]
    query = (query or "").strip()
    if query:
        sql.append("AND (name LIKE ? OR username LIKE ? OR CAST(tg_id AS TEXT) LIKE ?)")
        like = f"%{query.lstrip('@')}%"
        params += [like, like, like]
    orders = {"created_at": "created_at DESC", "last_seen": "last_seen DESC",
              "ltv": "ltv_stars DESC", "name": "name COLLATE NOCASE"}
    sql.append(f"ORDER BY {orders.get(order, orders['created_at'])}")
    sql.append("LIMIT ? OFFSET ?")
    params += [limit, offset]
    cur = await db.execute(" ".join(sql), params)
    return [dict(r) for r in await cur.fetchall()]


async def count(db, query: str = "", segment: str = "all") -> int:
    where, params = _segment_sql(segment)
    sql = [f"SELECT COUNT(*) c FROM users WHERE ({where})"]
    query = (query or "").strip()
    if query:
        sql.append("AND (name LIKE ? OR username LIKE ? OR CAST(tg_id AS TEXT) LIKE ?)")
        like = f"%{query.lstrip('@')}%"
        params += [like, like, like]
    cur = await db.execute(" ".join(sql), params)
    return (await cur.fetchone())["c"]


async def push_targets(db) -> list:
    """Кому вообще может прийти запланированное сообщение (для планировщика)."""
    cur = await db.execute(
        "SELECT * FROM users WHERE onboarded=1 AND status='active'")
    return await cur.fetchall()


def chart_of(user) -> dict:
    try:
        return json.loads(user["chart_json"] or "{}")
    except (TypeError, ValueError):
        return {}
