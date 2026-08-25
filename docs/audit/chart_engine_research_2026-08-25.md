# Chart-engine research — 2026-08-25

## Official findings

| Candidate | Official evidence | Output/support | License/release implication |
|---|---|---|---|
| Kerykeion 5.12.9 | [Docs](https://kerykeion.net/content/docs), [PyPI](https://pypi.org/project/kerykeion/), [source](https://github.com/g-battaglia/kerykeion) | Factory APIs cover natal, synastry, transit, composite, planetary returns, wheel-only and aspect-grid outputs. Official docs show `AstrologicalSubjectFactory` → `ChartDataFactory` → `ChartDrawer`. The product already pins 5.12.9 and prior local smoke renders succeeded. | GitHub reports AGPL-3.0. Swiss Ephemeris has a separate dual-license model; commercial/public distribution requires an explicit AGPL-compatible strategy or Swiss Professional license. Production integration remains conditional on legal/license sign-off. |
| Astrolog 8.00 | [Official documentation](https://www.astrolog.org/ftp/astrolog.htm), [downloads/license](https://www.astrolog.org/astrolog/astfile.htm) | Mature CLI with natal, relationship, transits, progressions, returns, aspect grids and direct bitmap/PNG capabilities. | Official downloads page states GPL v2. Direct PNG avoids transient SVG but visual style and CLI/container integration require a separate spike. Not selected as default premium renderer without stronger product fit evidence. |
| Stellium 0.22.0 | [PyPI](https://pypi.org/project/stellium/), [source](https://github.com/katelouie/stellium) | Broad modern API, natal/synastry/transit/composite/returns, SVG/PDF/PNG claims and bundled glyph/font handling. | PyPI/GitHub report AGPL-3.0 and active-development status. It is not selected for default integration before a separate stable API, parity and licensing review. |
| resvg_py 0.5.0 | [PyPI](https://pypi.org/project/resvg_py/), [source](https://github.com/baseplate-admin/resvg-py), [docs/license](https://resvg-py.readthedocs.io/en/latest/license.html) | High-level `svg_to_bytes()` API; official docs describe safe Rust-backed PNG rendering with prebuilt wheels. Upstream resvg is static-SVG focused and does not support scripts/events/animations. | Python binding source documents MIT; upstream resvg is dual MIT/Apache-2.0. Add exact version/SBOM and verify package wheel/runtime in the production image. |
| Swiss Ephemeris | [Official licensing page](https://www.astro.com/swisseph/) | Calculation library used by Kerykeion and existing canonical engine. | Dual model: AGPL or Swiss Ephemeris Professional License. This remains a commercial release blocker until legal/product owner chooses and documents the distribution strategy. |

## Decision for the spike

Use **Mode P** from the migration brief: Kerykeion server-side → transient in-memory SVG → `resvg_py` → PNG/WebP. The raw SVG must never be persisted, logged, returned by an API or sent to the browser. This is a technical spike and integration path, not a claim that AGPL/Swiss licensing is already approved.

Astrolog remains the strict zero-SVG comparison candidate because its official documentation describes direct bitmap/PNG output. Stellium remains a comparison candidate, not a production dependency, because its official package is AGPL and its current API is active-development.

## Source caveats

Official pages establish capabilities and licenses, but they do not prove OracleAI parity. Every enabled chart type still requires a real fixture, calculation parity check, raster output, visual artifact, API security test and license review.
