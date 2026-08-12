"""Рост: промокоды («золотые билеты» с Etsy) и двухуровневая рефералка."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from ..data.session import transaction, utcnow

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # без похожих 0/O, 1/I/L


def generate_code(prefix: str = "", length: int = 8) -> str:
    body = "".join(secrets.choice(ALPHABET) for _ in range(length))
    return f"{prefix}{body}" if prefix else body


# ─────────────────────────────── промокоды ────────────────────────────────────

async def create_codes(db, count: int, *, kind: str = "plan_days", days: int = 30,
                       plan_code: str = "vip", crystals: int = 0,
                       sku: str | None = None, batch: str = "",
                       max_uses: int = 1, valid_days: int | None = None,
                       created_by: int | None = None,
                       prefix: str = "") -> list[str]:
    """Генерирует партию кодов. Партия = листинг/канал, по ней считаем аналитику."""
    expires = None
    if valid_days:
        expires = (datetime.now(timezone.utc) + timedelta(days=valid_days)).isoformat()
    codes: list[str] = []
    async with transaction(db):
        while len(codes) < count:
            code = generate_code(prefix)
            cur = await db.execute(
                "INSERT OR IGNORE INTO promo_codes(code, kind, days, plan_code, crystals, "
                "sku, batch, max_uses, used_count, expires_at, created_by, created_at) "
                "VALUES(?,?,?,?,?,?,?,?,0,?,?,?)",
                (code, kind, days, plan_code, crystals, sku, batch, max_uses,
                 expires, created_by, utcnow()))
            if cur.rowcount:            # коллизия кода — просто берём следующий
                codes.append(code)
    return codes


async def get_code(db, code: str):
    cur = await db.execute("SELECT * FROM promo_codes WHERE code=?",
                           ((code or "").strip().upper(),))
    return await cur.fetchone()


async def redeem(db, code: str, tg_id: int) -> dict | None:
    """Активирует код. Возвращает описание выдачи или None.

    Проверки (срок, лимит использований, повторная активация одним человеком)
    и инкремент счётчика — в одной транзакции: иначе код с `max_uses=1`,
    отправленный двумя сообщениями подряд, активировался бы дважды.
    """
    code = (code or "").strip().upper()
    if not code:
        return None
    async with transaction(db):
        cur = await db.execute("SELECT * FROM promo_codes WHERE code=?", (code,))
        promo = await cur.fetchone()
        if not promo:
            return None
        if promo["expires_at"] and promo["expires_at"] <= utcnow():
            return None
        max_uses = promo["max_uses"] or 1
        if (promo["used_count"] or 0) >= max_uses:
            return None
        cur = await db.execute(
            "SELECT 1 FROM promo_redemptions WHERE code=? AND tg_id=?", (code, tg_id))
        if await cur.fetchone():
            return None                          # этот человек код уже применял

        cur = await db.execute(
            "UPDATE promo_codes SET used_count=COALESCE(used_count,0)+1, "
            "used_by=COALESCE(used_by, ?), used_at=COALESCE(used_at, ?) "
            "WHERE code=? AND COALESCE(used_count,0) < ?",
            (tg_id, utcnow(), code, max_uses))
        if not cur.rowcount:
            return None
        await db.execute(
            "INSERT OR IGNORE INTO promo_redemptions(code, tg_id, created_at) "
            "VALUES(?,?,?)", (code, tg_id, utcnow()))

    return {"code": code, "kind": promo["kind"] or "plan_days",
            "days": promo["days"] or 0, "plan_code": promo["plan_code"] or "vip",
            "crystals": promo["crystals"] or 0, "sku": promo["sku"],
            "batch": promo["batch"]}


async def batch_stats(db) -> list[dict]:
    cur = await db.execute(
        "SELECT COALESCE(batch,'(без партии)') batch, COUNT(*) total, "
        "SUM(CASE WHEN COALESCE(used_count,0) > 0 THEN 1 ELSE 0 END) used, "
        "MIN(created_at) created_at FROM promo_codes GROUP BY batch "
        "ORDER BY created_at DESC")
    return [dict(r) for r in await cur.fetchall()]


async def list_codes(db, *, batch: str | None = None, unused_only: bool = False,
                     limit: int = 200) -> list[dict]:
    sql = ["SELECT * FROM promo_codes WHERE 1=1"]
    params: list = []
    if batch:
        sql.append("AND batch=?")
        params.append(batch)
    if unused_only:
        sql.append("AND COALESCE(used_count,0)=0")
    sql.append("ORDER BY created_at DESC, code LIMIT ?")
    params.append(limit)
    cur = await db.execute(" ".join(sql), params)
    return [dict(r) for r in await cur.fetchall()]


# ─────────────────────────────── рефералы ─────────────────────────────────────

async def record_referral(db, referrer_id: int, invitee_id: int, *,
                          level: int = 1, bonus: int = 0) -> bool:
    """Фиксирует приглашение. False — такое уже записано (UNIQUE-ключ)."""
    async with transaction(db):
        cur = await db.execute(
            "INSERT OR IGNORE INTO referrals(referrer_id, invitee_id, level, bonus, "
            "created_at) VALUES(?,?,?,?,?)",
            (referrer_id, invitee_id, level, bonus, utcnow()))
        return bool(cur.rowcount)


async def referrer_of(db, tg_id: int) -> int | None:
    cur = await db.execute(
        "SELECT referrer_id FROM referrals WHERE invitee_id=? AND level=1", (tg_id,))
    row = await cur.fetchone()
    return row["referrer_id"] if row else None


async def referral_stats(db, tg_id: int) -> dict:
    cur = await db.execute(
        "SELECT level, COUNT(*) n, COALESCE(SUM(bonus),0) bonus FROM referrals "
        "WHERE referrer_id=? GROUP BY level", (tg_id,))
    rows = {r["level"]: dict(r) for r in await cur.fetchall()}
    # сколько приглашённых дошли до оплаты — главный аргумент делиться ссылкой
    cur = await db.execute(
        "SELECT COUNT(*) n FROM referrals r JOIN users u ON u.tg_id = r.invitee_id "
        "WHERE r.referrer_id=? AND r.level=1 AND u.ltv_stars > 0", (tg_id,))
    paying = (await cur.fetchone())["n"]
    return {
        "level1": rows.get(1, {}).get("n", 0),
        "level2": rows.get(2, {}).get("n", 0),
        "bonus_total": sum(r["bonus"] for r in rows.values()),
        "paying": paying,
    }


async def top_referrers(db, limit: int = 20) -> list[dict]:
    cur = await db.execute(
        "SELECT r.referrer_id tg_id, u.name, u.username, COUNT(*) invited, "
        "COALESCE(SUM(r.bonus),0) bonus FROM referrals r "
        "LEFT JOIN users u ON u.tg_id = r.referrer_id WHERE r.level=1 "
        "GROUP BY r.referrer_id ORDER BY invited DESC LIMIT ?", (limit,))
    return [dict(r) for r in await cur.fetchall()]
