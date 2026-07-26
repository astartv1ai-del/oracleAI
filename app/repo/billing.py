"""Деньги: тарифы, товары, заказы, платежи, права доступа, Кристаллы.

Три правила, из которых вырос этот модуль.

1. **Заказ создаётся до оплаты.** У каждого инвойса есть строка в `orders` с
   уникальным `payload`. Telegram может доставить `successful_payment` повторно
   (ретрай при обрыве связи) — по `payload` мы видим, что заказ уже оплачен, и
   не выдаём товар второй раз.
2. **Баланс ✦ меняется только вместе с записью в журнал.** `users.crystals` —
   быстрый счётчик, `crystal_ledger` — источник правды для аудита. Обе записи
   в одной транзакции, поэтому разъехаться не могут.
3. **Списание проверяет баланс тем же запросом, что и меняет его.** Проверка
   «хватает ли» отдельным SELECT — это гонка: два одновременных экстренных
   расклада уводили баланс в минус.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from ..data.session import transaction, utcnow

# ─────────────────────────────── тарифы ───────────────────────────────────────

FREE_PLAN = {
    "code": "free", "title": "✦ Искра", "tagline": "",
    "price_stars": 0, "price_usd": 0.0, "period_days": 36500,
    "daily_questions": 0, "weekly_questions": 1, "memory_depth": 5,
    "crystals_grant": 0, "features": [], "badge": None,
}


def _plan_dict(row) -> dict:
    plan = dict(row)
    try:
        plan["features"] = json.loads(plan.pop("features_json", None) or "[]")
    except ValueError:
        plan["features"] = []
    return plan


async def get_plan(db, code: str) -> dict:
    cur = await db.execute("SELECT * FROM plans WHERE code=?", (code or "",))
    row = await cur.fetchone()
    return _plan_dict(row) if row else dict(FREE_PLAN)


async def list_plans(db, *, public_only: bool = True) -> list[dict]:
    sql = "SELECT * FROM plans WHERE is_active=1"
    if public_only:
        sql += " AND is_public=1"
    sql += " ORDER BY sort, price_stars"
    cur = await db.execute(sql)
    return [_plan_dict(r) for r in await cur.fetchall()]


async def upsert_plan(db, code: str, **fields) -> None:
    allowed = {"title", "tagline", "price_stars", "price_usd", "period_days",
               "daily_questions", "weekly_questions", "memory_depth",
               "crystals_grant", "features_json", "badge", "sort",
               "is_active", "is_public"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    async with transaction(db):
        await db.execute(
            "INSERT OR IGNORE INTO plans(code, title, created_at, updated_at) "
            "VALUES(?,?,?,?)", (code, fields.get("title", code), utcnow(), utcnow()))
        if fields:
            keys = ", ".join(f"{k}=?" for k in fields)
            await db.execute(
                f"UPDATE plans SET {keys}, updated_at=? WHERE code=?",
                (*fields.values(), utcnow(), code))


# ─────────────────────────────── товары ───────────────────────────────────────

async def get_product(db, sku: str):
    cur = await db.execute("SELECT * FROM products WHERE sku=? AND is_active=1", (sku,))
    return await cur.fetchone()


async def list_products(db, kind: str | None = None, *,
                        active_only: bool = True) -> list[dict]:
    sql = ["SELECT * FROM products WHERE 1=1"]
    params: list = []
    if active_only:
        sql.append("AND is_active=1")
    if kind:
        sql.append("AND kind=?")
        params.append(kind)
    sql.append("ORDER BY sort, price_stars")
    cur = await db.execute(" ".join(sql), params)
    return [dict(r) for r in await cur.fetchall()]


async def upsert_product(db, sku: str, **fields) -> None:
    allowed = {"kind", "title", "description", "price_stars", "price_crystals",
               "grant_kind", "grant_code", "grant_qty", "valid_days", "sort",
               "is_active"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    async with transaction(db):
        await db.execute(
            "INSERT OR IGNORE INTO products(sku, kind, title, created_at, updated_at) "
            "VALUES(?,?,?,?,?)",
            (sku, fields.get("kind", "product"), fields.get("title", sku),
             utcnow(), utcnow()))
        if fields:
            keys = ", ".join(f"{k}=?" for k in fields)
            await db.execute(f"UPDATE products SET {keys}, updated_at=? WHERE sku=?",
                             (*fields.values(), utcnow(), sku))


# ─────────────────────────────── заказы ───────────────────────────────────────

async def create_order(db, tg_id: int, kind: str, *, sku: str | None = None,
                       title: str = "", amount_stars: int = 0,
                       amount_crystals: int = 0, surface: str = "bot",
                       meta: dict | None = None) -> dict:
    """Создаёт заказ в статусе pending и присваивает уникальный payload.

    payload уходит в инвойс Telegram и возвращается в `successful_payment` —
    это наш ключ идемпотентности, поэтому он и уникален на уровне БД.
    """
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO orders(tg_id, kind, sku, title, amount_stars, "
            "amount_crystals, status, surface, meta_json, created_at) "
            "VALUES(?,?,?,?,?,?,'pending',?,?,?)",
            (tg_id, kind, sku, title, amount_stars, amount_crystals, surface,
             json.dumps(meta, ensure_ascii=False) if meta else None, utcnow()))
        order_id = cur.lastrowid
        payload = f"o{order_id}:{kind}:{sku or '-'}"[:120]
        await db.execute("UPDATE orders SET payload=? WHERE id=?", (payload, order_id))
    return {"id": order_id, "payload": payload, "kind": kind, "sku": sku,
            "amount_stars": amount_stars, "amount_crystals": amount_crystals,
            "title": title}


async def get_order(db, order_id: int):
    cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    return await cur.fetchone()


async def order_by_payload(db, payload: str):
    cur = await db.execute("SELECT * FROM orders WHERE payload=?", (payload,))
    return await cur.fetchone()


async def mark_order_paid(db, payload: str, *, charge_id: str | None = None,
                          amount_stars: int | None = None,
                          provider: str = "telegram_stars"):
    """Помечает заказ оплаченным. Возвращает строку заказа или None.

    None означает «обрабатывать нечего»: либо payload неизвестен, либо заказ уже
    оплачен ранее. Второе — нормальная ситуация при ретрае вебхука, и товар
    повторно выдавать нельзя.
    """
    async with transaction(db):
        cur = await db.execute(
            "SELECT * FROM orders WHERE payload=? AND status='pending'", (payload,))
        order = await cur.fetchone()
        if not order:
            return None
        stars = amount_stars if amount_stars is not None else order["amount_stars"]
        await db.execute(
            "UPDATE orders SET status='paid', paid_at=? WHERE id=?",
            (utcnow(), order["id"]))
        await db.execute(
            "INSERT INTO payments(order_id, tg_id, amount_stars, currency, charge_id, "
            "provider, status, created_at) VALUES(?,?,?,'XTR',?,?,'succeeded',?)",
            (order["id"], order["tg_id"], stars, charge_id, provider, utcnow()))
        if stars:
            await db.execute("UPDATE users SET ltv_stars=ltv_stars+? WHERE tg_id=?",
                             (stars, order["tg_id"]))
    return order


async def refund_order(db, order_id: int) -> bool:
    async with transaction(db):
        cur = await db.execute(
            "SELECT * FROM orders WHERE id=? AND status='paid'", (order_id,))
        order = await cur.fetchone()
        if not order:
            return False
        await db.execute("UPDATE orders SET status='refunded' WHERE id=?", (order_id,))
        await db.execute("UPDATE payments SET status='refunded' WHERE order_id=?",
                         (order_id,))
        await db.execute(
            "UPDATE users SET ltv_stars=MAX(0, ltv_stars-?) WHERE tg_id=?",
            (order["amount_stars"] or 0, order["tg_id"]))
    return True


async def payment_charge_id(db, order_id: int) -> str | None:
    """Идентификатор платежа Telegram — нужен для возврата Stars."""
    cur = await db.execute(
        "SELECT charge_id FROM payments WHERE order_id=? AND status='succeeded' "
        "ORDER BY id DESC LIMIT 1", (order_id,))
    row = await cur.fetchone()
    return row["charge_id"] if row else None


async def user_orders(db, tg_id: int, limit: int = 50) -> list[dict]:
    cur = await db.execute(
        "SELECT * FROM orders WHERE tg_id=? ORDER BY id DESC LIMIT ?", (tg_id, limit))
    return [dict(r) for r in await cur.fetchall()]


async def recent_orders(db, *, status: str | None = None, limit: int = 100) -> list[dict]:
    sql = ["SELECT o.*, u.name, u.username FROM orders o "
           "LEFT JOIN users u ON u.tg_id = o.tg_id WHERE 1=1"]
    params: list = []
    if status:
        sql.append("AND o.status=?")
        params.append(status)
    sql.append("ORDER BY o.id DESC LIMIT ?")
    params.append(limit)
    cur = await db.execute(" ".join(sql), params)
    return [dict(r) for r in await cur.fetchall()]


# ─────────────────────────────── Кристаллы ────────────────────────────────────

async def add_crystals(db, tg_id: int, delta: int, reason: str,
                       ref: str | None = None) -> int:
    """Начисление/списание без проверки баланса (для начислений и админки)."""
    async with transaction(db):
        await db.execute("UPDATE users SET crystals=crystals+? WHERE tg_id=?",
                         (delta, tg_id))
        cur = await db.execute("SELECT crystals FROM users WHERE tg_id=?", (tg_id,))
        row = await cur.fetchone()
        balance = row["crystals"] if row else 0
        await db.execute(
            "INSERT INTO crystal_ledger(tg_id, delta, reason, balance, ref, created_at) "
            "VALUES(?,?,?,?,?,?)", (tg_id, delta, reason, balance, ref, utcnow()))
    return balance


async def spend_crystals(db, tg_id: int, amount: int, reason: str,
                         ref: str | None = None) -> bool:
    """Списывает ✦, если хватает. Проверка и списание — одним UPDATE.

    Условие `crystals >= ?` внутри UPDATE делает операцию атомарной: два
    параллельных списания не могут оба увидеть достаточный баланс.
    """
    if amount <= 0:
        return True
    async with transaction(db):
        cur = await db.execute(
            "UPDATE users SET crystals=crystals-? WHERE tg_id=? AND crystals>=?",
            (amount, tg_id, amount))
        if not cur.rowcount:
            return False
        cur = await db.execute("SELECT crystals FROM users WHERE tg_id=?", (tg_id,))
        row = await cur.fetchone()
        balance = row["crystals"] if row else 0
        await db.execute(
            "INSERT INTO crystal_ledger(tg_id, delta, reason, balance, ref, created_at) "
            "VALUES(?,?,?,?,?,?)", (tg_id, -amount, reason, balance, ref, utcnow()))
    return True


async def crystal_history(db, tg_id: int, limit: int = 50) -> list[dict]:
    cur = await db.execute(
        "SELECT delta, reason, balance, created_at FROM crystal_ledger "
        "WHERE tg_id=? ORDER BY id DESC LIMIT ?", (tg_id, limit))
    return [dict(r) for r in await cur.fetchall()]


# ──────────────────────── права доступа (entitlements) ────────────────────────

async def grant_entitlement(db, tg_id: int, kind: str, code: str | None = None, *,
                            qty: int = 1, valid_days: int | None = None,
                            source: str = "purchase",
                            order_id: int | None = None) -> int:
    expires = None
    if valid_days:
        expires = (datetime.now(timezone.utc) + timedelta(days=valid_days)).isoformat()
    async with transaction(db):
        cur = await db.execute(
            "INSERT INTO entitlements(tg_id, kind, code, qty_total, qty_used, "
            "expires_at, source, order_id, created_at) VALUES(?,?,?,?,0,?,?,?,?)",
            (tg_id, kind, code, qty, expires, source, order_id, utcnow()))
        ent_id = cur.lastrowid
    return ent_id


async def available_entitlements(db, tg_id: int, kind: str,
                                 code: str | None = None) -> int:
    """Сколько неиспользованных прав есть. `code='*'` в БД покрывает любой код."""
    now = utcnow()
    params: list = [tg_id, kind, now]
    clause = ""
    if code:
        clause = " AND (code=? OR code='*' OR code IS NULL)"
        params.append(code)
    cur = await db.execute(
        "SELECT COALESCE(SUM(qty_total - qty_used), 0) n FROM entitlements "
        "WHERE tg_id=? AND kind=? AND qty_used < qty_total "
        f"AND (expires_at IS NULL OR expires_at > ?){clause}", params)
    return (await cur.fetchone())["n"]


async def consume_entitlement(db, tg_id: int, kind: str,
                              code: str | None = None) -> bool:
    """Тратит одно право. Берём то, что истекает раньше — иначе оно сгорит зря."""
    now = utcnow()
    params: list = [tg_id, kind, now]
    clause = ""
    if code:
        clause = " AND (code=? OR code='*' OR code IS NULL)"
        params.append(code)
    async with transaction(db):
        cur = await db.execute(
            "SELECT id FROM entitlements WHERE tg_id=? AND kind=? "
            "AND qty_used < qty_total AND (expires_at IS NULL OR expires_at > ?)"
            f"{clause} ORDER BY (expires_at IS NULL), expires_at, id LIMIT 1", params)
        row = await cur.fetchone()
        if not row:
            return False
        cur = await db.execute(
            "UPDATE entitlements SET qty_used=qty_used+1 "
            "WHERE id=? AND qty_used < qty_total", (row["id"],))
        return bool(cur.rowcount)


async def list_entitlements(db, tg_id: int) -> list[dict]:
    cur = await db.execute(
        "SELECT * FROM entitlements WHERE tg_id=? AND qty_used < qty_total "
        "AND (expires_at IS NULL OR expires_at > ?) ORDER BY id DESC",
        (tg_id, utcnow()))
    return [dict(r) for r in await cur.fetchall()]


# ─────────────────────────────── сводки ───────────────────────────────────────

async def revenue(db, *, days: int = 30) -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    async def scalar(sql, *args):
        cur = await db.execute(sql, args)
        row = await cur.fetchone()
        return row[0] or 0

    return {
        "stars_total": await scalar(
            "SELECT SUM(amount_stars) FROM payments WHERE status='succeeded'"),
        "stars_period": await scalar(
            "SELECT SUM(amount_stars) FROM payments WHERE status='succeeded' "
            "AND created_at>=?", since),
        "orders_paid": await scalar(
            "SELECT COUNT(*) FROM orders WHERE status='paid'"),
        "orders_period": await scalar(
            "SELECT COUNT(*) FROM orders WHERE status='paid' AND paid_at>=?", since),
        "payers": await scalar(
            "SELECT COUNT(DISTINCT tg_id) FROM payments WHERE status='succeeded'"),
        "refunds": await scalar(
            "SELECT COUNT(*) FROM orders WHERE status='refunded'"),
    }


async def top_products(db, *, days: int = 30, limit: int = 10) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cur = await db.execute(
        "SELECT COALESCE(sku, kind) sku, title, COUNT(*) sales, "
        "SUM(amount_stars) stars FROM orders WHERE status='paid' AND paid_at>=? "
        "GROUP BY COALESCE(sku, kind) ORDER BY stars DESC LIMIT ?", (since, limit))
    return [dict(r) for r in await cur.fetchall()]
