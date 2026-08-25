from __future__ import annotations

import asyncio
import json
import re
import subprocess
from pathlib import Path

from app.pdfgen import builder, render

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "audit" / "pdf_samples_v2" / "profiles"
MARKER_RE = re.compile(
    r"не науч|не является науч|not (scientific|a fact)|just for (fun|entertainment)|"
    r"лишь символ|не доказатель|не приговор|не предсказ|без фатал|выбор всегда за|"
    r"не заменяет|symbolic|not proof|for entertainment purposes|not literal",
    re.IGNORECASE,
)

PROFILES = (
    {
        "slug": "known_time",
        "name": "Анна / Anna",
        "birth_date": "1990-06-21",
        "birth_time": "14:30",
        "birth_city": "Казань",
    },
    {
        "slug": "date_only",
        "name": "Мария / Maria",
        "birth_date": "1987-11-03",
        "birth_time": None,
        "birth_city": "Москва",
    },
    {
        "slug": "evening_time",
        "name": "Елена / Elena",
        "birth_date": "2001-02-17",
        "birth_time": "21:10",
        "birth_city": "Санкт-Петербург",
    },
)


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    geo_map = {
        "Казань": (55.79, 49.12, "Europe/Moscow"),
        "Москва": (55.75, 37.62, "Europe/Moscow"),
        "Санкт-Петербург": (59.94, 30.31, "Europe/Moscow"),
    }

    async def fake_geo(city: str, *_args, **_kwargs):
        return geo_map[city]

    original_geo = builder.geo.resolve_city_async
    original_llm = builder.llm.enabled
    builder.geo.resolve_city_async = fake_geo
    builder.llm.enabled = lambda: False
    results: list[dict] = []
    try:
        for profile in PROFILES:
            for lang in ("ru", "en"):
                localized_name = profile["name"].split(" / ")[0 if lang == "ru" else 1]
                order = builder.Order(
                    name=localized_name,
                    birth_date=profile["birth_date"],
                    birth_time=profile["birth_time"],
                    birth_city=profile["birth_city"],
                    lang=lang,
                )
                html = await builder.generate(None, order, concurrency=1)
                stem = f"{profile['slug']}_{lang}"
                html_path = OUT / f"{stem}.html"
                pdf_path = OUT / f"{stem}.pdf"
                text_path = OUT / f"{stem}.txt"
                html_path.write_text(html, encoding="utf-8")
                actual = render.render_pdf(html, pdf_path)
                if actual.suffix != ".pdf":
                    raise RuntimeError(f"WeasyPrint unavailable for {stem}: {actual}")
                text = subprocess.check_output(["pdftotext", "-layout", str(actual), "-"], text=True)
                text_path.write_text(text, encoding="utf-8")
                info = subprocess.check_output(["pdfinfo", str(actual)], text=True)
                pages_match = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
                size_match = re.search(r"^File size:\s+(\d+)", info, re.MULTILINE)
                markers = sorted(set(m.group(0) for m in MARKER_RE.finditer(text)))
                result = {
                    "profile": profile["slug"],
                    "lang": lang,
                    "time_known": bool(profile["birth_time"]),
                    "pages": int(pages_match.group(1)) if pages_match else None,
                    "pdf_bytes": int(size_match.group(1)) if size_match else actual.stat().st_size,
                    "html_bytes": html_path.stat().st_size,
                    "text_chars": len(text),
                    "marker_hits": markers,
                    "pdf": str(actual.relative_to(ROOT)),
                    "text": str(text_path.relative_to(ROOT)),
                }
                results.append(result)
                print(json.dumps(result, ensure_ascii=False))
    finally:
        builder.geo.resolve_city_async = original_geo
        builder.llm.enabled = original_llm

    summary = {
        "profiles": len(PROFILES),
        "languages": ["ru", "en"],
        "documents": len(results),
        "all_pdf": all(item["pages"] is not None for item in results),
        "all_marker_free": all(not item["marker_hits"] for item in results),
        "min_pages": min(item["pages"] for item in results),
        "max_pages": max(item["pages"] for item in results),
        "results": results,
    }
    (OUT / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary["all_pdf"] or not summary["all_marker_free"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
