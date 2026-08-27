"""Общие фикстуры тестов.

Каждый тест получает свою пустую базу в temp-файле: тесты денег и лимитов
меняют состояние, и общая база делала бы их зависимыми от порядка запуска.
LLM в тестах выключен — проверяем логику продукта, а не качество текстов.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Выключаем провайдеров до импорта настроек: иначе тесты полезут в сеть.
os.environ["LLM_PROVIDER"] = "off"
# Tests use deterministic keyword memory; never inherit a sandbox embedding key.
os.environ["EMBED_MODEL"] = ""
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("DEV_MODE", "1")
# Legacy fixtures intentionally opt into the historical trial; production defaults off.
os.environ.setdefault("AUTO_TRIAL", "1")


@pytest.fixture
async def db(tmp_path):
    from app.data.session import connect
    connection = await connect(str(tmp_path / "test.db"))
    yield connection
    await connection.close()


@pytest.fixture
async def user(db):
    """Клиентка с триалом, прошедшая онбординг (карта построена как в онбординге)."""
    import json

    from app.core import astro
    from app.repo import users
    created = await users.ensure(db, 1001, "Тестовая", "tester")
    chart = await astro.compute_chart_async("1990-06-21", "14:30", "Казань",
                                            55.79, 49.12, "Europe/Moscow")
    await users.update(db, 1001, onboarded=1, birth_date="1990-06-21",
                       birth_time="14:30", birth_time_known=1,
                       birth_city="Казань", tz="Europe/Moscow",
                       sub_level="vip",
                       chart_json=json.dumps(chart, ensure_ascii=False),
                       age_confirmed=1, memory_enabled=0)
    assert created["tg_id"] == 1001
    return await users.get(db, 1001)


@pytest.fixture
async def free_user(db):
    """Клиентка без активной подписки — уровень «Искра»."""
    from app.repo import users
    await users.ensure(db, 1002, "Без подписки")
    await users.update(db, 1002, onboarded=1, birth_date="1988-01-15",
                       sub_until="2000-01-01T00:00:00+00:00", sub_level="free",
                       age_confirmed=1, memory_enabled=0)
    return await users.get(db, 1002)


@pytest.fixture(autouse=True)
async def _reset_api_rate_limits():
    """Внутрипроцессное состояние между тестами: API-лимитер накапливает корзину
    «write», кеш touch проносит last_seen между тестами, фоновые записи событий
    (G14) могут жить дольше теста и дёргать чужое соединение."""
    from app.core import memory
    from app.repo import users
    from app.services import analytics, rate_limit as rate_limit_service
    rate_limit_service.reset_limiter_for_tests()
    users._last_seen_cache.clear()
    memory._recall_cache.clear()
    await analytics.drain()
