from pathlib import Path

from scripts.stress_test_agent_routing import run
from app.core.tarot_assets import validate_assets


def test_adversarial_routing_stress_has_full_top3_and_no_safety_misses():
    report = run()
    assert report["total"] >= 40
    assert report["overall"]["top3"] == report["total"]
    assert report["safety_critical_failures"] == []
    assert report["passed"] is True


def test_all_enabled_deck_manifests_and_local_assets_are_valid():
    report = validate_assets(Path(__file__).parents[1])
    assert report["ok"] is True, report["errors"]
    assert {item["manifest_cards"] for item in report["decks"]} == {36, 78}
