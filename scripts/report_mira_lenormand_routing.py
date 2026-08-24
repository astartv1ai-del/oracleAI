from __future__ import annotations

import json
from pathlib import Path

from app.core.agents.file_loader import profile_for_legacy, select_skills
from scripts.benchmark_mira_lenormand import CASES

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    rows = []
    for code, query, expected in CASES:
        profile = profile_for_legacy(code)
        names = [skill.name for skill in select_skills(profile, query, 3)]
        rank = names.index(expected) + 1 if expected in names else None
        rows.append((code, query, expected, names, rank))
    passed = sum(rank is not None for *_, rank in rows)
    top1 = sum(rank == 1 for *_, rank in rows)
    lines = [
        "# Mira / Madame Lenormand skill routing benchmark",
        "",
        "**Benchmark:** 20 difficult RU/EN/code-switched requests; expected skill must be present in bounded top-3.",
        "",
        f"| Metric | Result |\n| --- | ---: |\n| Cases | {len(rows)} |\n| Top-3 expected-skill inclusion | {passed}/{len(rows)} ({passed / len(rows):.1%}) |\n| Top-1 | {top1}/{len(rows)} ({top1 / len(rows):.1%}) |",
        "",
        "The benchmark measures routing, not interpretation quality. A top-3 hit means the skill is available to the downstream context resolver; top-1 is an improvement metric, not a promise that every real-world paraphrase will route identically.",
        "",
        "| # | Agent | Request | Expected | Actual top-3 | Rank |",
        "| ---: | --- | --- | --- | --- | ---: |",
    ]
    for index, (code, query, expected, names, rank) in enumerate(rows, 1):
        top3 = " → ".join(f"`{name}`" for name in names)
        safe_query = query.replace("|", "\\|")
        lines.append(f"| {index} | `{code}` | {safe_query} | `{expected}` | {top3} | {rank or 'miss'} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Mira cases cover visual evidence, line topology, school comparison, capture/rectification, photo comparison and safety. Madame Lenormand cases cover card ledger, adjacent combinations, question-to-spread, proof boundaries, reversals, high-risk reframing and Celtic Cross position discipline.",
        "",
        "The routing fixes deliberately use domain intent signals and preserve legacy behavior: a generic `расклад таро` still routes to `three-card-spread`, while explicit ledger/combinations/proof requests activate the new specialist skills.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "PYTHONPATH=. python3 scripts/benchmark_mira_lenormand.py",
        "PYTHONPATH=. python3 scripts/check_agent_quality.py",
        "```",
        "",
    ])
    target = ROOT / "docs" / "MIRA_LENORMAND_ROUTING_BENCHMARK.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"cases": len(rows), "top3_passed": passed,
                      "top1_passed": top1, "top3_accuracy": round(passed / len(rows), 3),
                      "top1_accuracy": round(top1 / len(rows), 3),
                      "report": str(target)}, ensure_ascii=False, indent=2))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
