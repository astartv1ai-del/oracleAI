# OracleAI Engine: полный план доведения до production-grade

**Дата:** 2026-08-27
**Архитектура:** `OracleAI Engine` → `OracleKerykeionEngine` → `Kerykeion 5.12.9` → `Swiss Ephemeris`
**Цель:** сделать расчётный слой воспроизводимым, проверяемым, безопасным при неполных данных и одинаковым на API, Mini App, chat, LLM evidence, PDF и сохранённых продуктах.

> OracleAI Engine — это собственный adapter/orchestration layer. Он не маскирует Kerykeion и Swiss Ephemeris под proprietary code: backend, версия и AGPL/commercial notice должны оставаться видимыми в provenance. Улучшение означает повышение корректности входов, семантики precision, воспроизводимости, валидации и поведения при неопределённости, а не неподтверждённое заявление о превосходстве численной точности Swiss Ephemeris.

## 1. Definition of Done

Движок считается полностью реализованным для текущего product scope только если одновременно выполнены следующие условия:

| Область | Критерий приемки |
|---|---|
| Canonical input | Каждый расчёт проходит через одну typed normalization boundary; raw input не используется как cache/evidence identity. |
| Time semantics | `exact`, `time_without_location`, `date_only`, `interval` и `sun_only` имеют однозначные правила; DST gap/fold не выбираются молча. |
| Geography | Координаты, timezone, source и confidence сериализуются; missing/invalid/polar/neutral reference не выдаются за exact location. |
| Reproducibility | Fingerprint зависит от всех calculation-affecting settings, engine/backend/tzdata versions и normalized request. |
| Numerical representation | Internal degrees находятся в `[0,360)`, negative zero устранён, UI rounding не используется для aspect/house decisions, JSON output стабилен. |
| Output integrity | Backend output проходит invariant validator до cache, API, persistence, PDF или LLM. Ошибка даёт bounded typed failure/fallback. |
| Products | Natal, transit, synastry, composite и solar-return contracts имеют свои validators и precision envelope. |
| Evidence | LLM получает только structured calculation evidence; он не вычисляет положения и не восстанавливает скрытые углы/дома. |
| Cross-surface parity | API, Mini App, chat, history, PDF и product endpoints показывают одинаковый contract/provenance/precision state. |
| Evidence corpus | Golden, adversarial, property, DST/geography и differential fixtures воспроизводимы; comparable и non-comparable поля разделены. |
| Release | Полный non-Palm QA, frontend build/browser smoke, lint/compile, diff check и clean Git worktree пройдены; release note содержит rollback/version policy. |

## 2. Последовательность работ

### Шаг 1. Inventory и contract freeze

Нужно зафиксировать единственный canonical path `raw request → normalize → ChartRequest → backend → validator → contract`. Проверить всех callers (`astro`, API routers, agents/skills, PDF, saved readings, products), запретить прямые вызовы Kerykeion в обход boundary и сохранить legacy `engine` только для совместимости. Ввести contract test, который проверяет наличие `calculation`, `engine_provenance`, `precision`, `angular_data_available` и adapter fingerprint.

**Готово, когда:** grep/static boundary check не находит обходов; каждый публичный chart response имеет stable calculation envelope.

### Шаг 2. Typed normalization и precision state machine

Усилить `ChartRequest` типами и явными причинами: дата, локальное время, `time_known`, IANA timezone, координаты, coordinate source/confidence, local-time status и precision. Принять только canonical `YYYY-MM-DD` и `HH:MM`; trim/case/whitespace normalization не должен менять semantic fingerprint. Invalid timezone/coordinates должны давать typed errors, а не server-local defaults.

Для spring-forward nonexistent time использовать controlled date-only/validation outcome. Для fall-back ambiguous time не выбирать `fold` silently: по умолчанию date-only, а при явно выбранном пользователем interval mode сохранять оба candidate instants. ASC/MC/houses и time-specific claims запрещены, пока state не `exact`.

**Готово, когда:** есть таблица переходов state machine, golden tests для normal/gap/fold/missing timezone/unconfirmed time и запрет углов при downgrade.

### Шаг 3. Geography provenance и uncertainty envelope

Добавить `coordinate_source` (`user`, `manual`, `geocoder`, `neutral_reference`), confidence, `location_status`, normalized latitude/longitude и timezone provenance. City label не должен быть authority для геометрии. `0/0` разрешён только как internal neutral reference для geo-independent longitudes и всегда маркируется.

Для approximate coordinates и unresolved location добавить uncertainty envelope. Если candidate charts дают расхождение углов выше documented threshold, возвращать `interval`/`date_only`, скрывая ASC/MC/houses. Raw PII и geocoder payload не сохраняются в logs; в evidence остаются только normalized coordinates, source и confidence согласно privacy policy.

**Готово, когда:** одинаковый city label с разными coordinates не коллапсирует в один fingerprint; location correction всегда меняет fingerprint.

### Шаг 4. Полный calculation fingerprint и config version

В fingerprint включить contract version, adapter version, Kerykeion version, Swiss Ephemeris backend/version когда доступен, tzdata identifier, zodiac, perspective, house system, node mode, Lilith policy, active points, aspect angles/orbs и precision policy. Разделить `request_fingerprint` и `configuration_fingerprint`, но включить оба в calculation metadata.

При изменении любого calculation-affecting setting cache должен miss, golden fixtures должны быть reviewable, а API должен показывать новый version/config hash. Старые clients получают legacy `engine` и stable field names.

**Готово, когда:** mutation test каждой config field меняет fingerprint; unrelated display localization fingerprint не меняет.

### Шаг 5. Numerical canonicalization

Свести все longitude/degree paths к одной функции normalization `[0,360)`, canonicalize `-0.0` в `0.0`, хранить exact float и отдельно UI-rounded value. Все aspect, opposition, midpoint и house decisions выполняются по exact values. Сериализация должна быть deterministic и не зависеть от dictionary insertion order.

**Готово, когда:** повторный расчёт, cache hit и JSON round-trip дают одинаковые semantic values; wraparound `359.999…/0.0` покрыт tests.

### Шаг 6. Post-calculation validator и fail-closed policy

Расширить validator для sign↔degree consistency, exact/rounded consistency, point inventory, duplicate names, house sequence, angle availability, finite/range values, node opposition, aspect codes/orbs и metadata/request agreement. Validator запускается до cache write и на cache read. Невалидный backend результат не сохраняется и не передаётся LLM; вызывается bounded fallback с явным `sun_only`/unavailable reason.

**Готово, когда:** malformed fixtures для каждого invariant приводят к typed failure/fallback без partial persistence.

### Шаг 7. Product-specific contracts

Для transit contract различать day snapshot и instant snapshot, хранить `sampled_at`, timezone/precision и отдельно ограничивать Moon/day uncertainty. Для synastry требовать совместимые exact charts и stable owner/partner labels, проверять duplicate pair/aspect policy и partner scope. Для composite использовать shortest circular midpoint и проверять source longitudes, wraparound и deterministic aspects. Для solar return валидировать year range, root/bracket, UTC/local conversion, timezone/DST conversion, match ordering и multiple crossings.

Каждый product response должен иметь schema version, calculation/config fingerprint, source precision, limitations и immutable evidence snapshot при сохранении.

**Готово, когда:** продуктовый validator rejects incompatible precision and malformed cross-field data; API tests закрывают owner boundary.

### Шаг 8. Cache, persistence и evidence boundary

Calculation cache должен возвращать defensive copies, иметь bounded eviction и key только из normalized request/config. Durable evidence должна быть immutable snapshot с engine/config/provenance, а не ссылкой на текущий backend. Проверить owner isolation, invalidation при version/config changes, отсутствие raw PII и отсутствие partial chart persistence.

**Готово, когда:** cache tests проверяют mutation isolation, eviction, cross-owner isolation и version invalidation.

### Шаг 9. API, LLM, chat, PDF и Mini App parity

Проверить, что все surfaces читают calculation envelope, а не угадывают precision по наличию time string. LLM prompts/tools получают фактические placements и limitations; date-only/interval states блокируют angular/time-specific claims. PDF/history сохраняют provenance snapshot. Mini App показывает collapsed localized provenance в chat/full chart, экранирует allowlisted fields, сохраняет legacy fallback и не переносит raw license text в пользовательские данные.

**Готово, когда:** contract parity tests сравнивают API JSON, chat helper, PDF metadata и saved evidence; RU/EN browser smoke подтверждает labels, details toggle и no raw untrusted HTML.

### Шаг 10. Verification corpus и differential evidence

Расширить deterministic corpus: leap days, timezone transitions, historical dates, high latitudes, equator/longitude wrap, missing/partial coordinates, unknown time, node/aspect thresholds и repeated serialization. Direct `pyswisseph` используется только как same-kernel adapter check. Comparable planetary UTC fields можно сравнивать с NASA/JPL/Horizons artifacts; ASC/MC/Placidus/nodes/Lilith и product semantics отмечаются non-comparable, если настройки/reference неэквивалентны.

**Готово, когда:** discrepancy report хранит configuration, precision, comparable status и не превращается в универсальное accuracy claim.

### Шаг 11. Operational release policy

Для каждой adapter/config version публиковать migration note, golden diff, provenance change, rollout decision и rollback target. В CI добавить checks на boundary, fixture freshness, licensing disclosure, browser smoke artifact и clean generated assets. Palm/ONNX environment gates должны быть явно отделены от engine gate, а не скрываться в отчёте.

**Готово, когда:** release gate выдаёт `SHIP` или `BLOCKED` с перечисленными причинами и reproducer commands.

## 3. Текущая реализация и текущая итерация

До этой итерации уже реализованы frontend provenance, RU/EN localization, canonical normalization первой версии, DST gap/fold safe downgrade, базовый output validator, golden corpus и domain QA. В этой итерации будут доведены configuration fingerprint, coordinate provenance/uncertainty envelope, product validators, cross-surface contract tests, adversarial/property coverage, differential fixture metadata и release report.

## 4. Честные ограничения

OracleAI не должен заявлять, что его астрономические долготы точнее Swiss Ephemeris, если расчёт использует Swiss Ephemeris как numerical backend. Проверяемое преимущество текущего слоя — **truthfulness и integrity**: он не silently invents time/location precision, не пропускает malformed output, делает cache/evidence reproducible, раскрывает backend/license и не передаёт LLM право считать карту.

## References

[1]: ASTROLOGY.md — OracleAI canonical astrology contract and precision rules.
[2]: ../../app/core/chart_contract.py — versioned calculation configuration and public contract.
[3]: ../../app/core/astrology_engine.py — request normalization, cache boundary and output validation.
[4]: FRONTEND_PROVENANCE_BROWSER_TEST.md — RU/EN browser evidence for provenance disclosure.
[5]: https://github.com/g-battaglia/kerykeion — Kerykeion upstream repository and license source.
[6]: https://www.astro.com/swisseph/swephinfo_e.htm — Swiss Ephemeris information and distribution/licensing reference.
[7]: https://data.iana.org/time-zones/tz-link.html — IANA Time Zone Database and related data sources.
[8]: https://docs.python.org/3/library/zoneinfo.html — Python `zoneinfo` behavior and IANA timezone integration.
[9]: https://ssd.jpl.nasa.gov/horizons/ — NASA/JPL Horizons reference service for comparable ephemeris checks.
