"""Практики и мантры: каталог, программа по дням, стрик, завершение.

Раздел держится на непрерывности: «21 день подряд» должно означать ровно это.
Поэтому проверяем не только счётчики, но и то, что повторная отметка за сутки
ничего не двигает, а дойдя до конца программы, она закрывается.
"""
from __future__ import annotations

import pytest

from app.core import practices as catalog
from app.repo import readings, users
from app.services import practices as practices_svc


# ─────────────────────────────── каталог ──────────────────────────────────────

def test_catalog_is_not_empty():
    assert len(catalog.PRACTICES) >= 10, "раздел практик почти пустой"


@pytest.mark.parametrize("code", sorted(catalog.PRACTICES))
def test_every_practice_is_complete(code):
    """Практика без шагов или знаков продвижения бросается на третий день."""
    item = catalog.PRACTICES[code]
    assert item["steps"], f"{code}: нет шагов"
    assert item["signs"], f"{code}: нет знаков продвижения"
    assert item["goal"], f"{code}: непонятно, зачем она"
    assert item["days"] >= 7, f"{code}: программа короче недели"
    assert item["category"] in catalog.CATEGORIES, f"{code}: чужая категория"


@pytest.mark.parametrize("code", sorted(catalog.PRACTICES))
def test_program_covers_all_days(code):
    """На любой день программы должен находиться этап — иначе экран пустой."""
    item = catalog.PRACTICES[code]
    for day in range(1, item["days"] + 1):
        assert catalog.today_step(item, day), f"{code}: нет этапа на день {day}"


def test_all_categories_have_practices():
    used = {item["category"] for item in catalog.PRACTICES.values()}
    assert used == set(catalog.CATEGORIES), "есть раздел без единой практики"


def test_mantras_have_text():
    """У мантры обязан быть текст — иначе её нечего повторять."""
    for code, item in catalog.PRACTICES.items():
        if item["category"] == "mantra":
            assert item.get("text"), f"{code}: мантра без текста"


# ──────────────────────────── прогресс клиентки ───────────────────────────────

async def test_catalog_shows_progress(db, user):
    items = await practices_svc.list_for_user(db, user)
    assert items
    assert all(not p["started"] for p in items), "ничего не должно быть начато"
    assert all(p["today_step"] for p in items), "нет шага на первый день"


async def test_filter_by_category(db, user):
    items = await practices_svc.list_for_user(db, user, category="money")
    assert items
    assert {p["category"] for p in items} == {"money"}


async def test_start_and_first_day(db, user):
    started = await practices_svc.start(db, user, "money_mirror")
    assert started["started"] and started["day_index"] == 0

    result = await practices_svc.mark_done(db, user, "money_mirror")
    assert result["day_index"] == 1
    assert result["streak"] == 1
    assert not result["already"]
    assert not result["finished"]


async def test_second_mark_same_day_does_nothing(db, user):
    await practices_svc.start(db, user, "money_mirror")
    await practices_svc.mark_done(db, user, "money_mirror")
    again = await practices_svc.mark_done(db, user, "money_mirror")
    assert again["already"], "стрик накрутился повторным нажатием"
    assert again["streak"] == 1


async def test_streak_breaks_after_gap(db, user):
    """Пропущенный день обнуляет стрик — на этом держится вся механика."""
    await practices_svc.start(db, user, "energy_clean")
    await practices_svc.mark_done(db, user, "energy_clean")

    # «последняя отметка была позавчера»: имитируем пропуск
    async with _tx(db):
        await db.execute(
            "UPDATE practices SET last_done=date('now','-2 day') "
            "WHERE tg_id=? AND code=?", (user["tg_id"], "energy_clean"))

    result = await practices_svc.mark_done(db, user, "energy_clean")
    assert result["streak"] == 1, "стрик пережил пропуск дня"


async def test_program_finishes_at_last_day(db, user):
    """Дойдя до конца, программа закрывается: «7 дней» должно значить семь."""
    code = "love_release"                       # самая короткая, 9 дней
    total = catalog.PRACTICES[code]["days"]
    await practices_svc.start(db, user, code)

    result = None
    for day in range(total):
        result = await practices_svc.mark_done(db, user, code)
        if result["finished"]:
            break
        async with _tx(db):
            await db.execute(
                "UPDATE practices SET last_done=date('now','-1 day') "
                "WHERE tg_id=? AND code=?", (user["tg_id"], code))

    assert result["finished"], "программа не закрылась на последнем дне"
    assert result["day_index"] == total
    assert "прошла всю программу" in result["message"]


async def test_stop_closes_program(db, user):
    await practices_svc.start(db, user, "mantra_gayatri")
    assert await practices_svc.stop(db, user, "mantra_gayatri")
    assert not await readings.active_practice(db, user["tg_id"], "mantra_gayatri")

    items = await practices_svc.list_for_user(db, user)
    item = next(p for p in items if p["code"] == "mantra_gayatri")
    assert item["finished"]


async def test_unknown_practice_raises(db, user):
    with pytest.raises(LookupError):
        await practices_svc.start(db, user, "нет-такой")


async def test_reminder_targets_skip_marked_today(db, user):
    from app.repo import readings as readings_repo

    await practices_svc.start(db, user, "mantra_shiva")
    today = users.user_today(user)
    targets = await readings_repo.practice_reminder_targets(db, today)
    assert targets, "начатая практика не попала в напоминания"

    code = targets[0]["code"]
    await practices_svc.mark_done(db, user, code)
    after = await readings_repo.practice_reminder_targets(db, today)
    assert all(t["code"] != code for t in after), \
        "напоминание придёт по уже отмеченной практике"


def _tx(db):
    from app.data.session import transaction
    return transaction(db)
