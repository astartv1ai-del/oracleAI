"""Ядро без БД: колода, астрология, Матрица, совместимость, устойчивый сид."""
from __future__ import annotations

from datetime import date

from app.core import astro, tarot
from app.core.matrix import compute_matrix
from app.core.skills import _compat
from app.core.stable import stable_seed


def test_deck_has_78_cards():
    assert len(tarot.DECK) == 78
    majors = [c for c in tarot.DECK if c["arcana"] == "major"]
    assert len(majors) == 22


def test_draw_returns_distinct_cards_in_order():
    cards = tarot.draw(5)
    assert len(cards) == 5
    assert len({c["name"] for c in cards}) == 5
    assert all("reversed" in c for c in cards)


def test_draw_handles_large_spreads():
    """«Колесо года» — 12 карт: раскладов больше колоды быть не может."""
    cards = tarot.draw(12)
    assert len(cards) == 12
    assert len({c["name"] for c in cards}) == 12


def test_all_spreads_have_positions():
    for code, item in tarot.SPREADS.items():
        assert item["positions"], code
        assert item["tier"] in ("included", "premium"), code
        assert len(item["positions"]) <= len(tarot.DECK)


def test_spread_lookup_falls_back():
    assert tarot.spread("nope")["code"] == tarot.DEFAULT_SPREAD
    assert tarot.spread("celtic")["code"] == "celtic"
    assert tarot.spread_by_title("На отношения")["code"] == "love"


def test_sun_sign_boundaries():
    assert astro.sun_sign(date(1990, 6, 21))[0] in ("Близнецы", "Рак")
    assert astro.sun_sign(date(1990, 1, 5))[0] == "Козерог"
    assert astro.sun_sign(date(1990, 8, 1))[0] == "Лев"


def test_moon_phase_is_stable_for_a_date():
    first = astro.moon_phase(date(2026, 7, 26))
    second = astro.moon_phase(date(2026, 7, 26))
    assert first == second
    assert 1 <= first["day"] <= 31


def test_chart_never_raises_and_marks_mode():
    chart = astro.compute_chart("1990-06-21", "14:30", "Казань", 55.79, 49.12,
                                "Europe/Moscow")
    assert chart["mode"] in ("full", "lite")
    assert chart["sun"]["sign"]
    # лайт-режим обязан честно себя помечать, иначе клиентка не поймёт,
    # почему у неё нет домов
    if chart["mode"] == "lite":
        assert chart["note"]


def test_matrix_arcana_in_range():
    matrix = compute_matrix("1990-06-21")
    assert set(matrix) == {"personal", "spirit", "family", "destiny", "center",
                           "love", "money"}
    for item in matrix.values():
        assert 1 <= item["n"] <= 22
        assert item["arcana"] and item["meaning"]


def test_compat_is_deterministic_and_explained():
    first = _compat("1990-06-21", "1996-11-03")
    second = _compat("1990-06-21", "1996-11-03")
    assert first["score"] == second["score"]
    assert 35 <= first["score"] <= 98
    assert first["breakdown"] and first["verdict"]


def test_stable_seed_survives_restart():
    """crc32 вместо hash(): встроенный хеш строк рандомизируется при запуске,
    из-за чего карта дня менялась после рестарта процесса."""
    assert stable_seed("вопрос", 42) == stable_seed("вопрос", 42)
    assert stable_seed("вопрос", 42) != stable_seed("вопрос", 43)


def test_cards_text_marks_reversed():
    cards = [{"emoji": "🌙", "name": "Жрица", "meaning": "интуиция", "reversed": True}]
    text = tarot.cards_text(cards, ["Ответ"])
    assert "Ответ" in text and "перевёрнутая" in text
