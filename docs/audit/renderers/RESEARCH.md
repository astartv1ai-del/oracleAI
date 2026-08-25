# Renderer research notes

## AstroDraw AstroChart

Primary source: https://github.com/AstroDraw/AstroChart

The repository describes AstroChart as a free/open-source TypeScript library that generates SVG charts and does not calculate planetary positions. The tested package is `@astrodraw/astrochart` 3.0.2, distributed under MIT. Its public API accepts `planets: Record<string, number[]>` and exactly 12 `cusps`, creates a browser DOM SVG with `viewBox`, and supports custom settings for colors, symbol scale, padding and click areas. The repository page showed 415 stars, 103 forks, 28 issues, 3 pull requests and 180 commits at the time of review. The package was actually unpacked and rendered under Node 22 + jsdom.

## Kerykeion

Primary sources: https://github.com/g-battaglia/kerykeion and https://kerykeion.net/python-library

The repository describes Kerykeion as a Python astrology library that computes chart data and generates SVG for natal, synastry, transit, composite and return charts. The installed package exposes a separated architecture: `AstrologicalSubjectFactory` calculates a subject, `ChartDataFactory.create_natal_chart_data()` prepares a chart data model, and `ChartDrawer` renders the SVG. The current installed package includes both `classic` and `modern` styles; the modern renderer has concentric rings and a dedicated planet-decluttering algorithm. The project page showed 697 stars, 190 forks, 5 issues, 3 pull requests and 1,540 commits at the time of review. The repository license is AGPL-3.0 according to the GitHub page, so commercial integration requires a licensing review; the local product currently uses Kerykeion for calculation and must not silently embed AGPL renderer code into a closed distribution.

## Real smoke results

`@astrodraw/astrochart` 3.0.2 rendered three custom dark-theme SVGs under `docs/audit/renderers/astrochart/`: sparse (53,470 bytes, 27 text nodes), clustered (61,696 bytes, 42 text nodes) and spread (58,844 bytes, 39 text nodes). All had `viewBox="0 0 760 760"`, cusp labels, premium gold styling and valid SVG output. A limitation is that the package’s style settings did not emit the project violet token in the tested output and the library’s collision behavior is less controllable than the project’s current custom layer.

Kerykeion real rendering is implemented in `kerykeion_smoke.py`; the first two attempts exposed API mismatches (legacy constructor date order and the current ChartDrawer chart-data separation) and were corrected against installed source. The supported ChartDataFactory + ChartDrawer path successfully rendered both classic and modern styles; exact SVG metrics are recorded in `kerykeion/smoke_results.json` and the integration decision is recorded in ADR-006.
