"""Планировщик: преген утренних прогнозов (G8).

Преген — за час до рассылки по таймзоне: текст прогноза уже лежит в forecasts,
когда наступает час клиентки. Проверяем окно, идемпотентность кеша и фильтр
аудитории. LLM в тестах выключен, поэтому генерация уходит в офлайн-шаблон —
это заодно проверяет запасной путь.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repo import readings, users
from app.services import scheduler


async def _moscow_at_8(db):
    """Клиентка, у которой в выбранный момент местные 8:00."""
    await users.ensure(db, 1001, "Тестовая")
    await users.update(db, 1001, onboarded=1, tz="Europe/Moscow", sub_level="vip")
    return 1001


async def test_pregen_fills_forecast_before_push(db):
    """За час до рассылки преген кладёт текст в forecasts — к часу он готов."""
    tg_id = await _moscow_at_8(db)
    now = datetime(2026, 8, 3, 5, 0, tzinfo=timezone.utc)   # 5:00 UTC = 8:00 МСК

    scheduler._KNOWN_ZONES = ["Europe/Moscow"]
    await scheduler._pregen_forecasts(db, now, {"morning_hour": 9})

    day = users.user_today(await users.get(db, tg_id))
    text = await readings.get_forecast(db, tg_id, day)
    assert text and text.startswith("🌅"), "прогноз не прегенерирован или пуст"


async def test_pregen_is_idempotent(db, monkeypatch):
    """Второй проход не генерирует заново: текст уже в кеше forecasts."""
    tg_id = await _moscow_at_8(db)
    now = datetime(2026, 8, 3, 5, 0, tzinfo=timezone.utc)

    calls = []
    orig = scheduler.agent_core.daily_forecast

    async def counting(db_, user, chart):
        calls.append(user["tg_id"])
        return await orig(db_, user, chart)

    monkeypatch.setattr(scheduler.agent_core, "daily_forecast", counting)
    scheduler._KNOWN_ZONES = ["Europe/Moscow"]
    await scheduler._pregen_forecasts(db, now, {"morning_hour": 9})
    await scheduler._pregen_forecasts(db, now, {"morning_hour": 9})

    assert calls.count(tg_id) == 1, "второй проход сгенерировал прогноз заново"


async def test_pregen_skips_off_audience(db):
    """Без рассылки (morning_push=0) прогноз не тратится."""
    await _moscow_at_8(db)
    await users.ensure(db, 9002, "Без рассылки")
    await users.update(db, 9002, onboarded=1, tz="Europe/Moscow",
                       sub_level="vip", morning_push=0)
    now = datetime(2026, 8, 3, 5, 0, tzinfo=timezone.utc)

    scheduler._KNOWN_ZONES = ["Europe/Moscow"]
    await scheduler._pregen_forecasts(db, now, {"morning_hour": 9})

    day = users.user_today(await users.get(db, 9002))
    assert await readings.get_forecast(db, 9002, day) is None


async def test_pregen_noop_outside_window(db, monkeypatch):
    """В другие часы преген ничего не генерирует."""
    tg_id = await _moscow_at_8(db)
    now = datetime(2026, 8, 3, 5, 0, tzinfo=timezone.utc)

    called = []

    async def counting(db_, user):
        called.append(user["tg_id"])
        return "🌅"

    monkeypatch.setattr(scheduler.agent_core, "daily_forecast_cached", counting)
    scheduler._KNOWN_ZONES = ["Europe/Moscow"]
    # окно прегена = 8:00 МСК, а тут morning_hour=11 → преген должен молчать
    await scheduler._pregen_forecasts(db, now, {"morning_hour": 11})

    assert called == []


async def _bulk_users(db, base: int, count: int, *, sub_until: str | None = None):
    """Прямая вставка пачкой — быстрее, чем 6000× users.ensure."""
    ids = range(base, base + count)
    if sub_until is None:
        await db.executemany(
            "INSERT INTO users(tg_id, onboarded, status, tz) "
            "VALUES(?,1,'active','Europe/Moscow')", [(i,) for i in ids])
    else:
        await db.executemany(
            "INSERT INTO users(tg_id, onboarded, status, tz, sub_until) "
            "VALUES(?,1,'active','Europe/Moscow',?)", [(i, sub_until) for i in ids])
    await db.commit()


async def test_audience_scales_beyond_cap(db):
    """10-тысячная аудитория не режется лимитом 5000: приходит целиком."""
    await _bulk_users(db, 100_000, 6000)

    audience = await scheduler._audience(db, {"Europe/Moscow"})

    assert len(audience) == 6000, "курсорная пагинация обрезала аудиторию"
    ids = [u["tg_id"] for u in audience]
    assert ids == sorted(ids), "аудитория не упорядочена по tg_id"
    assert len(set(ids)) == 6000, "есть дубли между пачками"


async def test_expiring_audience_scales_beyond_cap(db):
    """Кандидаты на продление выбираются тоже без отсечки в 5000."""
    soon = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    await _bulk_users(db, 200_000, 6000, sub_until=soon)

    audience = await scheduler._expiring_audience(db, datetime.now(timezone.utc))

    assert len(audience) == 6000, "курсор обрезал expiring-аудиторию"
    ids = [u["tg_id"] for u in audience]
    assert ids == sorted(ids) and len(set(ids)) == 6000
