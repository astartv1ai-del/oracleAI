"""Единый перевод прикладных отказов в HTTP-ошибки."""
from __future__ import annotations

from fastapi import HTTPException


DENY_TEXT = {
    "sub_over": "Доступ завершён 🌙 Продли подписку — я сохранила всё о тебе.",
    "limit_reached": "Вопросы исчерпаны. Вернись на рассвете 🌘 "
                     "или открой поле силой Кристаллов ✦",
}


def access_denied(verdict) -> HTTPException:
    """Преобразует результат лимитов в стабильный HTTP-контракт.

    Сервисный слой возвращает verdict, а HTTP-слой единолично отвечает за
    статус-код и пользовательский detail. Это не даёт сервисам зависеть от
    FastAPI и не заставляет роутеры импортировать друг друга.
    """
    reason = getattr(verdict, "reason", None)
    status = 402 if reason == "sub_over" else 429
    return HTTPException(status_code=status,
                         detail=DENY_TEXT.get(reason, "Сейчас нельзя"))
