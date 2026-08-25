from __future__ import annotations

import re
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    name="fixture", year=1990, month=7, day=15, hour=10, minute=30,
    lat=41.9028, lng=12.4964, tz_str="Europe/Rome", online=False,
    zodiac_type="Tropical", houses_system_identifier="P",
    perspective_type="Apparent Geocentric",
)
svg = ChartDrawer(
    chart_data=ChartDataFactory.create_natal_chart_data(subject),
    chart_language="RU", style="modern",
).generate_wheel_only_svg_string(remove_css_variables=True, style="modern")
for pattern in [
    r"<(script|foreignObject|iframe|object|use)\\b",
    r"(?:href|xlink:href)\\s*=\\s*['\"](?:https?:|data:|//)",
]:
    print(pattern, re.findall(pattern, svg, re.I)[:20])
for line in svg.splitlines():
    if any(token in line.lower() for token in ("<use", "href=", "xlink:href", "foreignobject", "<script")):
        print(line[:500])
