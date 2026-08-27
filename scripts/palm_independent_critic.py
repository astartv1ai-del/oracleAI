"""Independent, context-light critic for the Palm/Mira accuracy gauntlet.

This is intentionally separate from the implementation tests: it reviews the
source contract from observable invariants and returns BLOCKED when a semantic
golden corpus is absent, rather than treating mocks as accuracy evidence.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(text: str, needle: str, label: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"missing {label}: {needle}")


def main() -> int:
    failures: list[str] = []
    palm = (ROOT / "app/core/palm.py").read_text(encoding="utf-8")
    landmarks = (ROOT / "app/core/palm_landmarks.py").read_text(encoding="utf-8")
    full_scope = (ROOT / "app/core/palm_full_scope.py").read_text(encoding="utf-8")
    skills = (ROOT / "app/core/skills.py").read_text(encoding="utf-8")
    ui = (ROOT / "miniapp/js/13-palm.js").read_text(encoding="utf-8")
    locale = (ROOT / "miniapp/js/12-misc.js").read_text(encoding="utf-8")
    tests = (ROOT / "tests/test_palm_gauntlet.py").read_text(encoding="utf-8")
    tests += "\n" + (ROOT / "tests/test_palm_integration.py").read_text(encoding="utf-8")

    for needle, label in [
        ("EVIDENCE_CONTRACT_VERSION", "versioned evidence contract"),
        ("EVIDENCE_STATES", "evidence state enum"),
        ("declared_content_type", "declared MIME input"),
        ("actual_mime", "signature MIME check"),
        ("n_frames", "animated-image rejection"),
        ("hard_cv_reject", "hard CV rejection"),
        ("multiple_hands", "multiple-hand boundary"),
        ("vision_skipped", "provider skip metric"),
        ("provider_content_stored", "provider content retention flag"),
        ("_UNTRUSTED_TEXT", "prompt-injection sanitizer"),
    ]:
        # The schema check below is handled by a direct source token because
        # the surrounding Python object is not evaluated here.
        if isinstance(needle, bool):
            continue
        require(palm, needle, label, failures)
    require(palm, '"additionalProperties": False', "strict closed schema", failures)
    require(palm, '"evidence_state"', "observation evidence state", failures)
    require(palm, '"requires_view"', "required view contract", failures)
    require(landmarks, "num_hands=2", "no arbitrary one-hand selection", failures)
    require(full_scope, '"status": "hand_hull_scoped"', "palm-region scope", failures)
    require(full_scope, '"raw_mask_stored": False', "raw mask non-retention", failures)
    require(skills, "PALM_LIMITATION", "Mira weak-evidence boundary", failures)
    require(ui, "PALM_I18N", "Palm RU/EN dictionary", failures)
    require(ui, "refreshPalmLocale", "Palm locale refresh hook", failures)
    require(ui, "folded-edge", "folded-edge guidance", failures)
    require(locale, "refreshPalmLocale", "language-switch integration", failures)
    for needle, label in [
        ("adversarial", "adversarial visual text case"),
        ("multiple_hands", "multiple hands case"),
        ("folded_edge", "folded edge case"),
        ("mismatched", "MIME mismatch case"),
        ("weak_evidence", "weak evidence case"),
    ]:
        require(tests, needle, label, failures)

    result = {
        "critic": "palm-independent-static-critic-v1",
        "blocking_failures": failures,
        "deterministic_contract": "PASS" if not failures else "BLOCKED",
        "semantic_accuracy": "BLOCKED: no consented/synthetic golden corpus with region labels and expected limitations",
        "ship_verdict": "BLOCKED" if failures else "SHIP WITH ACCURACY GATE",
        "reason": "A passing contract critic proves guardrails, not semantic palm-reading accuracy.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
