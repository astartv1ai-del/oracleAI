# OracleAI Engine integration audit

**Дата:** 2026-08-27
**Ветка:** `master`
**Канонический путь:** `raw input → normalize → ChartRequest → OracleKerykeionEngine → Kerykeion → Swiss Ephemeris → validator → calculation contract → consumers`

## 1. Проверенная карта callers

| Caller/surface | Используемый путь | Проверенный статус |
|---|---|---|
| `/api/chart` GET/POST | `astro.compute_chart` / `compute_chart_async` | Canonical normalization, validation, fingerprints and provenance. |
| Onboarding | `astro.compute_chart_async` | Same canonical chart path before profile persistence. |
| Chart products | `astro.compute_chart` and product validators | Same input semantics; exact product fields validated. |
| Specialized placements | `astro.compute_chart` | No separate placement calculation path; legacy response shape preserved. |
| PDF builder | `astro.compute_chart` and evidence snapshot | Same calculation metadata reaches report generation. |
| Golden/domain QA scripts | `astro.compute_chart` | Deterministic corpus uses tracked generator and explicit precision cases. |
| LLM/agent evidence | Structured chart/product evidence | LLM receives facts and limitations; it does not calculate placements. |
| Chart image | Validated saved chart snapshot → render-only Kerykeion drawer | Image rendering is presentation-only; it now prefers snapshot input, checks stale config and keys cache by request/config/runtime fingerprints. |

The only direct Kerykeion imports in application code are the canonical numerical adapter (`app/core/astro.py`) and the render-only SVG adapter (`app/core/chart_rendering.py`). The latter cannot emit raw SVG or calculate a separate public chart: it requires `precision=exact`, validated snapshot conventions, and returns raster bytes only.

## 2. Timing and precision checks

The public chart calculation happens before cache write, API response, PDF/evidence hand-off and product interpretation. Fresh and cached results pass the same output validator. Date-only, unknown-time and ambiguous-DST states are prevented from exposing ASC/MC/houses. Chart image generation returns a typed `409 insufficient_precision` instead of drawing a misleading wheel.

The image route uses the birth input captured in `calculation.input` before current profile fields. This prevents a profile edit from silently changing the image for an older immutable chart snapshot. A configuration mismatch such as a stored non-Product configuration is rejected as `engine_render_failed`; the renderer no longer silently draws using current defaults.

## 3. Cache and evidence integrity

Calculation cache identity includes normalized request and configuration fingerprints. Render cache identity additionally includes the calculation contract/configuration/request fingerprints and the actual Kerykeion, Swiss Ephemeris and tzdata runtime versions from the stored config. Durable report/evidence snapshots remain independent of later profile or backend changes.

The user notification inbox is deliberately outside the numerical calculation path. It materializes only an already persisted daily forecast, deduplicates by owner/day/language, exposes unread/read state, and never invokes an LLM or accepts user-supplied notification content.

## 4. Local verification

The following integration checks are required and pass in the current local environment:

```text
pytest -q tests/test_engine_call_paths.py tests/test_chart_integration.py tests/test_api.py -k 'chart_image or chart_image_route or render or full_state'
pytest -q tests/test_notifications.py tests/test_placements_palm.py
pytest -q -k 'not palm'
python3 scripts/domain_qa.py  # 8/8
ruff check app admin tests scripts
python3 -m compileall -q app tests scripts
```

## 5. External gates

This audit does not certify real Telegram signed `initData` on every device, live LLM quality/SLO, payment provider settlement, Docker/HTTPS game day, production backup/restore/rollback, formal legal/privacy review or an independent ephemeris vendor comparison. Direct `pyswisseph` checks remain same-kernel adapter QA; independent comparisons must use equivalent external planetary UTC reference fields and must not be generalized into a universal accuracy claim.

## References

[1]: [ASTROLOGY.md](ASTROLOGY.md) — canonical chart contract and precision policy.
[2]: [ENGINE_COMPLETION_PLAN.md](ENGINE_COMPLETION_PLAN.md) — implementation sequence and acceptance criteria.
[3]: [ENGINE_READINESS_SUMMARY.md](../ENGINE_READINESS_SUMMARY.md) — component/readiness matrix and next tasks.
[4]: [API.md](../API.md) — API route and owner-scope rules.
[5]: [https://github.com/g-battaglia/kerykeion](https://github.com/g-battaglia/kerykeion) — numerical/render backend source.
[6]: [https://www.astro.com/swisseph/swephinfo_e.htm](https://www.astro.com/swisseph/swephinfo_e.htm) — Swiss Ephemeris reference.
