from __future__ import annotations

import json
from pathlib import Path

from app.core import astro
from app.core.chart_rendering import (
    InsufficientPrecisionError,
    clear_render_cache,
    render_chart_image,
    render_cache_stats,
)

OUT = Path(__file__).resolve().parents[1] / "docs" / "audit" / "chart_engine_smoke"
OUT.mkdir(parents=True, exist_ok=True)

clear_render_cache()
chart = astro.compute_chart(
    "1990-07-15", "10:30", "Rome", 41.9028, 12.4964, "Europe/Rome", time_known=True,
)
png, png_spec, hit1, key1 = render_chart_image(
    chart, birth_date="1990-07-15", birth_time="10:30", lat=41.9028, lon=12.4964,
    tz="Europe/Rome", variant="print", image_format="png", locale="ru",
)
png2, _, hit2, key2 = render_chart_image(
    chart, birth_date="1990-07-15", birth_time="10:30", lat=41.9028, lon=12.4964,
    tz="Europe/Rome", variant="print", image_format="png", locale="ru",
)
webp, webp_spec, _, _ = render_chart_image(
    chart, birth_date="1990-07-15", birth_time="10:30", lat=41.9028, lon=12.4964,
    tz="Europe/Rome", variant="share", image_format="webp", locale="en",
)
assert png.startswith(b"\x89PNG\r\n\x1a\n")
assert png == png2 and not hit1 and hit2 and key1 == key2
assert webp.startswith(b"RIFF") and webp[8:12] == b"WEBP"
assert png_spec.width == png_spec.height == 2400
assert webp_spec.width == webp_spec.height == 1600
unknown = astro.compute_chart(
    "1990-07-15", None, "Rome", 41.9028, 12.4964, "Europe/Rome", time_known=False,
)
try:
    render_chart_image(
        unknown, birth_date="1990-07-15", birth_time=None, lat=41.9028, lon=12.4964,
        tz="Europe/Rome", variant="compact", image_format="png", locale="ru",
    )
except InsufficientPrecisionError as exc:
    unknown_code = exc.code
else:
    raise AssertionError("unknown-time natal chart must not produce a wheel image")
result = {
    "png_bytes": len(png), "webp_bytes": len(webp), "cache": render_cache_stats(),
    "unknown_time_code": unknown_code,
}
(OUT / "adapter_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
