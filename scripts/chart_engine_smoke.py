from __future__ import annotations

import io
import json
import re
from pathlib import Path

from PIL import Image
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
import resvg_py


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "audit" / "chart_engine_smoke"
OUT.mkdir(parents=True, exist_ok=True)


def render_fixture(name: str, *, year: int, month: int, day: int, hour: int, minute: int,
                   lat: float, lon: float, tz: str, width: int = 1200, height: int = 1200) -> dict:
    subject = AstrologicalSubjectFactory.from_birth_data(
        name="fixture", year=year, month=month, day=day, hour=hour, minute=minute,
        lat=lat, lng=lon, tz_str=tz, online=False,
        zodiac_type="Tropical", houses_system_identifier="P",
        perspective_type="Apparent Geocentric",
    )
    data = ChartDataFactory.create_natal_chart_data(subject)
    svg = ChartDrawer(chart_data=data, theme="dark", style="classic").generate_wheel_only_svg_string(remove_css_variables=True)
    assert "<script" not in svg.lower()
    assert "<foreignobject" not in svg.lower()
    assert not re.search(r"(?:href|xlink:href)\s*=\s*['\"](?:https?:|data:|//)", svg, re.I)
    png = resvg_py.svg_to_bytes(svg_string=svg, background="#0c0a1d", width=width, height=height)
    png_path = OUT / f"{name}.png"
    png_path.write_bytes(png)
    with Image.open(io.BytesIO(png)) as image:
        image.load()
        png_size = image.size
        image.save(OUT / f"{name}.webp", format="WEBP", lossless=True, method=6)
    return {
        "fixture": name,
        "svg_bytes": len(svg.encode("utf-8")),
        "png_bytes": len(png),
        "png_dimensions": list(png_size),
        "webp_bytes": (OUT / f"{name}.webp").stat().st_size,
        "svg_has_script": "<script" in svg.lower(),
        "svg_has_external_href": bool(re.search(r"(?:href|xlink:href)\s*=\s*['\"](?:https?:|data:|//)", svg, re.I)),
    }


results = [
    render_fixture("known_time", year=1990, month=7, day=15, hour=10, minute=30,
                   lat=41.9028, lon=12.4964, tz="Europe/Rome"),
    render_fixture("dense_stellium", year=2000, month=1, day=6, hour=12, minute=0,
                   lat=47.6038, lon=-122.3301, tz="America/Los_Angeles"),
]
(OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))
