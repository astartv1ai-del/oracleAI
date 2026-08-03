"""Зависимости FastAPI: соединение с БД, клиентка, администратор, темп запросов."""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from fastapi import Depends, Header, HTTPException, Query, Request

from ..config import settings
from ..data.session import connect
from ..repo import admin as admin_repo
from ..repo import users as users_repo
from .security import parse_init_data

log = logging.getLogger("oracle.api")

# Одно соединение на процесс: aiosqlite сериализует запросы сама, а WAL позволяет
# API и боту работать с файлом одновременно.
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
# Ограничитель в памяти процесса: он защищает от случайного цикла в клиенте и от
# грубого перебора. Распределённый лимит (несколько инстансов) потребует Redis —
# до этого масштаба одного VPS хватает с запасом.

_hits: dict[tuple[int, str], deque] = defaultdict(deque)

LIMITS = {
    "read": (120, 60),      # 120 запросов в минуту
    "write": (30, 60),
    "llm": (12, 60),        # генерации дороги: 12 в минуту заведомо выше живого темпа
    "admin": (60, 60),      # панель: админ один, грубый перебор / утечка ключа — отсечь
}


def rate_limit(bucket: str = "read"):
    """Зависимость-ограничитель. Ключ — клиентка + корзина."""
    limit, window = LIMITS.get(bucket, LIMITS["read"])

    async def guard(request: Request):
        # tg_id берём из подписанного заголовка, чтобы лимит был персональным,
        # а не общим на весь сервер
        tg_id = 0
        data = parse_init_data(request.headers.get("x-init-data", ""))
        if data:
            tg_id = data["tg_id"]
        elif settings.dev_mode:
            try:
                tg_id = int(request.query_params.get("dev_user") or 0)
            except ValueError:
                tg_id = 0
        key = (tg_id, bucket)
        now = time.monotonic()
        hits = _hits[key]
        while hits and now - hits[0] > window:
            hits.popleft()
        if len(hits) >= limit:
            raise HTTPException(429, "слишком часто — переведи дыхание 🌙")
        hits.append(now)
        if len(_hits) > 50_000:                 # страховка от роста словаря
            _hits.clear()

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


async def active_user(user=Depends(current_user)):
    """Как `current_user`, но требует живую подписку — для платного контента."""
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
        log.warning("попытка входа в админку: %s", tg_id)
        raise HTTPException(403, "нет доступа к панели")
    return AdminContext(tg_id, role)


def require(permission: str):
    """Зависимость-проверка права: `Depends(require('catalog'))`."""
    async def guard(ctx: AdminContext = Depends(current_admin)) -> AdminContext:
        ctx.require(permission)
        return ctx
    return guard
