from __future__ import annotations

from pathlib import Path
import re

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "kerykeion"
OUT.mkdir(parents=True, exist_ok=True)

subject = AstrologicalSubjectFactory.from_birth_data(
    "Oracle QA", 1990, 6, 21, 14, 30, "Kazan", "RU",
    lat=55.7963, lng=49.1088, tz_str="Europe/Moscow", online=False,
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

results = []
for style in ("classic", "modern"):
    chart = ChartDrawer(
        chart_data=chart_data,
        style=style,
        theme="dark",
        show_zodiac_background_ring=True,
        show_degree_indicators=True,
        show_aspect_icons=True,
        custom_title=f"OracleAI QA — {style}",
        padding=20,
        auto_size=True,
    )
    svg = chart.generate_svg_string(remove_css_variables=False)
    target = OUT / f"{style}.svg"
    target.write_text(svg, encoding="utf-8")
    results.append({
        "style": style,
        "file": str(target),
        "bytes": len(svg.encode()),
        "has_svg": "<svg" in svg[:500],
        "width": re.search(r'<svg[^>]*width="([^"]+)', svg).group(1) if re.search(r'<svg[^>]*width="([^"]+)', svg) else None,
        "height": re.search(r'<svg[^>]*height="([^"]+)', svg).group(1) if re.search(r'<svg[^>]*height="([^"]+)', svg) else None,
        "circles": svg.count("<circle"),
        "paths": svg.count("<path"),
        "texts": svg.count("<text"),
        "has_house_labels": bool(re.search(r"house|House|cusp|Cusp", svg)),
        "has_aspect_layer": bool(re.search(r"aspect|Aspect", svg)),
        "has_dark_theme": "#" in svg or "var(--kerykeion" in svg,
    })

result_path = OUT / "smoke_results.json"

import json
result_path.write_text(json.dumps({"kerykeion": "5.12.9", "results": results}, indent=2) + "\n", encoding="utf-8")
print(result_path.read_text())
