from __future__ import annotations

from scripts.evaluate_llm import evaluate_case
from scripts.generate_eval_set import _sample_response, build


def test_golden_set_has_expected_size_and_scenarios():
    rows = build()
    assert len(rows) == 140
    assert {row["scenario"] for row in rows} == {
        "general", "natal_full", "natal_date_only", "tarot_choice",
        "tarot_relationship", "compatibility", "daily", "safety",
        "palm_quality", "palm_reading", "palm_prompt_injection", "palm_safety",
    }
    assert {row["language"] for row in rows} == {"ru", "en"}


def test_synthetic_fixture_has_no_critical_violations():
    results = [evaluate_case(row, _sample_response(row)) for row in build()]
    assert not any(result["forbidden_hits"] for result in results)
    assert min(result["score"] for result in results) >= 0.75
    assert all(result["latency"] == 1 for result in results)
