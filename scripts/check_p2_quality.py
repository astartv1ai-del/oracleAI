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
        ROOT / "docs/P2_RELEASE_CHECKLIST.md",
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

    glossary = (ROOT / "docs/LOCALIZATION_GLOSSARY.md").read_text(encoding="utf-8").casefold()
    glossary_terms = ("ru", "en", "pluralization", "long labels", "glyph")
    missing_glossary = [term for term in glossary_terms if term not in glossary]
    checks.append(_check(
        "localization_glossary", not missing_glossary,
        f"missing={missing_glossary or 'none'}",
    ))

    templates = (ROOT / "docs/PDF_TEMPLATE_CATALOG.md").read_text(encoding="utf-8")
    required_template_terms = ("natal", "synastry", "tarot", "localized", "snapshot")
    template_missing = [term for term in required_template_terms if term not in templates.casefold()]
    checks.append(_check(
        "report_template_contract", not template_missing,
        f"missing={template_missing or 'none'}",
    ))

    def run_script(name: str) -> tuple[bool, str]:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / name)],
            cwd=ROOT, env={**__import__("os").environ, "LLM_PROVIDER": "off", "EMBED_MODEL": ""},
            capture_output=True, text=True, check=False,
        )
        detail = (result.stdout or result.stderr).strip().splitlines()
        return result.returncode == 0, detail[-1] if detail else "no output"

    for check_name, script_name in (
        ("accessibility_design_contract", "check_design_contract.py"),
        ("visual_contrast_contract", "check_visual_contrast.py"),
        ("report_golden_cases", "check_pdf_golden_cases.py"),
        ("backup_restore_isolation", "check_backup_restore_drill.py"),
    ):
        ok, detail = run_script(script_name)
        checks.append(_check(check_name, ok, detail))

    palm_repo = (ROOT / "app/repo/palm.py").read_text(encoding="utf-8")
    palm_contract = all(marker in palm_repo for marker in (
        "image_sha256=NULL", "image_size=NULL", "analysis_json=NULL", "status='deleted'",
    ))
    checks.append(_check(
        "palm_retention_contract", palm_contract,
        "deleted palm readings scrub analysis and image metadata" if palm_contract
        else "delete_reading does not scrub all sensitive fields",
    ))

    payment_ui = (ROOT / "miniapp/js/17-payments.js").read_text(encoding="utf-8")
    payment_dictionary = re.search(
        r"const PAYMENT_I18N = \{\s*ru: \{(.*?)\n\s*\},\s*en: \{(.*?)\n\s*\},",
        payment_ui, re.S,
    )
    payment_ru = set(re.findall(r"(?:^|,)\s*([A-Za-z][A-Za-z0-9_]*)\s*:", payment_dictionary.group(1))) if payment_dictionary else set()
    payment_en = set(re.findall(r"(?:^|,)\s*([A-Za-z][A-Za-z0-9_]*)\s*:", payment_dictionary.group(2))) if payment_dictionary else set()
    checks.append(_check(
        "payment_locale_key_parity", payment_ru == payment_en and bool(payment_ru),
        f"ru={len(payment_ru)} en={len(payment_en)} missing_ru={sorted(payment_en - payment_ru)} missing_en={sorted(payment_ru - payment_en)}",
    ))
    payment_contract = all(marker in payment_ui for marker in (
        "Доступ откроется только после подтверждения провайдера",
        "История заказов", "payment-retry", "payProduct", "aria-label=",
    ))
    checks.append(_check(
        "payment_ux_contract", payment_contract,
        "provider-confirmed entitlement, retry, order history and accessible payment actions are present"
        if payment_contract else "payment safety or recovery marker is missing",
    ))

    release = (ROOT / "docs/P2_RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    release_contract = all(f"P2-00{i}" in release for i in range(1, 9)) and "OPEN — manual" in release
    checks.append(_check(
        "manual_release_register", release_contract,
        "all eight P2 rows and explicit manual/external status are recorded"
        if release_contract else "P2 release register is incomplete",
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
