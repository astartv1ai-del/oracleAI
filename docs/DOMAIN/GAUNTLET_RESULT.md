# OracleAI Domain Accuracy Gauntlet — result

**Run date:** 2026-08-27

**Repository:** `astartv1ai-del/oracleAI`

**Branch:** `master`
**Scope:** Western astrology, transits/synastry/composite/solar returns, Vedic/Jyotish, Matrix, Tarot, evidence-first interpretation, PDF/API/chat/history consistency. Palm/CV is intentionally outside the primary Gauntlet scope.

## Executive result

The Gauntlet produced a stronger and more explicit deterministic contract, golden regression corpus, Tarot replay validation, evidence-bound skill wrappers and report-history metadata. A representative independent NASA/JPL Horizons comparison covered the ten canonical planetary longitudes at one UTC instant; the maximum recorded delta was 0.000282188° and the redacted output is stored in [`jpl_reference_2026-08-27.json`](jpl_reference_2026-08-27.json). JPL quantity 31 is an apparent observer-centered ecliptic-of-date longitude, so the artifact records configuration rather than pretending that its fields are identical to every OracleAI astrology field. [1]

The final verdict is **BLOCKED**, not because the deterministic local checks failed, but because the complete release evidence set is not yet closed. The exact blockers are the legal distribution decision for AGPL/commercial Swiss Ephemeris and AGPL Kerykeion, broader independent reference coverage across cases and angles, a documented product policy for polar Placidus, external node/Lilith and retrograde-boundary checks, live-model evaluation, and manual PDF/UI/device review. Astro.com explicitly states that Swiss Ephemeris users must choose AGPL or the Swiss Ephemeris Professional License before distributing software or activating a public service. [2]

## Implemented in this run

| Area | Delivered result |
|---|---|
| Precision truth state | Exact charts now require confirmed time plus a valid IANA timezone; missing timezone downgrades supplied clock data to date-only. Invalid/missing coordinates suppress angles and houses while allowing bounded planetary snapshots. `precision_reason` is carried in calculation metadata. |
| PDF consistency | PDF report rebuild no longer initializes an absent city/timezone as Europe/Moscow. A supplied clock without resolvable timezone is rendered as date-only and cannot produce ASC/MC/houses. |
| Tarot integrity | Draw sizes are strict 1–78; canonical persisted evidence rejects unknown IDs, duplicate cards, mismatched names and invalid objects. An explicit complete legacy alias map supports older English RWS names without redraw. Replay remains checksum-based and immutable. |
| Skill boundary | Tarot tool arguments no longer clamp invalid values silently. Chart skill headlines use actual chart precision and angular availability rather than only a profile flag. Vimshottari tool access requires date, confirmed time and timezone. |
| Report history | Monthly reports now store `monthly-evidence-v1` aggregate-only metadata, including counts and limits, without copying raw diary, memory or question text into report metadata. Existing purchased reports remain append-only. |
| Documentation | Added `ACCURACY_MATRIX.md`, `ASTROLOGY.md`, `TAROT.md`, `VEDIC.md`, `MATRIX.md`, this result report and an external evidence record. |
| Tests and fixtures | Added version-pinned deterministic `tests/fixtures/domain_golden.json`, `tests/test_domain_gauntlet.py`, Tarot adversarial cases, legacy history cases, PDF precision cases and skill-wrapper adversarial cases. |

## Verification record

| Check | Outcome |
|---|---|
| Focused domain/Tarot/grounding/PDF/product tests | Passed: 57 tests in the final focused run. |
| Full suite excluding Palm/CV | The pre-merge run passed; after the latest origin/master documentation merge, one unrelated existing `test_p2_contracts.py::test_payment_locale_dictionaries_have_matching_keys` failure remains because the test expects legacy payment keys absent from the current remote frontend. |
| Full `pytest -q` | Two additional failures remain in the intentionally out-of-scope Palm/CV area: missing ONNX runtime produces `unavailable` where the old test expects a line status, and the ensemble test expects a legacy model label. No Gauntlet astrology/Tarot/Vedic/Matrix test failed. |
| Ruff | Passed for `app admin tests scripts`. |
| Python compileall | Passed for `app tests scripts`. |
| JavaScript syntax | Passed for all `miniapp` and `admin` JavaScript files. |
| `scripts/domain_qa.py` | Passed 8/8 local case checks, with polar houses/ASC/MC explicitly unverified and external-vendor status recorded. |
| PDF golden cases | Passed 6/6 synthetic exact/date-only/high-latitude checks. |
| Static asset references | Passed. |
| `scripts/selfcheck.py` | Passed; live LLM was intentionally skipped and reported unavailable/offline in the local environment. |
| `scripts/release_gate.py` | Passed. |
| `pip-audit -r requirements.txt` | Passed: no known vulnerabilities. |
| `scripts/check_p2_quality.py` | Post-merge result is **false** only for the unrelated `payment_ux_contract` check (`payment safety or recovery marker is missing` in the current remote frontend); all other listed P2 checks passed. |
| NASA/JPL Horizons comparison | Passed for the captured representative planetary case; 10 bodies compared, max delta 0.000282188°. This does not close universal coverage or non-comparable fields. |

## Remaining evidence gates

The legal owner must choose and document the Swiss Ephemeris distribution model, including copyright notices, source/offer obligations and whether a commercial Professional License is required. Kerykeion is also identified upstream as AGPL-3.0, so the combined deployment decision requires legal review rather than an assumption based on package installation. [2] [3]

The external numerical reference set should be expanded to multiple exact-time, DST-transition, historical-timezone, southern/high-latitude and date-boundary cases, with matched settings and retained redacted outputs. JPL Horizons does not provide the full OracleAI Placidus/true-node/True-Lilith/retrograde contract in the captured observer artifact. Polar Placidus behavior must be either explicitly unsupported/fail-closed or validated against a suitable reference.

A staging or production-like model evaluation must exercise prompt injection in questions, names, cities, diary/memory text and partner data, then confirm that invalid model output is rejected or replaced by bounded offline content. Manual review must inspect Russian and English PDF rendering, Mini App/admin views and representative device widths. The current code-level checks are not a substitute for that human review.

## References

[1] [NASA/JPL Solar System Dynamics, Horizons Manual](https://ssd.jpl.nasa.gov/horizons/manual.html)

[2] [Astrodienst, Swiss Ephemeris — for 8000 years and more](https://www.astro.com/swisseph/swephinfo_e.htm)

[3] [g-battaglia/kerykeion — upstream GitHub repository](https://github.com/g-battaglia/kerykeion)
