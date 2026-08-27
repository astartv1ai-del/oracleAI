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
        "asteroid_sign", "ceres_sign", "chiron_sign", "juno_sign", "jupiter_sign",
        "ketu_sign", "lilith_sign", "mars_sign", "mercury_sign", "moon_sign",
        "neptune_sign", "north_node_sign", "pallas_sign", "pluto_sign", "rahu_sign",
        "rising_sign", "saturn_sign", "south_node_sign", "uranus_sign", "venus_sign",
        "vesta_sign",
    ]
    for code in codes:
        result = placements.calculate_placement(code, **BIRTH)
        assert result["source"] == "swiss_ephemeris"
        assert result["engine"] == "Swiss Ephemeris via Kerykeion"
        assert result["zodiac_type"] == "Tropical"
        assert result["house_system"] == "P"
        assert result["house_system_name"] == "Placidus"
        assert result["perspective_type"] == "Apparent Geocentric"
        assert result["node_mode"] == "true"
        assert result["precision"] == "exact"
        if code == "asteroid_sign":
            assert {item["point"] for item in result["points"]} == {"Ceres", "Vesta", "Pallas"}
        else:
            assert result.get("sign")
            assert result["degree_exact"] is not None
            assert result["abs_degree_exact"] is not None


def test_explicit_node_aliases_are_same_true_node_facts():
    rahu = placements.calculate_placement("rahu_sign", **BIRTH)
    north = placements.calculate_placement("north_node_sign", **BIRTH)
    ketu = placements.calculate_placement("ketu_sign", **BIRTH)
    south = placements.calculate_placement("south_node_sign", **BIRTH)
    assert rahu["point"] == north["point"] == "True_North_Lunar_Node"
    assert ketu["point"] == south["point"] == "True_South_Lunar_Node"
    assert rahu["abs_degree_exact"] == north["abs_degree_exact"]
    assert ketu["abs_degree_exact"] == south["abs_degree_exact"]


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
    assert set(result["lines"]) >= {"life", "head", "heart", "fate", "sun", "mercury",
                                      "girdle_of_venus", "ring_of_solomon", "ring_of_apollo",
                                      "via_lasciva", "mars_lines", "influence_lines", "bracelets",
                                      "relationship", "children", "travel"}
    assert result["lines"]["fate"]["visibility"] == "not_visible"
    assert set(result["mounts"]) == {"venus", "jupiter", "saturn", "apollo", "mercury", "moon", "mars"}
    assert set(result["fingers"]) == {"thumb", "index", "middle", "ring", "little"}
    assert result["markings"] == []


def test_chiromant_is_registered_with_palm_tools():
    assert "chiromant" in codes()
    agent = get("chiromant")
    assert agent is not None
    assert set(agent.skills) == {"activate_skill", "palm_scanner", "palm_photo_guide", "palm_history"}
    assert not ({"draw_tarot", "get_chart", "get_matrix", "get_transits"} & set(agent.skills))
    assert {"get_placement", "get_all_placements", "get_life_path", "get_chinese_zodiac"}.issubset(SKILLS)


def test_palm_normalizer_coerces_model_enums_and_sanitizes_quality_fields():
    result = palm._normalize({
        "status": "complete", "hand_detected": True, "hand_side": "future",
        "image_quality": {"score": "0.9", "issues": ["диагноз болезни"]},
        "observations": [{
            "topic": "medical_claim", "visibility": "certain",
            "summary": "обычная линия", "confidence": "not-a-number",
        }],
        "safety_flags": ["смерть неизбежна"],
    }, {"score": "0.9", "issues": ["диагноз болезни"]})
    observation = result["observations"][0]
    assert observation["topic"] == "unknown"
    assert observation["visibility"] == "unclear"
    assert observation["confidence"] == 0.0
    assert result["hand_side"] == "unknown"
    assert "диагноз" not in result["image_quality"]["issues"][0]
    assert "смерть" not in result["safety_flags"][0]


def test_palm_response_format_is_strict_and_closed():
    schema = palm.PALM_RESPONSE_FORMAT["json_schema"]
    root = schema["schema"]
    assert schema["strict"] is True
    assert root["additionalProperties"] is False
    assert set(root["required"]) == set(root["properties"])
    assert root["properties"]["status"]["enum"] == ["complete", "needs_photo"]
    for section in ("mounts", "fingers"):
        nested = root["properties"][section]
        assert nested["additionalProperties"] is False
        assert set(nested["required"]) == set(nested["properties"])
    lines = root["properties"]["lines"]
    assert lines["additionalProperties"] is False
    assert {"life", "head", "heart", "fate", "sun", "mercury", "girdle_of_venus",
            "ring_of_solomon", "ring_of_apollo", "via_lasciva", "mars_lines",
            "influence_lines", "bracelets", "relationship", "children", "travel"}.issubset(lines["required"])
    for extra in ("children", "travel", "mercury", "girdle_of_venus", "ring_of_solomon",
                  "ring_of_apollo", "via_lasciva", "mars_lines", "influence_lines", "bracelets"):
        assert extra in lines["properties"]
    assert "markings" in root["required"]
    assert "photo_assessment" in root["required"]
    assert root["properties"]["photo_assessment"]["properties"]["view_type"]["enum"] == [
        "open_palm", "folded_edge", "unclear"]
