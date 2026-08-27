# OracleAI Engine: completion report

**Дата:** 2026-08-27
**Статус локального release gate:** `PASS` для текущего non-Palm product scope
**Architecture:** `OracleAI Engine` → `OracleKerykeionEngine` → `Kerykeion 5.12.9` → `Swiss Ephemeris`

## Результат

Реализован production-oriented calculation boundary. Входные данные проходят canonical normalization; timezone/DST, coordinates, precision и uncertainty представлены явно; calculation-affecting configuration и runtime versions участвуют в fingerprint; backend results валидируются до cache/API/LLM/PDF; product contracts и specialized placements имеют отдельные invariants; frontend и PDF используют тот же evidence envelope.

Это не является заявлением о том, что OracleAI численно точнее Swiss Ephemeris. Swiss Ephemeris остаётся disclosed numerical backend. Доказуемое улучшение OracleAI находится в adapter semantics: отсутствие silent defaults, воспроизводимость, cache safety, fail-closed output validation, product consistency и provenance/licensing transparency.

## Выполненные шаги

| Шаг | Реализация | Проверка |
|---|---|---|
| Canonical boundary | `ChartRequest` является единственным входным boundary перед Kerykeion. | Golden and contract tests. |
| Precision state machine | `exact`, `time_without_location`, `date_only`, `interval`, `sun_only`; angular data выдаётся только при exact. | Normalization/DST tests and API assertions. |
| DST safety | Nonexistent spring-forward time и ambiguous fall-back time не выбираются молча; default — safe date-only, explicit interval mode сохраняет two candidate UTC instants. | Berlin/New York boundary tests. |
| Geography provenance | `coordinate_source`, bounded `coordinate_confidence`, `timezone_source`, `location_reason` и neutral-reference semantics. | Contract tests and geo metadata path. |
| Configuration fingerprint | Contract v2 hash includes active points, aspect policy, node policy, precision policy, Kerykeion/pyswisseph/tzdata versions. | Fingerprint mutation test and golden regeneration. |
| Numerical canonicalization | Exact fields отделены от rounded UI fields; composite aspects теперь используют exact longitudes. | Golden/product tests. |
| Output integrity | Проверка finite/range values, planets, houses, angles, nodes, aspects, precision agreement and cache hits. | Malformed backend and cache validator tests. |
| Product validators | Synastry, transit, composite and returns validators проверяют schema, roles, precision, exact longitudes, shortest midpoint, timestamps and return ordering. | Product adversarial tests and API product suite. |
| Evidence parity | Product contracts and PDF build preserve source/config fingerprints; API keeps legacy `engine` plus explicit provenance. | API/PDF/agent suites. |
| Specialized placements | Moon, Venus, rising, nodes, asteroids and other Western placement calculators now call canonical `astro.compute_chart`; the legacy placement response shape is preserved while calculation evidence is propagated. | Placement suite plus fingerprint regression test. |
| Mini App | RU/EN provenance disclosure, v105 cache bust, static guard for unresolved `{sign}`, hashed build and localized license copy. | Browser click smoke and frontend checks. |
| Documentation | Full step-by-step plan and updated roadmap with licensing/external-evidence boundaries. | Markdown reviewed; citations retained. |

## Browser evidence

The local FastAPI app was opened with synthetic users `10001` (RU) and `10002` (EN). Clicking `Карта`/`Chart`, then `Полная карта`/`Full chart`, opened the full-chart modal. Clicking the native provenance summary expanded the details. Both locales showed `OracleAI Engine`, `Kerykeion`, `oracleai-kerykeion-engine-v2`, `Swiss Ephemeris` and localized AGPL/commercial licensing copy.

The browser found a real UI regression before the final pass: the full-chart text contained literal `{sign}`. It was fixed by using `profileFormat('ascendant', ...)`, protected by `check_frontend_provenance.py`, and delivered with cache-bust `v105`. The final RU and EN DOM showed `Асцендент Весы` / `Ascendant Весы` and no placeholder. The chat path was also checked with a real `/api/chart` payload through `app.chartHtml`; provenance was present, localized, escaped and collapsed by default. The offline/LLM smoke correctly returned a bounded answer-not-arrived state rather than fabricating chart facts.

## Verification commands

The following checks passed after the final source changes:

```text
pytest -q -k 'not palm'
ruff check app admin tests scripts
python3 -m compileall -q app tests scripts
python3 scripts/domain_qa.py                 # 8/8; same Swiss Ephemeris kernel
python3 scripts/check_frontend_provenance.py
node --check miniapp/js/*.js
npm run build:frontend
python3 scripts/check_frontend_build.py
python3 scripts/check_static_asset_references.py
python3 scripts/check_design_contract.py
python3 scripts/check_visual_contrast.py
python3 scripts/check_cache_busting.py        # v105
python3 scripts/release_gate.py               # PASS
python3 scripts/selfcheck.py                  # exit 0
```

The environment still emits expected warnings when the configured LLM proxy returns empty completions; the application falls back safely and the selfcheck exits successfully. Palm/ONNX-specific tests remain outside this engine gate and are not represented as passed.

## Remaining external gates

A truly independent astronomical comparison still requires an independently sourced artifact with equivalent settings. Direct `pyswisseph` comparison is explicitly classified as same-kernel adapter QA. NASA/JPL/Horizons comparison can reasonably cover comparable UTC planetary positions, while ASC/MC, Placidus, true-node/Lilith semantics and product interpretations require explicit comparability notes. No universal predictive or scientific accuracy claim is made.

## References

[1]: ENGINE_COMPLETION_PLAN.md — complete implementation sequence and acceptance criteria.
[2]: ENGINE_PROVENANCE_AND_ACCURACY_ROADMAP.md — current roadmap and external-evidence boundaries.
[3]: ASTROLOGY.md — canonical OracleAI chart contract.
[4]: EXTERNAL_EVIDENCE.md — licensing and differential-evidence notes.
[5]: FRONTEND_PROVENANCE_BROWSER_TEST.md — interactive RU/EN browser evidence.
[6]: https://github.com/g-battaglia/kerykeion — Kerykeion upstream project and license source.
[7]: https://www.astro.com/swisseph/swephinfo_e.htm — Swiss Ephemeris information and licensing reference.
[8]: https://data.iana.org/time-zones/tz-link.html — IANA Time Zone Database resources.
[9]: https://ssd.jpl.nasa.gov/horizons/ — NASA/JPL Horizons reference service.

## Post-rollout improvement iteration

A focused audit found that specialized Western placement calculators still had a separate direct Kerykeion construction path. This was corrected: placement calculators now call canonical `astro.compute_chart`, inherit its normalization/DST/validation behavior, and expose the same calculation request/configuration fingerprints and `engine_provenance`. The legacy placement response fields remain compatible, including `source`, `engine`, precision labels, exact degrees and point codes. The unused direct-backend helper constants were removed, and placement regression tests cover deterministic values, true-node aliases, unknown-time safety and canonical evidence propagation.
