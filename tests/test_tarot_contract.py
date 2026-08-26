from __future__ import annotations

from app.core import tarot


def test_tarot_deck_has_78_unique_cards_and_four_minor_suits():
    deck = tarot.full_deck()
    assert len(deck) == 78
    assert len({card["img"] for card in deck}) == 78
    assert sum(card["arcana"] == "major" for card in deck) == 22
    assert sum(card["arcana"] == "minor" for card in deck) == 56
    assert {card["suit"] for card in deck if card["arcana"] == "minor"} == set(tarot.SUITS)


def test_seeded_draw_is_replayable_but_reversal_is_part_of_evidence():
    first = tarot.draw(10, seed="synthetic-seed")
    second = tarot.draw(10, seed="synthetic-seed")
    assert first == second
    assert len({card["img"] for card in first}) == 10
    ledger = tarot.reading_ledger(first, "three")
    assert ledger["deck_id"] == "rws-78-v1"
    assert all(entry["orientation"] in {"upright", "reversed"} for entry in ledger["entries"])
    flipped = [dict(card, reversed=not card["reversed"]) for card in first]
    assert tarot.reading_ledger(flipped, "three")["checksum"] != ledger["checksum"]


def test_unknown_lenormand_is_not_silently_promised_as_tarot():
    assert "lenormand" not in tarot.SPREADS
    fallback = tarot.spread("lenormand")
    assert fallback["code"] == tarot.DEFAULT_SPREAD
    assert fallback["title"] == tarot.SPREADS[tarot.DEFAULT_SPREAD]["title"]
