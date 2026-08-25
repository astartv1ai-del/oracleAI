# PDF chart migration audit

**Дата:** 2026-08-25  
**Status:** local technical checks passed; target-image/Docker and commercial licensing gates remain open.

## New composition contract

The PDF report no longer embeds the bespoke natal `wheel_svg()` output. The natal chart is rendered server-side through Kerykeion 5.12.9 in the **classic dark theme** and resvg_py 0.5.0 with a matching `#0c0a1d` canvas, producing a **2400×2400 PNG** embedded as a data URI in a dedicated full-width `natal-print-section`. The extra zodiac background ring is disabled to reduce visual competition between the outer and inner rings. At the target 180mm print width this is approximately 339 DPI, above the requested 2000–2400px print envelope.

The Matrix remains a separate visual track and is not placed beside the natal chart. The overview grid contains facts and Matrix; the natal image receives its own page-break-before section. This avoids shrinking two unrelated diagrams into a side-by-side block and keeps the natal image legible in print.

## Boundary checks

| Check | Evidence |
|---|---|
| No natal `wheel_svg()` call | Source grep after migration returns no `nativitySvg` or `wheel_svg` symbols |
| Raw SVG not embedded for natal | PDF tests assert `data-contract-version="1"` is absent and natal block contains PNG data URI |
| Raster dimensions | `tests/test_pdfgen.py` asserts `width="2400" height="2400"` |
| Unknown-time behavior | `_natal_print_block()` emits a structured precision state and no fake wheel |
| RU/EN | `test_full_natal_report...` and `test_english_natal_report_is_localized` pass |
| Real PDF path | `app/pdfgen/render.py` remains the WeasyPrint conversion path; local `render.available()` is covered by selfcheck |

## Real synthetic evidence

The local WeasyPrint path generated RU and EN PDFs from fixed synthetic fixtures. The latest RU artifact is a valid A4 PDF with 10 pages. `pdftotext` found `Натальная карта`, `Куспиды домов`, `Ключевые аспекты` and `Матрица Судьбы`. The latest dedicated natal page is `docs/audit/chart_engine_smoke/pdf_pages/user_fix/ru-03.png`; it was visually inspected after switching to classic dark rendering, and the technical pipeline caption is absent. The latest house page is `docs/audit/chart_engine_smoke/pdf_pages/user_fix/ru-06.png`; all 12 houses fit on one dedicated page with larger typography and generous row spacing, without the former dense composition.

## Remaining evidence

A target production image must still be built and inspected with `pdfinfo`, `pdftotext`, page raster screenshots and font/image checks. Docker was unavailable in the current sandbox, so the final container smoke is an external blocker. The current tests establish HTML contract and real engine PNG generation, while the synthetic PDF artifact provides local visual evidence; neither replaces inspection of the final target deployment image.

## References

[1]: ../app/pdfgen/builder.py "PDF report assembly and print-image integration"  
[2]: ../app/pdfgen/layout.py "PDF HTML/CSS layout"  
[3]: ../app/pdfgen/render.py "WeasyPrint HTML-to-PDF wrapper"  
[4]: ../tests/test_pdfgen.py "PDF regression tests"  
[5]: CHART_ENGINE_DECISION.md "Mode P chart-engine decision"
