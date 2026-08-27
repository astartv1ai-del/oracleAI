# OracleAI Engine: frontend audit и roadmap точности

**Дата проверки:** 2026-08-27

**Ветка:** `master`
**Текущий backend:** `OracleAI Engine` v2 → Kerykeion 5.12.9 → Swiss Ephemeris

## 1. Результат проверки `engine_provenance`

Backend уже формирует provenance в двух местах публичного chart response:

```text
GET /api/chart
├── engine                         # legacy-compatible string
├── engine_provenance              # explicit public disclosure
└── calculation.engine_provenance  # same object inside stable calculation contract
```

Текущий disclosure object содержит `product_engine`, `adapter_version`, `backend`, `backend_version`, `ephemeris` и `license_notice`. Канонический источник значений — `app/core/chart_contract.py`; API отдаёт его через `app/api/routers/chart.py`. Это правильная архитектура: frontend не должен сам угадывать движок по строке `engine`.

### Что фактически делает frontend

| Surface | Файл/путь | Текущее поведение | Вывод |
|---|---|---|---|
| Chat chart | `miniapp/js/10-chart.js:119`, `app.chartHtml` | Вызывает общий `chartProvenanceHtml(c)` и показывает collapsed technical disclosure | Реализовано; helper читает только allowlist и экранирует значения |
| Full chart modal | `miniapp/js/12-misc.js:582`, `app.openFullChart` | Вызывает тот же helper и показывает product/backend/version/ephemeris/license details | Реализовано; RU/EN проверено в браузере |
| Chart image | `miniapp/js/10-chart.js:100`, `/api/chart/image` | Использует только `precision` для разрешения изображения | Provenance корректно не добавляется в image URL или raster payload |
| Admin | `admin/` | Нет chart provenance consumer | Отдельный diagnostics view остаётся опциональным |
| Hashed production bundle | `scripts/build_frontend.mjs`, `miniapp/index.html` | Source собирается в hashed bundles; asset query version bumped to `v=104` | Cache-bust и CI contract check добавлены |

### Нужны ли frontend-доработки

**Основная frontend-доработка выполнена.** Пользовательский disclosure теперь доступен в chat chart и full-chart modal через единый закрытый по умолчанию `<details>`. Значения проходят allowlist и `esc()`, неполные ответы используют bounded fallback, а license explanation локализован для RU/EN вместо вывода сырого backend текста.

Добавлены `scripts/check_frontend_provenance.py`, cache-bust `v=104`, keyboard focus state и CI execution. Браузерная проверка на disposable RU/EN users подтвердила загрузку обеих карт, раскрытие блока и localized copy. Chat question path в локальном offline/LLM smoke завершился bounded “answer not arrived” состоянием, поэтому inline chart response требует отдельного live-service test.

### Fallback и совместимость

Текущая frontend-логика в целом tolerant к дополнительным JSON-полям: неизвестный `engine_provenance` не вызывает ошибку. Но она также не проверяет shape объекта. Поэтому helper должен работать по allowlist полей и не использовать `innerHTML` для непроверенных значений. Старое поле `engine` нужно продолжать принимать для старых cached responses; отсутствие `engine_provenance` не должно блокировать просмотр карты.

Frontend не должен копировать provenance в localStorage, user profile или Tarot history. Это calculation metadata, которое можно отобразить в текущем chart view; исторические отчёты должны сохранять собственный versioned snapshot, а не ссылку на текущий backend.

## 2. Roadmap алгоритмических улучшений

Цель roadmap — улучшать наш OracleAI Engine как versioned request/calculation layer, не меняя Kerykeion silently и не позволяя LLM вычислять или дополнять факты. Kerykeion остаётся явно раскрытым backend; его обновление требует отдельного compatibility review.

### Приоритеты

| Priority | Улучшение | Что меняется | Acceptance criteria |
|---|---|---|---|
| P0 | Typed canonical request | Перевести вход в строгую модель `ChartRequest`: date, optional local time, IANA timezone, latitude/longitude, source/confidence и `time_known` | Невалидные значения отклоняются typed error; одинаковые семантические inputs дают один fingerprint; raw user text не входит в persistent evidence |
| P0 | DST ambiguity policy | Разделить nonexistent local time при spring-forward и ambiguous local time при fall-back; не выбирать fold молча | Для gap — controlled validation error или date-only; для fold — явное подтверждение fold либо bounded candidate interval; golden tests для обеих границ |
| P0 | Precision state machine | Уточнить states `exact`, `time_without_location`, `date_only`, `interval` и `sun_only`; отделить source confidence от mathematical output availability | API, skills, PDF и UI используют одну state machine; при downgrade запрещены ASC/MC/houses и time-specific claims |
| P0 | Coordinate provenance | Хранить normalized finite coordinates, source (`geocoder/user/manual`), confidence и whether location is sufficient for houses | `0/0` остаётся только technical neutral reference и явно маркируется; invalid/polar policy не маскируется под exact |
| P1 | Versioned backend config | В fingerprint и calculation metadata включить Kerykeion version, Swiss Ephemeris version, tzdata identifier, zodiac, perspective, house system, node/Lilith policy и aspect policy | Изменение любой calculation-affecting setting invalidates cache and requires fixture review; old API clients сохраняют `engine` compatibility |
| P1 | Numerical canonicalization | Ввести single degree normalization `[0, 360)`, canonical negative-zero handling, explicit float serialization and presentation-only rounding | Repeated runs and JSON serialization are byte-stable; aspect/house decisions use exact values, never UI-rounded degrees |
| P1 | Output validator | Проверять Kerykeion result before exposure: finite values, known points, sign/degree consistency, house order, angle presence and expected node opposition | Malformed backend output becomes bounded typed failure/offline response; no partial invented chart is persisted |
| P1 | Deterministic cache boundary | Разделить calculation cache и durable evidence; bounded cache key includes normalized request plus engine/config versions | Cache returns defensive copies, has deterministic eviction tests and cannot be used to reconstruct another owner’s history |
| P1 | Differential corpus | Расширить JPL/direct Swiss comparison to multiple UTC/DST/historical/high-latitude cases and record non-comparable fields explicitly | No fake external values; every discrepancy is retained with configuration; independent comparison is never generalized into universal accuracy claim |
| P2 | Geocoder/timezone confidence | Avoid city-only authority; persist resolved coordinates/timezone and confidence, with a user correction path | Same city with different coordinates is not conflated; timezone changes trigger recalculation; manual correction is auditable without raw PII logs |
| P2 | Interval and uncertainty calculations | For unknown minute, ambiguous fold or approximate coordinates, calculate bounded candidates or date-level facts instead of inventing a point estimate | UI labels interval/approximate states; angular fields are hidden unless all candidate results agree within a documented threshold |
| P2 | Product-specific validators | Add invariants for transits day vs instant, shortest-arc composite midpoints, synastry reproducibility and solar-return root/bracket validation | Product contracts expose source precision and reject incompatible exact-time requests; saved product evidence is immutable |
| P2 | Regression and rollout policy | Add adapter migration notes, contract compatibility tests, staged canary metrics and rollback version | Every engine version has golden corpus, diff report, release note and explicit SHIP/BLOCKED gate |

## 3. Recommended implementation sequence

### Phase A — frontend transparency — completed

`chartProvenanceHtml(c)` is used in chat and full-chart surfaces, RU/EN keys are present, values are escaped, fallback behavior is bounded, keyboard focus is visible, the hashed bundle was rebuilt, and CI now runs the provenance contract checker. Browser evidence is recorded in `FRONTEND_PROVENANCE_BROWSER_TEST.md`.

### Phase B — normalization correctness — first iteration completed

The canonical `ChartRequest` now normalizes surrounding whitespace in time, timezone and city, canonicalizes valid finite coordinates, rejects non-string/invalid IANA timezone identifiers before backend calls, and records `location_reason`. It classifies local times as `normal`, `nonexistent`, `ambiguous`, `no_timezone` or `not_applicable`; spring-forward gaps and fall-back folds downgrade to date-only rather than silently selecting an instant. Missing timezone is never replaced by the server timezone. Remaining work is typed coordinate source/confidence and candidate intervals for user-confirmed ambiguous times.

### Phase C — calculation integrity — first iteration completed

The OracleAI Engine now runs a post-Kerykeion validation layer on both fresh and cached results. It validates finite numeric outputs, degree ranges, the ten-planet inventory, house/angle availability, expected precision, public aspect orbs, house-number bounds and true-node opposition; malformed backend output is downgraded to bounded Sun-only fallback. Exact values remain separate from presentation rounding. Remaining work is full configuration fingerprinting and typed product-specific errors.

### Phase D — accuracy evidence

The deterministic corpus now includes normalization metadata and DST boundary tests, while the tracked generator remains the only way to refresh numeric snapshots. Expand it into separate deterministic regression fixtures and external comparison artifacts. Use direct `pyswisseph` only as a same-kernel adapter check; use NASA/JPL Horizons where settings are comparable for planetary positions; leave ASC/MC/Placidus/nodes/Lilith/retrograde fields open when the reference does not expose equivalent semantics. No external comparison should be used to claim scientific or universal predictive accuracy.

### Phase E — products and release

Apply the same evidence envelope to transits, synastry, composite and solar returns. Add property tests for date boundaries, longitude wraparound, aspect thresholds, coordinate extremes and repeated serialization. Release only when local tests, differential reports, frontend disclosure, licensing notices and manual cross-surface review agree. A backend version bump must be visible in API metadata and documented in the release record.

## 4. Proposed next implementation ticket

The frontend disclosure ticket, first normalization iteration and first output-integrity validator are complete. The next implementation ticket is **uncertainty envelope + configuration fingerprint P0/P1**:

1. Add typed `coordinate_source`/confidence and user-visible geocoder provenance.
2. Represent ambiguous local times as bounded candidate instants when the user explicitly requests interval mode; never silently choose a fold.
3. Include Kerykeion, Swiss Ephemeris, tzdata, zodiac, house, node/Lilith and aspect configuration in the calculation-affecting fingerprint.
4. Extend node/point cross-field validation and add product-specific validators for transits, synastry, composite and solar returns.
5. Expand the external differential corpus beyond the representative JPL run and retain all non-comparable fields explicitly.

The current browser audit finds the frontend disclosure visible and localized. The algorithmic roadmap is still not a claim of universal or scientific predictive accuracy: Kerykeion/Swiss Ephemeris remain the disclosed numerical backend, while OracleAI improvements target input truthfulness, reproducibility, integrity validation and product semantics.

## References

[1] [OracleAI ASTROLOGY.md contract](ASTROLOGY.md) — current exact/date-only, backend and provenance rules.

[2] [OracleAI chart contract](../../app/core/chart_contract.py) — versioned calculation metadata and public contract source.

[3] [OracleAI improved engine](../../app/core/astrology_engine.py) — request normalization, fingerprint, bounded cache and post-calculation validation hook.

[6] [Frontend provenance browser test notes](FRONTEND_PROVENANCE_BROWSER_TEST.md) — RU/EN interactive smoke evidence and cache-bust finding.

[4] [Kerykeion upstream repository](https://github.com/g-battaglia/kerykeion) — disclosed backend provenance and upstream license source.

[5] [Astrodienst Swiss Ephemeris information](https://www.astro.com/swisseph/swephinfo_e.htm) — Swiss Ephemeris distribution/license information.
