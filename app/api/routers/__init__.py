"""Роутеры API. Каждый файл — один экран или одна область продукта."""
from . import (admin, chart, chat, diary, practices, profile,  # noqa: F401
               share, shop, tarot, today, webhooks)

ROUTERS = (profile.router, today.router, chat.router, tarot.router, chart.router,
           diary.router, practices.router, share.router, shop.router,
           webhooks.router, admin.router)

__all__ = ["ROUTERS"]
