# Chart-type capability matrix

**Дата:** 2026-08-25  
**Правило:** в таблице различаются capability библиотек и реально включённый продуктовый путь. Наличие factory в upstream не считается доказательством OracleAI parity, UX, security или licensing readiness.

| Тип | Capability Kerykeion | OracleAI status | Precision/product gate | Следующий evidence gate |
|---|---|---|---|---|
| Natal | `AstrologicalSubjectFactory`, `ChartDataFactory.create_natal_chart_data`, `ChartDrawer` wheel output | **Enabled for exact natal image** | Exact time, coordinates and timezone required; unknown time returns structured `insufficient_precision` and no wheel | RU/EN render artifacts, API auth/ETag tests, PDF print artifact, legal sign-off |
| Natal date-only | Kerykeion can calculate positions using a technical time, but that does not make angles valid | **No wheel output** | Planets/aspects remain in JSON; ASC/MC/houses are hidden by canonical calculation contract | Keep explicit UX recovery state and regression test |
| Synastry | Official factory/documentation capability exists | **Not enabled as chart image** | Both subjects must have exact, owner-authorized inputs; no partner birth data in GET URLs or public cache keys | Dedicated fixture/parity/API ownership/PDF decision and licensing review |
| Transit | Official transit/chart-data capability exists | **Not enabled as chart image** | Requires explicit transit date/time/location contract; current natal image route must not infer a transit from profile data | Define product contract, timezone policy, fixture matrix and visual evidence |
| Composite | Official composite capability exists | **Not enabled** | Requires two exact subjects and a documented composite convention | Dedicated calculation contract and owner/partner privacy review |
| Planetary returns | Official returns capability exists | **Not enabled** | Requires return planet, target year/window, timezone and location semantics; current solar product is not a return implementation | Define return contract and deterministic fixtures before UI work |
| Matrix | Existing `matrix_svg()` is a separate product visual | **Existing separate track** | Not a natal chart engine and not included in the Kerykeion image boundary | Preserve independent tests; do not conflate with natal migration |

## Product invariants

The visual engine never becomes a second source of truth. `app/core/astro.py` remains responsible for canonical values and precision. The chart adapter is responsible only for reconstructing an exact Kerykeion subject from server-side canonical inputs, asking the public ChartDrawer API for a wheel, validating the transient SVG envelope, and rasterizing it.

A future chart type must not be enabled merely because an upstream documentation page lists it. Before enablement it needs a canonical input contract, deterministic fixture set, calculation parity review, visual evidence in RU/EN where applicable, owner-scoped API tests, PDF/share decision, operational limits and a completed license review.

## References

[1]: https://kerykeion.net/content/docs "Kerykeion official documentation"  
[2]: https://pypi.org/project/kerykeion/ "Kerykeion PyPI"  
[3]: https://github.com/g-battaglia/kerykeion "Kerykeion source repository"  
[4]: ../app/core/astro.py "OracleAI canonical calculation source"  
[5]: ../app/core/chart_rendering.py "OracleAI raster image adapter"
