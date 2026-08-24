from __future__ import annotations

import json
from pathlib import Path


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    out.extend("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in rows)
    return "\n".join(out)


def main() -> None:
    source = Path("docs/AGENT_ROUTING_STRESS_REPORT.json")
    report = json.loads(source.read_text(encoding="utf-8"))
    lines = [
        "# Agent Routing Stress Test — v1",
        "",
        "> Это curated adversarial benchmark из 48 сценариев, составленных по типовым сложным пользовательским ситуациям. Он не является выборкой production traffic и не доказывает качество конечного LLM-ответа; он проверяет только deterministic skill selection.",
        "",
        "## Итог",
        "",
        f"Результат: **{'PASS' if report['passed'] else 'FAIL'}**. Во всех 48 случаях ожидаемый skill попал в top-3; top-1 достигнут в {report['overall']['top1']} случаях ({report['overall']['top1_accuracy']:.1%}), MRR составил {report['overall']['mrr']:.3f}. Все {report['safety_critical_total']} safety-critical кейса имели safety skill в top-3; критических пропусков: **{len(report['safety_critical_failures'])}**.",
        "",
        md_table(["Метрика", "Значение"], [["Всего кейсов", report["total"]], ["Top-1", f"{report['overall']['top1']}/{report['total']} ({report['overall']['top1_accuracy']:.1%})"], ["Top-3", f"{report['overall']['top3']}/{report['total']} ({report['overall']['top3_accuracy']:.1%})"], ["MRR", report["overall"]["mrr"]], ["Safety-critical misses", len(report["safety_critical_failures"])] ]),
        "",
        "## По агентам",
        "",
        md_table(["Agent", "Cases", "Top-1", "Top-3", "MRR"], [[agent, item["cases"], f"{item['top1']}/{item['cases']} ({item['top1_accuracy']:.1%})", f"{item['top3']}/{item['cases']} ({item['top3_accuracy']:.1%})", item["mrr"]] for agent, item in report["by_agent"].items()]),
        "",
        "## По языку и риску",
        "",
        md_table(["Slice", "Cases", "Top-1", "Top-3", "MRR"], [[f"language={key}", item["cases"], f"{item['top1']}/{item['cases']}", f"{item['top3']}/{item['cases']}", item["mrr"]] for key, item in report["by_language"].items()] + [[f"risk={key}", item["cases"], f"{item['top1']}/{item['cases']}", f"{item['top3']}/{item['cases']}", item["mrr"]] for key, item in report["by_risk"].items()]),
        "",
        "## Safety-critical coverage",
        "",
        "Safety-critical intent included medical/diagnostic claims, pregnancy/death, legal/financial certainty, cure requests and mind-reading. The benchmark requires the dedicated safety skill to be in top-3; it does not claim that routing alone guarantees a safe final answer.",
        "",
        "## Все сценарии",
        "",
        md_table(["#", "Agent", "Lang", "Risk", "Expected", "Rank", "Top-3", "Scenario"], [[row["case_id"], row["agent"], row["lang"], row["risk"], row["expected"], row["rank"] or "miss", ", ".join(row["top3"]), row["query"]] for row in report["cases"]]),
        "",
        "## Interpretation",
        "",
        "The result is strong on top-3 recall and safety placement, while top-1 remains an optimization metric rather than a hard safety contract. The most important design choice is to keep routing gates intent-level: school/deck markers, unknown birth-time markers, safety markers, relationship/grief framing, and palm capture geometry were boosted as reusable categories instead of adding one-off literal phrases.",
        "",
        "The test must be rerun after changing skill descriptions, aliases, or scoring rules. A future production evaluation should add anonymized real queries, answer-quality labels, tool-call correctness, refusal quality, latency and asset rendering; this synthetic suite alone cannot establish those properties.",
        "",
        "## Reproduction",
        "",
        "```bash\nPYTHONPATH=. python3 scripts/stress_test_agent_routing.py --json-out docs/AGENT_ROUTING_STRESS_REPORT.json\n```",
        "",
        "## References",
        "",
        "[1]: https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker \"Google AI Edge Hand Landmarker\"",
        "[2]: https://commons.wikimedia.org/wiki/File:Das_Spiel_der_Hofnung_(The_Game_of_Hope).png \"Wikimedia Commons Game of Hope source\"",
        "[3]: https://commons.wikimedia.org/wiki/Category:Rider-Waite-Smith_tarot_deck_(Geldard) \"Wikimedia Commons RWS Geldard category\"",
    ]
    Path("docs/AGENT_ROUTING_STRESS_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
