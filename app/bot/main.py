"""Точка входа бота: python -m app.bot.main

Процесс бота владеет: поллингом Telegram, планировщиком (утренние прогнозы,
отчёты, продления) и отправкой рассылок. Веб-процесс (`app.api.main`) их не
дублирует — иначе клиентка получала бы каждое сообщение дважды.
"""
from __future__ import annotations

import asyncio
import logging
import time

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from ..config import settings
from ..data.session import connect
from ..repo import content as content_repo
from ..services import broadcast, scheduler
from . import chat, features, growth, onboarding, profile, shop

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("oracle")

BROADCAST_TICK = 60          # рассылки проверяем чаще планировщика: «отправить
                             # сейчас» из панели не должно ждать десять минут

COMMANDS = [
    BotCommand(command="start", description="Начать / вернуться в меню"),
    BotCommand(command="today", description="Прогноз дня"),
    BotCommand(command="horoscope", description="Гороскоп на сегодня"),
    BotCommand(command="practice", description="Практики и мантры"),
    BotCommand(command="moon", description="Лунная неделя"),
    BotCommand(command="promo", description="Ввести промокод"),
    BotCommand(command="help", description="Как я работаю"),
]


class DbMiddleware(BaseMiddleware):
    """Прокидывает соединение с БД в хендлеры (аргумент db)."""

    def __init__(self, db):
        self.db = db

    async def __call__(self, handler, event, data):
        data["db"] = self.db
        return await handler(event, data)


class ThrottleMiddleware(BaseMiddleware):
    """Антифлуд по пользователю.

    Молча гасим слишком частые сообщения: ответ «не так быстро» на каждый
    лишний тап сам превращается в спам.
    """

    def __init__(self, interval: float = 1.2):
        self.interval = interval
        self.last: dict[int, float] = {}

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user:
            now = time.monotonic()
            if now - self.last.get(user.id, 0) < self.interval:
                return None
            self.last[user.id] = now
            if len(self.last) > 20_000:
                self.last.clear()
        return await handler(event, data)


async def on_error(event, exception=None, **kwargs):
    """Глобальный обработчик: один сбойный апдейт не роняет поллинг."""
    log.exception("ошибка обработки апдейта: %s",
                  exception or getattr(event, "exception", "?"))
    return True


async def broadcast_loop(bot: Bot, db) -> None:
    while True:
        try:
            await broadcast.tick(bot, db)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            log.error("цикл рассылок: %s", e)
        await asyncio.sleep(BROADCAST_TICK)


async def _remember_username(bot: Bot, db) -> None:
    """Имя бота нужно Mini App для реферальных ссылок — кладём его в настройки."""
    try:
        me = await bot.get_me()
        current = await content_repo.get_setting(db, "brand.bot_username", "")
        if current != me.username:
            await content_repo.set_setting(db, "brand.bot_username", me.username)
        log.info("бот @%s готов", me.username)
    except Exception as e:  # noqa: BLE001
        log.warning("не удалось узнать имя бота: %s", e)


def build_dispatcher(db) -> Dispatcher:
    dp = Dispatcher()
    dp.update.middleware(DbMiddleware(db))
    dp.message.middleware(ThrottleMiddleware())
    dp.errors.register(on_error)

    # Порядок критичен: FSM-состояния онбординга и разделов должны получить текст
    # раньше, чем свободный чат — он ловит любое сообщение.
    dp.include_router(onboarding.router)
    dp.include_router(features.router)
    dp.include_router(growth.router)
    dp.include_router(shop.router)
    dp.include_router(profile.router)
    dp.include_router(chat.router)
    return dp


async def main() -> None:
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN не задан в .env")

    for warning in settings.ready:
        log.warning("проверь конфигурацию: %s", warning)

    db = await connect()
    bot = Bot(settings.bot_token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher(db)

    names = {"anthropic": "Claude API", "openai": "OpenAI API",
             "custom": f"свой сервер ({settings.custom_model_main})",
             "off": "офлайн-режим (без LLM)"}
    chain = " → ".join(names.get(p, p) for p in settings.provider_chain) or names["off"]
    log.info("Оракул запускается. LLM-цепочка: %s", chain)

    await _remember_username(bot, db)
    try:
        await bot.set_my_commands(COMMANDS)
    except Exception as e:  # noqa: BLE001
        log.warning("не удалось задать меню команд: %s", e)

    tasks = [
        asyncio.create_task(scheduler.run(bot, db), name="scheduler"),
        asyncio.create_task(broadcast_loop(bot, db), name="broadcasts"),
    ]
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        # аккуратное завершение: иначе SQLite остаётся с открытым WAL,
        # а недоотправленная рассылка теряет прогресс
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await bot.session.close()
        await db.close()
        log.info("Оракул остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("остановка по Ctrl+C")
