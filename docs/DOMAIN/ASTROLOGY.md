# Western astrology contract

## Canonical calculator

The canonical natal path is `app.core.astro.compute_chart`. In the full path it uses **Kerykeion 5.12.9** over Swiss Ephemeris. The product contract is version **1** from `app/core/chart_contract.py`. The calculation is tropical, apparent geocentric and Placidus (`P`) when angular data is available. The active points include Sun–Pluto, Chiron, Juno, Ceres, Vesta, Pallas, true North/South lunar nodes, true Lilith and the four angles where supported.

The direct reference harness in `scripts/domain_qa.py` calls `pyswisseph` directly. It is an independent implementation path but shares the Swiss Ephemeris kernel with Kerykeion. It confirms adapter/timezone consistency, not independent vendor or scientific truth. The exact run and its limits are documented in [`docs/ASTRONOMY_REFERENCE_QA.md`](../ASTRONOMY_REFERENCE_QA.md).

## Input contract

| Field | Contract |
|---|---|
| `birth_date` | ISO calendar date `YYYY-MM-DD`; invalid dates fail validation. |
| `birth_time` | Optional local civil time `HH:MM`; invalid values fail instead of becoming noon. |
| `time_known` | Explicit confirmation flag. A technical noon used for a date-only calculation is never presented as factual birth time. |
| `tz` | IANA timezone identifier. Exact local-time interpretation requires this field. Unknown/invalid timezone is rejected; missing timezone downgrades a supplied clock to date-only. |
| `lat`, `lon` | Physical ranges latitude `[-90, 90]`, longitude `[-180, 180]`; non-finite values are invalid. |
| `city` | Display/context label, not an authority for coordinates. Coordinates are resolved and then carried in evidence. |

The calculation path is therefore:

```text
local civil date/time + IANA timezone
→ UTC instant
→ Swiss Ephemeris/Kerykeion
→ canonical chart contract
→ evidence metadata
→ interpretation/UI/PDF
```

## Precision states

`precision=exact` requires confirmed time, valid coordinates and a valid timezone; it may include houses, ASC, MC and house placements. `precision=time_without_location` retains time-based planetary evidence but suppresses houses and angles. `precision=date_only` is used for unknown/unconfirmed time or missing timezone; a technical snapshot may show planetary sign/longitude evidence, but ASC, MC, houses and house placements are not facts. If the full engine is unavailable, the result is explicitly `mode=lite`, `precision=sun_only` and contains only the Sun fallback.

The API, grounding layer, PDF builder and UI must consume the `precision` and `calculation.input.precision_reason` fields rather than infer precision from whether a time string happens to be present. The date-only contract is intentionally propagated through chat and reports.

## Planet and angle evidence

Each canonical planet row contains sign, UI-rounded degree, exact degree, absolute longitude, exact absolute longitude and the source retrograde flag. UI rounding is presentation only and must never be used for downstream aspect or house classification. ASC, MC and 12 Placidus cusps are emitted only when angular data is available.

Nodes use the explicit **true node** convention. Rahu is the true North Lunar Node and Ketu is the true South Lunar Node. The product currently exposes `True_Lilith` as its Lilith convention. These are named conventions, not interchangeable “node” or “Black Moon” defaults. An independent external node/Lilith comparison remains open.

## Aspect policy

Only these major aspects are exposed:

| Aspect | Angle | Maximum orb |
|---|---:|---:|
| Conjunction | 0° | 8° |
| Opposition | 180° | 8° |
| Trine | 120° | 8° |
| Square | 90° | 7° |
| Sextile | 60° | 6° |

The exact orb is retained as `orb_exact`; the rounded `orb` is for display. Applying/separating state is not implemented and must not be invented by the model. Boundary tests cover inside and outside thresholds.

## Supported products and limitations

Synastry calculates major inter-chart planetary aspects from two exact saved charts. It is not a relationship certainty score. Composite v1 calculates shortest-arc midpoints for ten traditional planets and internal major aspects; it does not calculate ASC, MC, houses or nodes. Transit day snapshots use a documented 12:00 UTC sample when no clock is supplied and are marked `precision=day`; they must not be described as an exact lunar instant. Solar returns v1 supports only the Sun and returns an astronomical crossing, not a prediction or guaranteed event.

## Interpretation boundary

Astrology output is reflective domain content. It may describe calculated positions and traditional symbolic meanings, but it must not become medical diagnosis, guaranteed financial outcome, guaranteed relationship outcome, deterministic future claim, mortality prediction or legal decision. When time/coordinates are insufficient, the system must say which precision is unavailable instead of fabricating houses or angles.

## Versioning and reproducibility

Every chart carries `contract_version`, calculator configuration, input fields, precision, angular availability and exact-field semantics. Changes to calculator version, timezone database, Swiss Ephemeris dependency, aspect policy, node/Lilith convention or rounding rules require a golden-fixture review and an explanation in the release record. The current golden corpus is `tests/fixtures/domain_golden.json` and the deterministic tests are in `tests/test_domain_gauntlet.py`.
