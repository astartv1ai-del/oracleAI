from __future__ import annotations

import json
from app.core.astro import compute_chart

chart = compute_chart(
    "1990-06-21", "14:30", "Казань", 55.79, 49.12, "Europe/Moscow", time_known=True
)
print(json.dumps({
    "mode": chart.get("mode"),
    "precision": chart.get("precision"),
    "planets": len(chart.get("planets", [])),
    "nodes": [n.get("name") for n in chart.get("nodes", [])],
    "additional_points": [p.get("name") for p in chart.get("additional_points", [])],
    "rahu": chart.get("lunar_nodes", {}).get("rahu", {}).get("name"),
    "ketu": chart.get("lunar_nodes", {}).get("ketu", {}).get("name"),
    "error": chart.get("error"),
}, ensure_ascii=False, indent=2))
