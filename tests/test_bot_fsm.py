"""Бот-FSM: сценарий «удали мои данные» (G28).

Хендлеры aiogram гоняем без живого бота: FSMContext на MemoryStorage ведёт
настоящие переходы состояний, а вместо Message — тонкий фейк с `text`,
`from_user` и подставным `answer`. Проверяем сам переход по FSM и то, что
данные правда стираются.
"""
from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.onboarding import DeleteMe, delete_me, delete_me_confirm
from app.repo import users


class _User:
    def __init__(self, tg_id: int):
        self.id = tg_id

    @property
    def first_name(self) -> str:
        return "Тест"


class _Message:
    def __init__(self, tg_id: int, text: str):
        self.from_user = _User(tg_id)
        self.text = text
        self.replied = None

    async def answer(self, text: str = "", **kwargs):
        self.replied = text


def _state_for() -> FSMContext:
    storage = MemoryStorage()
    key = StorageKey(chat_id=1, user_id=1, bot_id=42, thread_id=0)
    return FSMContext(storage=storage, key=key)


async def test_delete_me_enters_confirmation_state(db):
    await users.ensure(db, 1001, "Аня")
    state = _state_for()
    await delete_me(_Message(1001, "/delete_me"), state, db)
    assert await state.get_state() == DeleteMe.confirm.state


async def test_delete_me_ignores_wrong_keyword(db):
    await users.ensure(db, 1002, "Белла")
    state = _state_for()
    await delete_me_confirm(_Message(1002, "пока не надо"), state, db)
    assert (await users.get(db, 1002))["status"] != "deleted"


async def test_delete_me_wipes_data_and_clears_state(db):
    await users.ensure(db, 1003, "Вера")
    state = _state_for()
    await delete_me_confirm(_Message(1003, "УДАЛИТЬ"), state, db)

    user = await users.get(db, 1003)
    assert user["status"] == "deleted"
    assert user["name"] == "удалено"
    assert await state.get_state() is None, "FSM должен был очиститься"
