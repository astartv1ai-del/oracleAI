# OracleAI — astrology and chart products

## Document orientation

| Field | Definition |
|---|---|
| **Purpose** | Define the supported Western/Vedic calculation semantics and chart-product boundaries. |
| **Source of truth** | `app/core/astro.py`, `app/core/chart_contract.py`, `app/core/vedic.py` and `app/core/chart_products.py`. |
| **Scope** | Natal, Vedic, lunar/today, synastry, transit, composite and solar-return evidence. |
| **Do not change** | Do not calculate chart facts in JavaScript or an LLM; do not expose houses/angles when birth time is unknown; do not turn symbolic evidence into scientific or guaranteed prediction claims. |
| **Key files** | `app/core/astro.py`, `app/core/chart_contract.py`, `app/core/vedic.py`, `app/core/chart_products.py`, `tests/test_chart_contract.py`, `tests/test_chart_products.py`. |
| **Validation** | `python3 -m scripts.domain_qa`, `pytest -q tests/test_chart_contract.py tests/test_chart_products.py tests/test_vedic.py tests/test_natal_sections.py`. |

## Western natal

OracleAI’s Western natal path is tropical, apparent geocentric and calculated server-side through the pinned Swiss Ephemeris dependency, with Kerykeion used for structured/rendering integration. The exact-time contract may include planets, nodes, points, aspects, retrograde flags, houses and angles. Placidus houses are restricted to exact-time input.

The truth state is explicit. With `time_known=false`, the response can contain supported date-only facts but must omit ASC, MC, houses, house overlays and the natal wheel. The browser and AI do not fill missing precision with a guess. Coordinates, timezone and the calculation source remain part of the evidence metadata.

## Vedic boundary

The Vedic path is sidereal and uses the exposed Lahiri/Chitrapaksha configuration. It supports bounded chart facts, Vimshottari dasha, panchang-like moon data and Guna Milan compatibility where the implementation contract permits. Vedic semantics must not be silently mixed with Western tropical meanings; any bridge must be named in the UI or response.

Divisional charts, yogas, muhurta and broader prediction products require their own contract, golden cases and release decision. They are not implied by the presence of upstream calculation capability.

## Products

| Product | Current rule | Explicit limitation |
|---|---|---|
| Natal | One owner-scoped chart with exact or date-only precision. | Missing time never receives inferred houses/angles. |
| Synastry | Two exact owner-scoped charts, cross-chart aspects and bounded relationship evidence. | Does not establish feelings, infidelity or future decisions. |
| Transit | Versioned date/day or instant snapshot. | A day snapshot is not represented as an exact instant; transit houses are excluded from the current contract. |
| Composite | Contracted circular midpoints and internal major aspects. | Current JSON-first contract has no houses or angles. |
| Solar return | Bounded search for the Sun’s return to natal longitude for an explicit target year and location. | Other planetary returns and deterministic fate claims are out of scope. |
| Lunar/today | Deterministic snapshot with explicit local date/timezone handling. | A day-level snapshot is not an exact lunar instant. |

The request/response shapes and version fields are canonical in [`../CHART_PRODUCT_CONTRACTS.md`](../CHART_PRODUCT_CONTRACTS.md). Product calculations remain in the core layer and are not reimplemented in the client.

## Evidence and safety

The calculation output is evidence, not a diagnosis, scientific finding or certainty claim. Agent responses must preserve precision, source and limitations. Independent authority comparison and licensing confirmation are external release gates; local unit tests demonstrate implementation contracts only.

## References

[1]: [app/core/astro.py](../../app/core/astro.py) — Western calculation source.
[2]: [app/core/chart_contract.py](../../app/core/chart_contract.py) — precision and natal truth state.
[3]: [app/core/vedic.py](../../app/core/vedic.py) — Vedic calculation boundary.
[4]: [app/core/chart_products.py](../../app/core/chart_products.py) — product builders.
[5]: [../CHART_PRODUCT_CONTRACTS.md](../CHART_PRODUCT_CONTRACTS.md) — public product contract.
