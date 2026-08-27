"""Зависимости FastAPI: соединение с БД, клиентка, администратор, темп запросов."""
from __future__ import annotations

import logging


from fastapi import Depends, Header, HTTPException, Query, Request

from ..config import settings
from ..data.session import connect
from ..repo import admin as admin_repo
from ..repo import users as users_repo
from ..services import rate_limit as rate_limit_service
from .security import parse_init_data

log = logging.getLogger("oracle.api")

# Одно соединение на процесс: пул PostgreSQL-адаптера живёт в db_ объекта.
_db = None


async def get_db():
    global _db
    if _db is None:
        _db = await connect()
    return _db


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None


# ─────────────────────────────── темп запросов ────────────────────────────────
# The limiter service supports process-local development and Redis-backed
# multi-process production. Identity is always derived from signed Telegram data
# (or explicit dev mode), never from a user-controlled body field.

LIMITS = {
    "read": (120, 60),
    "write": (30, 60),
    "llm": (12, 60),
    "admin": (60, 60),
}


def rate_limit(bucket: str = "read"):
    """Distributed-safe dependency limiter with bounded retry metadata."""
    limit, window = LIMITS.get(bucket, LIMITS["read"])

    async def guard(request: Request):
        tg_id = 0
        data = parse_init_data(request.headers.get("x-init-data", ""))
        if data:
            tg_id = data["tg_id"]
        elif settings.dev_mode:
            try:
                tg_id = int(request.query_params.get("dev_user") or 0)
            except ValueError:
                tg_id = 0
        decision = await rate_limit_service.allow(str(tg_id), bucket, limit, window)
        if not decision.allowed:
            log.warning(
                "rate_limit_denied bucket=%s backend=%s retry_after=%s",
                bucket, decision.backend, decision.retry_after,
            )
            raise HTTPException(
                429,
                detail={"code": "rate_limited", "backend": decision.backend,
                        "message": "слишком часто — переведи дыхание 🌙"},
                headers={"Retry-After": str(decision.retry_after)},
            )

    return guard


# ──────────────────────────────── клиентка ────────────────────────────────────

async def current_user(db=Depends(get_db),
                       x_init_data: str | None = Header(default=None),
                       dev_user: int | None = Query(default=None)):
    """Клиентка по подписи Telegram. В DEV_MODE — по `?dev_user=<id>`."""
    data = parse_init_data(x_init_data) if x_init_data else None
    tg_id = data["tg_id"] if data else None
    if tg_id is None and settings.dev_mode and dev_user:
        tg_id = dev_user
    if tg_id is None:
        raise HTTPException(401, "подпись Telegram не подтверждена")

    user = await users_repo.get(db, tg_id)
    if not user:
        raise HTTPException(404, "открой бота и нажми /start — я ещё не знаю тебя ✨")
    if user["status"] == "blocked":
        raise HTTPException(403, "доступ приостановлен")
    if data and data["username"] and user["username"] != data["username"]:
        await users_repo.update(db, tg_id, username=data["username"])
    return user


async def confirmed_age_user(user=Depends(current_user)):
    """Пользователь, подтвердивший возраст 16+ на сервере.

    Age-gate must not rely on a Mini App overlay: every sensitive product
    surface depends on this guard so direct API calls cannot bypass consent.
    """
    if not user["age_confirmed"]:
        raise HTTPException(
            403,
            detail={
                "code": "age_confirmation_required",
                "message": "подтверди, что тебе уже исполнилось 16 лет",
            },
        )
    return user


async def active_user(user=Depends(confirmed_age_user)):
    """Как `confirmed_age_user`, но требует живую подписку — для платного контента."""
    if not users_repo.sub_active(user):
        raise HTTPException(402, "подписка завершена — продли её в боте")
    return user


async def touched_user(user=Depends(current_user), db=Depends(get_db)):
    """Клиентка + отметка «была онлайн» (для аналитики удержания)."""
    await users_repo.touch(db, user["tg_id"])
    return user


# ─────────────────────────────── администратор ────────────────────────────────

class AdminContext:
    """Кто вошёл в панель и что ему можно."""

    def __init__(self, tg_id: int, role: str):
        self.tg_id = tg_id
        self.role = role

    def require(self, permission: str) -> None:
        if not admin_repo.can(self.role, permission):
            raise HTTPException(403, f"недостаточно прав: нужно {permission}")


async def current_admin(db=Depends(get_db),
                        x_init_data: str | None = Header(default=None),
                        dev_user: int | None = Query(default=None)) -> AdminContext:
    """Администратор панели.

    Вход только через подпись Telegram: панель открывается кнопкой из бота, и
    отдельного пароля у неё нет — так нечего утекать. `dev_user` работает лишь
    при DEV_MODE, то есть на машине разработчика.
    """
    data = parse_init_data(x_init_data) if x_init_data else None
    tg_id = data["tg_id"] if data else None
    if tg_id is None and settings.dev_mode and dev_user:
        tg_id = dev_user
    if tg_id is None:
        raise HTTPException(401, "подпись Telegram не подтверждена")
    role = await admin_repo.resolve_role(db, tg_id)
    if not role:
        log.warning("попытка входа в админку без роли")
        raise HTTPException(403, "нет доступа к панели")
    user = await users_repo.get(db, tg_id)
    if user and user["status"] == "blocked":
        log.warning("заблокированный администратор отклонён")
        raise HTTPException(403, "доступ приостановлен")
    return AdminContext(tg_id, role)


def require(permission: str):
    """Зависимость-проверка права: `Depends(require('catalog'))`."""
    async def guard(ctx: AdminContext = Depends(current_admin)) -> AdminContext:
        ctx.require(permission)
        return ctx
    return guard
