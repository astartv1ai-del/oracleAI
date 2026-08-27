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
| Chat chart | `miniapp/js/10-chart.js:119`, `app.chartHtml` | Читает `sun`, `precision`, `note`, `sections`, planets and aspects; `engine_provenance` не читает | Backend field silently ignored; rendering не ломается, но disclosure пользователю не виден |
| Full chart modal | `miniapp/js/12-misc.js:582`, `app.openFullChart` | Повторно запрашивает `/api/chart`; отображает precision, planets, nodes, houses и aspects; provenance не отображается | Нужна отдельная compact technical details section |
| Chart image | `miniapp/js/10-chart.js:100`, `/api/chart/image` | Использует только `precision` для разрешения изображения | Provenance не должен добавляться в image URL или raster payload |
| Admin | `admin/` | Нет chart provenance consumer | Доработка не нужна, если администратору не требуется отдельный diagnostics view |
| Hashed production bundle | `scripts/build_frontend.mjs` | Собирает source JS/CSS в `miniapp/dist/app.<hash>.min.*` | После frontend change обязателен frontend build; source остаётся canonical |

### Нужны ли frontend-доработки

**Да, если требование «показывать backend» относится к пользователю.** Сейчас disclosure доступен через API, но нигде не отображается в Mini App. Это не функциональный backend bug, а прозрачность интерфейса: пользователь получает расчёт, но не видит, каким движком он выполнен.

Рекомендуемый UX — не перегружать основной экран техническими деталями. В `chartHtml` и `openFullChart` следует добавить один общий helper, например `chartProvenanceHtml(c)`, который выводит закрытый по умолчанию `<details>` с подписью «Источник расчёта / Calculation source». Все значения должны проходить через `esc()`, а неизвестные или неполные поля — заменяться на bounded fallback «Источник расчёта не указан», без exception и без доверия к произвольным backend strings.

Показывать следует `OracleAI Engine`, `Kerykeion 5.12.9`, `Swiss Ephemeris` и короткое уведомление о лицензии. Текст не следует дублировать в каждом planetary row. Для RU/EN нужны локализационные ключи, а не inline-only строки. После изменения понадобятся source tests, build manifest check, accessibility check для `<details>` и визуальная проверка узких экранов.

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

### Phase A — frontend transparency

Add `chartProvenanceHtml(c)` in a shared Mini App utility or chart module, use it in both chart surfaces, add RU/EN localization keys, escape all values, and add an accessibility test. The disclosure should be user-visible but collapsed by default. Build the hashed bundle and verify that production HTML references the new manifest entries.

### Phase B — normalization correctness

Replace ad hoc normalization in callers with one `ChartRequest` model. Normalize whitespace and numeric representations, validate IANA timezone before any backend call, define explicit DST gap/fold behavior, and attach coordinate source/confidence. Do not silently convert missing timezone to the server timezone. Keep a compatibility parser for old stored chart metadata, but never redraw or recompute historical artifacts silently.

### Phase C — calculation integrity

Add a post-Kerykeion validation layer. It should validate finite numeric outputs, signs and degrees, expected point inventory, house/angle availability, node opposition and aspect policy. Preserve exact values internally and round only at the presentation boundary. Add versioned cache keys and include the full calculation-affecting configuration in provenance.

### Phase D — accuracy evidence

Expand the existing golden corpus into separate deterministic regression fixtures and external comparison artifacts. Use direct `pyswisseph` only as a same-kernel adapter check; use NASA/JPL Horizons where settings are comparable for planetary positions; leave ASC/MC/Placidus/nodes/Lilith/retrograde fields open when the reference does not expose equivalent semantics. No external comparison should be used to claim scientific or universal predictive accuracy.

### Phase E — products and release

Apply the same evidence envelope to transits, synastry, composite and solar returns. Add property tests for date boundaries, longitude wraparound, aspect thresholds, coordinate extremes and repeated serialization. Release only when local tests, differential reports, frontend disclosure, licensing notices and manual cross-surface review agree. A backend version bump must be visible in API metadata and documented in the release record.

## 4. Proposed next implementation ticket

The best next code change is **Frontend Provenance Disclosure + normalization validator P0**:

1. Add localized `chartProvenanceHtml(c)` and render it in chat and full-chart modal.
2. Add frontend tests for complete, missing and malformed provenance objects.
3. Add `ChartRequest` DST gap/fold test cases and coordinate-source fields without changing current valid exact outputs.
4. Add post-Kerykeion schema validation in the engine boundary.
5. Bump adapter version only if the serialized contract changes; otherwise record the additive API field as backward-compatible.

The current audit finds no frontend crash caused by `engine_provenance`; the gap is that the field is **ignored and therefore not visible**. The algorithmic roadmap should be implemented incrementally behind the existing deterministic contracts, with no claim that Kerykeion or Swiss Ephemeris licensing obligations disappear.

## References

[1] [OracleAI ASTROLOGY.md contract](ASTROLOGY.md) — current exact/date-only, backend and provenance rules.

[2] [OracleAI chart contract](../../app/core/chart_contract.py) — versioned calculation metadata and public contract source.

[3] [OracleAI improved engine](../../app/core/astrology_engine.py) — request normalization, fingerprint and bounded cache.

[4] [Kerykeion upstream repository](https://github.com/g-battaglia/kerykeion) — disclosed backend provenance and upstream license source.

[5] [Astrodienst Swiss Ephemeris information](https://www.astro.com/swisseph/swephinfo_e.htm) — Swiss Ephemeris distribution/license information.
