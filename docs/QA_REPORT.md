# Chart-engine migration QA report

**Дата:** 2026-08-25  
**Scope:** Mode P natal chart migration, not a public-launch approval.

## Evidence summary

| Area | Result | Evidence |
|---|---|---|
| Kerykeion → resvg spike | **PASS** | `docs/audit/chart_engine_smoke/known_time.png`, `dense_stellium.png`, JSON results; production now uses classic dark theme and no extra zodiac background ring |
| Glyph and visual readability | **PASS after CSS-variable fix** | Initial direct raster was black; `remove_css_variables=True` produced readable wheel artifacts |
| SVG safety envelope | **PASS** | No script, foreignObject, iframe, object or external/data URL references; internal fragment `<use>` is allowed |
| PNG/WebP output | **PASS** | Adapter contract asserts PNG signature, WebP RIFF/WEBP signature and expected dimensions |
| Unknown-time correctness | **PASS** | Typed `insufficient_precision`; no fake wheel generated |
| API auth/ownership | **PASS locally** | `tests/test_api.py -k chart_image`: private headers, ETag/304, PNG/WebP, allowlist and date-only state |
| PDF HTML/real artifact | **PASS locally** | `tests/test_pdfgen.py` plus synthetic WeasyPrint RU/EN PDFs: 2400×2400 classic-dark natal PNG, no technical pipeline caption, valid A4 PDF, latest RU output 10 pages, dedicated larger-type house page visually inspected at `audit/chart_engine_smoke/pdf_pages/user_fix/ru-06.png` |
| Selfcheck | **PASS locally** | `scripts/selfcheck.py` completed; live LLM probe remained disabled/offline as prior status records |
| JavaScript syntax | **PASS locally** | `node --check` across remaining Mini App modules |
| Legacy natal renderer removal | **PASS in product/test source grep** | No `nativitySvg` or `wheel_svg` symbols remain under `miniapp/`, `app/`, `scripts/` or `tests/`; historical ADR/docs references are intentional |
| Docker/target runtime | **OPEN** | Docker unavailable in current sandbox |
| Commercial licensing | **BLOCKED** | Kerykeion AGPL-3.0 and Swiss Ephemeris dual-license decision require owner/legal sign-off |

## Privacy and product-boundary checks

Birth input is sourced from the authenticated owner’s stored profile or canonical calculation metadata. It is not accepted as a chart-image GET parameter. Telegram `X-Init-Data` is sent in the request header; the Mini App uses `apiBlob()` and object URLs, then revokes those URLs after download/replacement. The API returns `image/png` or `image/webp` only. Raw SVG is local to the server adapter and is not persisted, logged or returned.

The server-side raster cache is bounded and process-local. Its key is an HMAC digest that incorporates engine, rasterizer, chart contract, precision, variant, locale and render dimensions. The cache does not use a birth date, time, city or Telegram ID as a filename or log field.

## Known limitations

The product currently enables exact natal image output only. Synastry, transit, composite and planetary-return images are documented as capabilities/candidates, not enabled features. Unknown-time profiles continue to receive structured placements and recovery copy rather than a visually authoritative wheel. The target production image must still prove the pinned rasterizer and PDF dependencies, and the licensing gate must be closed before public commercial release.

## References

[1]: CHART_ENGINE_DECISION.md "Mode P architectural decision"  
[2]: CHART_TYPE_CAPABILITIES.md "Chart capability matrix"  
[3]: CHART_ENGINE_LICENSING.md "Licensing and SBOM gate"  
[4]: PDF_AUDIT.md "PDF migration audit"  
[5]: audit/chart_engine_research_2026-08-25.md "Official-source engine research"
