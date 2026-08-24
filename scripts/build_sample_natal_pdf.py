from __future__ import annotations

import asyncio
from pathlib import Path

from app.pdfgen import builder, render


async def main() -> None:
    async def fake_geo(*_args, **_kwargs):
        return 55.79, 49.12, "Europe/Moscow"

    original_geo = builder.geo.resolve_city_async
    original_llm = builder.llm.enabled
    builder.geo.resolve_city_async = fake_geo
    builder.llm.enabled = lambda: False
    try:
        for lang, suffix in (("ru", "ru"), ("en", "en")):
            order = builder.Order(
                name="Анна" if lang == "ru" else "Anna",
                birth_date="1990-06-21", birth_time="14:30", birth_city="Казань",
                lang=lang,
            )
            html = await builder.generate(None, order, concurrency=1)
            html_path = Path(f"/home/ubuntu/oracleAI-sample-natal-report-{suffix}.html")
            pdf_path = Path(f"/home/ubuntu/oracleAI-sample-natal-report-{suffix}.pdf")
            html_path.write_text(html, encoding="utf-8")
            actual = render.render_pdf(html, pdf_path)
            print(f"lang={lang} html={html_path}")
            print(f"lang={lang} rendered={actual}")
            print(f"lang={lang} pdf_available={render.available()}")
            print(f"lang={lang} html_bytes={html_path.stat().st_size}")
            if actual.suffix == ".pdf":
                print(f"lang={lang} pdf_bytes={actual.stat().st_size}")
    finally:
        builder.geo.resolve_city_async = original_geo
        builder.llm.enabled = original_llm


if __name__ == "__main__":
    asyncio.run(main())
