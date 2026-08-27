"""Offline P2 quality gate for repository-level product trust checks."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _check(name: str, ok: bool, detail: str) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def _locale_keys(source: str, locale: str) -> set[str]:
    """Extract keys from the primary I18N dictionary, not profile dictionaries."""
    dictionary = re.search(
        r"const I18N = \{\s*ru: \{(.*?)\n\s*\},\s*en: \{(.*?)\n\s*\},",
        source, re.S,
    )
    if not dictionary:
        return set()
    body = dictionary.group(1 if locale == "ru" else 2)
    return set(re.findall(r"(?:^|,)\s*([A-Za-z][A-Za-z0-9_]*)\s*:", body))


def run_checks() -> list[dict]:
    checks: list[dict] = []
    required = [
        ROOT / "docs/LOCAL_BROWSER_BASELINE.md",
        ROOT / "docs/VISUAL_QA_A11Y_REPORT.md",
        ROOT / "docs/LOCALIZATION_GLOSSARY.md",
        ROOT / "docs/PDF_TEMPLATE_CATALOG.md",
        ROOT / "docs/PALM_ENGINE_RESEARCH.md",
        ROOT / "scripts/benchmark_product_performance.py",
        ROOT / "scripts/check_repository_hygiene.py",
    ]
    checks.append(_check(
        "tracked_evidence", all(path.is_file() for path in required),
        "all required P2 evidence and contract files exist",
    ))

    hygiene = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_repository_hygiene.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    checks.append(_check("markdown_hygiene", hygiene.returncode == 0,
                         hygiene.stdout.strip() or hygiene.stderr.strip()))

    utils = (ROOT / "miniapp/js/01-utils.js").read_text(encoding="utf-8")
    ru_keys = _locale_keys(utils, "ru")
    en_keys = _locale_keys(utils, "en")
    checks.append(_check(
        "locale_key_parity", ru_keys == en_keys and bool(ru_keys),
        f"ru={len(ru_keys)} en={len(en_keys)} missing_ru={sorted(en_keys - ru_keys)[:5]} "
        f"missing_en={sorted(ru_keys - en_keys)[:5]}",
    ))

    templates = (ROOT / "docs/PDF_TEMPLATE_CATALOG.md").read_text(encoding="utf-8")
    required_template_terms = ("natal", "synastry", "tarot", "localized", "snapshot")
    template_missing = [term for term in required_template_terms if term not in templates.casefold()]
    checks.append(_check(
        "report_template_contract", not template_missing,
        f"missing={template_missing or 'none'}",
    ))

    benchmark = subprocess.run(
        [sys.executable, str(ROOT / "scripts/benchmark_product_performance.py")],
        cwd=ROOT, env={**__import__("os").environ, "LLM_PROVIDER": "off", "EMBED_MODEL": ""},
        capture_output=True, text=True, check=False,
    )
    try:
        payload = json.loads(benchmark.stdout)
        perf_ok = benchmark.returncode == 0 and payload.get("pass") is True
        detail = f"pass={payload.get('pass')} metrics={len(payload.get('metrics', {}))}"
    except (TypeError, ValueError):
        perf_ok = False
        detail = (benchmark.stdout + benchmark.stderr).strip()[-400:]
    checks.append(_check("benchmark_reproducibility", perf_ok, detail))

    visual = (ROOT / "docs/VISUAL_QA.md").read_text(encoding="utf-8")
    checks.append(_check(
        "visual_evidence_is_tracked",
        "LOCAL_BROWSER_BASELINE.md" in visual and "VISUAL_QA_A11Y_REPORT.md" in visual,
        "visual QA points to tracked summaries rather than absent raw artifacts",
    ))
    return checks


def main() -> int:
    checks = run_checks()
    print(json.dumps({"checks": checks, "pass": all(item["pass"] for item in checks)},
                     ensure_ascii=False, indent=2))
    return 0 if all(item["pass"] for item in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
