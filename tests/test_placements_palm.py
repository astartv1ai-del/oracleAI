from __future__ import annotations

from app.core import palm, placements
from app.core.agents.specs import codes, get
from app.core.skills import SKILLS


BIRTH = {
    "birth_date": "1990-06-21",
    "birth_time": "12:00",
    "city": "Moscow",
    "lat": 55.75,
    "lon": 37.62,
    "tz": "Europe/Moscow",
    "time_known": True,
}


def test_all_requested_placements_are_deterministic():
    codes = [
        "asteroid_sign", "chiron_sign", "juno_sign", "jupiter_sign", "mars_sign",
        "mercury_sign", "moon_sign", "neptune_sign", "north_node_sign", "pluto_sign",
        "rising_sign", "saturn_sign", "south_node_sign", "uranus_sign", "venus_sign",
    ]
    for code in codes:
        result = placements.calculate_placement(code, **BIRTH)
        assert result["source"] == "swiss_ephemeris"
        assert result["precision"] == "exact"
        if code == "asteroid_sign":
            assert {item["point"] for item in result["points"]} == {"Ceres", "Vesta", "Pallas"}
        else:
            assert result.get("sign")


def test_unknown_time_never_exposes_rising_or_houses():
    result = placements.calculate_placement(
        "rising_sign", BIRTH["birth_date"], BIRTH["birth_time"], BIRTH["city"],
        BIRTH["lat"], BIRTH["lon"], BIRTH["tz"], time_known=False,
    )
    assert result["precision"] == "insufficient"
    assert "точные" in result["error"]
    bundle = placements.calculate_placement(
        "natal_chart", BIRTH["birth_date"], BIRTH["birth_time"], BIRTH["city"],
        BIRTH["lat"], BIRTH["lon"], BIRTH["tz"], time_known=False,
    )
    asc = next(item for item in bundle["points"] if item["code"] == "rising_sign")
    assert asc["precision"] == "insufficient"
    assert "sign" not in asc


def test_life_path_preserves_master_number():
    result = placements.life_path("2000-01-08")
    assert result["value"] == 11
    assert result["master_number"] is True
    assert result["trace"] == [11]


def test_chinese_zodiac_uses_lunisolar_boundary():
    before = placements.chinese_zodiac("2024-02-09")
    after = placements.chinese_zodiac("2024-02-10")
    assert before["boundary_adjusted"] is True
    assert before["animal"] == "Кролик"
    assert after["animal"] == "Дракон"
    assert after["element"] == "Дерево"


def test_palm_normalizer_sanitizes_forbidden_claims_and_keeps_confidence():
    result = palm._normalize({
        "status": "complete",
        "hand_detected": True,
        "hand_side": "right",
        "image_quality": {"score": 0.9, "issues": []},
        "observations": [{
            "topic": "heart_line", "visibility": "clear",
            "summary": "это диагноз болезни и точный прогноз смерти",
            "confidence": 1.5,
        }],
        "interpretive_prompts": ["Что помогает тебе говорить о чувствах?"],
    }, {"score": 0.9, "issues": []})
    assert result["status"] == "complete"
    assert result["observations"][0]["confidence"] == 1.0
    assert "диагноз" not in result["observations"][0]["summary"]
    assert "model_claim_sanitized" in result["safety_flags"]


def test_chiromant_is_registered_with_palm_tools():
    assert "chiromant" in codes()
    agent = get("chiromant")
    assert agent is not None
    assert {"get_palm_reading", "request_better_palm_photo"}.issubset(agent.skills)
    assert {"get_placement", "get_all_placements", "get_life_path", "get_chinese_zodiac"}.issubset(SKILLS)
