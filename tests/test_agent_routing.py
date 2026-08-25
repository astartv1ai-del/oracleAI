from __future__ import annotations

import pytest

from app.core.agents.routing import route_agent


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Что значит мой Сатурн в 10 доме?", "astro"),
        ("Tell me about my natal chart and rising sign", "astro"),
        ("Раху and Ketu: куда мне расти?", "astro"),
        ("Сделай расклад Таро на решение", "tarot"),
        ("What does this tarot spread show?", "tarot"),
        ("Прочитай ладонь по фото, heart line", "chiromant"),
        ("Can you analyze my palm photo?", "chiromant"),
        ("Подбери практику для спокойствия", "oracle"),
        ("Помоги с дневником и границами", "oracle"),
    ],
)
def test_clear_multilingual_domain_routes(text, expected):
    decision = route_agent(text)
    assert decision.agent == expected
    if expected != "oracle":
        assert decision.auto_route is True
        assert decision.confidence >= 0.76


def test_ambiguous_mixed_domain_stays_default_and_explains_why():
    decision = route_agent("Сделай расклад Таро и объясни мой натальный Сатурн")
    assert decision.agent == "oracle"
    assert decision.auto_route is False
    assert "ambiguous" in decision.reason
    assert set(("astro", "tarot")) <= set(decision.candidates)


def test_no_signal_stays_default():
    decision = route_agent("Помоги мне разобраться, что делать дальше")
    assert decision.agent == "oracle"
    assert decision.auto_route is False
    assert decision.confidence == 0.5


def test_route_decision_is_serializable():
    data = route_agent("my natal chart").as_dict()
    assert data["agent"] == "astro"
    assert isinstance(data["candidates"], list)
    assert data["auto_route"] is True
