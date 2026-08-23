"""Администраторы, роли и аудит действий.

Аудит пишется на каждое изменяющее действие панели. Причина простая: панель
умеет дарить подписки, начислять Кристаллы и рассылать сообщения всей базе —
такие операции должны быть объяснимы задним числом.
"""
from __future__ import annotations

import json

from ..config import settings
from ..data.session import transaction, utcnow

# Роли по возрастанию прав. Проверка — «уровень роли ≥ требуемого».
ROLES = ("analyst", "support", "admin", "owner")
ROLE_LEVEL = {role: i for i, role in enumerate(ROLES)}

# Что разрешено роли: набор областей панели.
PERMISSIONS = {
    "analyst": {"dashboard", "users:read", "content:read", "settings:read"},
    "support": {"dashboard", "users:read", "users:write", "crm:write",
                "content:read", "settings:read", "grants"},
    "admin": {"dashboard", "users:read", "users:write", "crm:write",
              "content:read", "content:write", "settings:read", "settings:write",
              "grants", "promo", "broadcast", "catalog"},
    "owner": {"*"},
}


async def get_admin(db, tg_id: int):
    cur = await db.execute("SELECT * FROM admins WHERE tg_id=?", (tg_id,))
    return await cur.fetchone()


async def resolve_role(db, tg_id: int) -> str | None:
    """Роль администратора или None. ADMIN_ID из .env всегда владелец.

    Аварийный доступ через .env нужен, чтобы потеря записи в таблице (или пустая
    после переезда база) не заперла владельца снаружи собственной панели.
    """
    if settings.admin_id and tg_id == settings.admin_id:
        return "owner"
    row = await get_admin(db, tg_id)
    return row["role"] if row else None


def can(role: str | None, permission: str) -> bool:
    if not role:
        return False
    allowed = PERMISSIONS.get(role, set())
    return "*" in allowed or permission in allowed


async def list_admins(db) -> list[dict]:
    cur = await db.execute("SELECT * FROM admins ORDER BY created_at")
    rows = [dict(r) for r in await cur.fetchall()]
    if settings.admin_id and not any(r["tg_id"] == settings.admin_id for r in rows):
        rows.insert(0, {"tg_id": settings.admin_id, "role": "owner",
                        "title": "Владелец (.env)", "created_at": None})
    return rows


async def add_admin(db, tg_id: int, role: str = "admin", *, title: str = "",
                    added_by: int | None = None) -> None:
    if role not in ROLE_LEVEL:
        raise ValueError(f"неизвестная роль: {role}")
    async with transaction(db):
        await db.execute(
            "INSERT OR REPLACE INTO admins(tg_id, role, title, added_by, created_at) "
            "VALUES(?,?,?,?,COALESCE((SELECT created_at FROM admins WHERE tg_id=?),?))",
            (tg_id, role, title, added_by, tg_id, utcnow()))


async def update_admin_role(db, tg_id: int, role: str, *,
                            title: str | None = None,
                            changed_by: int | None = None) -> bool:
    """Меняет роль существующего администратора, не затирая его подпись.

    Добавление нового сотрудника остаётся отдельным действием (`add_admin`).
    Это защищает от опечатки в id в форме смены роли.
    """
    if role not in ROLE_LEVEL:
        raise ValueError(f"неизвестная роль: {role}")
    async with transaction(db):
        if title is None:
            cur = await db.execute(
                "UPDATE admins SET role=?, added_by=? WHERE tg_id=?",
                (role, changed_by, tg_id))
        else:
            cur = await db.execute(
                "UPDATE admins SET role=?, title=?, added_by=? WHERE tg_id=?",
                (role, title, changed_by, tg_id))
    return bool(cur.rowcount)


async def remove_admin(db, tg_id: int) -> None:
    async with transaction(db):
        await db.execute("DELETE FROM admins WHERE tg_id=?", (tg_id,))


# ──────────────────────────────── аудит ───────────────────────────────────────

async def audit(db, admin_id: int | None, action: str, *, target: str = "",
                payload: dict | None = None) -> None:
    async with transaction(db):
        await db.execute(
            "INSERT INTO admin_audit(admin_id, action, target, payload_json, created_at) "
            "VALUES(?,?,?,?,?)",
            (admin_id, action, target,
             json.dumps(payload, ensure_ascii=False) if payload else None, utcnow()))


async def audit_log(db, limit: int = 200) -> list[dict]:
    cur = await db.execute(
        "SELECT a.*, u.name admin_name FROM admin_audit a "
        "LEFT JOIN users u ON u.tg_id = a.admin_id ORDER BY a.id DESC LIMIT ?",
        (limit,))
    return [dict(r) for r in await cur.fetchall()]
