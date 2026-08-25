from __future__ import annotations

import json
from pathlib import Path

from app.core.agents.routing import route_agent

CASES = [
    ("ru-astro-saturn", "Что значит мой Сатурн в 10 доме?", "astro", True),
    ("ru-astro-nodes", "Раху и Кету: куда мне расти?", "astro", True),
    ("ru-astro-compat", "Сделай синастрию и объясни аспекты Венеры", "astro", True),
    ("ru-astro-date", "Транзит Юпитера и выбор даты запуска", "astro", True),
    ("en-astro-natal", "Tell me about my natal chart and rising sign", "astro", True),
    ("en-astro-house", "What does my Venus in the seventh house mean?", "astro", True),
    ("mixed-astro", "Раху and Ketu in my natal chart", "astro", True),
    ("ru-tarot", "Сделай расклад Таро на решение", "tarot", True),
    ("ru-tarot-reversed", "Объясни перевёрнутые карты в раскладе", "tarot", True),
    ("en-tarot", "What does this tarot spread show?", "tarot", True),
    ("mixed-tarot", "Tarot расклад для journal reflection", "tarot", True),
    ("ru-lenormand", "Хочу расклад Ленорман", "tarot", True),
    ("ru-palm", "Прочитай ладонь по фото, линия сердца", "chiromant", True),
    ("en-palm", "Can you analyze my palm photo?", "chiromant", True),
    ("mixed-palm", "Фото ладони и heart line", "chiromant", True),
    ("ru-palm-mounts", "Что значат холмы на ладони?", "chiromant", True),
    ("ru-oracle-practice", "Подбери практику для спокойствия", "oracle", False),
    ("ru-oracle-diary", "Помоги с дневником и границами", "oracle", False),
    ("en-oracle-values", "Help me reflect on my values conflict", "oracle", False),
    ("mixed-oracle", "Нужен ritual для journal", "oracle", False),
    ("ambiguous-tarot-astro", "Сделай расклад Таро и объясни мой натальный Сатурн", "oracle", False),
    ("ambiguous-palm-tarot", "Фото ладони и расклад на отношения", "oracle", False),
    ("no-signal", "Помоги мне понять, что делать дальше", "oracle", False),
    ("off-topic", "Помоги написать SQL-запрос для отчёта", "oracle", False),
]


def main() -> int:
    results = []
    for case_id, text, expected, should_auto in CASES:
        decision = route_agent(text)
        ok = decision.agent == expected and decision.auto_route == should_auto
        results.append({
            "id": case_id,
            "text": text,
            "expected": expected,
            "actual": decision.agent,
            "auto_route": decision.auto_route,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "candidates": list(decision.candidates),
            "ok": ok,
        })
    summary = {
        "cases": len(results),
        "passed": sum(item["ok"] for item in results),
        "accuracy": sum(item["ok"] for item in results) / len(results),
        "auto_route_passed": sum(item["ok"] and item["auto_route"] for item in results),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    out = Path("docs/audit/agent_routing_2026-08-25.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if summary["passed"] == summary["cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
