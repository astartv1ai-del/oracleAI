# OracleAI Engine и post-Engine readiness summary

**Дата:** 2026-08-27
**Ветка:** `master`
**Архитектура:** `OracleAI Engine` → `OracleKerykeionEngine` → `Kerykeion 5.12.9` → `Swiss Ephemeris`

## 1. Общий статус

OracleAI Engine имеет production-oriented локальную реализацию для текущего Western astrology product scope. Единственный расчётный путь проходит через typed normalization, configuration/request fingerprints, Kerykeion backend, post-calculation validation и versioned calculation/evidence contract. API, product contracts, specialized placements, PDF, LLM evidence и Mini App используют один источник расчётных фактов.

> Статус `PASS` означает, что локальная реализация и её автоматические проверки зелёные. Он не означает завершённую production-сертификацию Telegram, платёжных провайдеров, live LLM, deployment, backup/restore или юридическую проверку.

## 2. Компоненты Engine

| Компонент | Реализовано | Метрика/доказательство |
|---|---|---|
| Typed input boundary | `ChartRequest` и `OracleKerykeionEngine.normalize()` | Нормализуются дата, время, timezone, city, coordinates и source/confidence; raw text не используется как identity. |
| Precision state machine | `exact`, `time_without_location`, `date_only`, `interval`, `sun_only` | Angular data, ASC/MC и houses выдаются только при достаточной точности. |
| DST handling | Gap/fold detection | Nonexistent и ambiguous local time не выбираются молча; interval mode сохраняет candidates без ложной angular precision. |
| Geography provenance | Source/confidence/status | Координаты и timezone имеют явный provenance; neutral reference маркируется. |
| Reproducibility | Request/configuration fingerprints | В hash входят product policy, active points, aspect/node settings, backend/runtime versions и normalized request. |
| Numerical integrity | Exact vs presentation values | UI rounding не участвует в aspect, midpoint или house decisions. |
| Output validator | Fresh и cached results | Проверяются finite/range values, point inventory, houses, angles, nodes, aspects и metadata agreement. |
| Fail-closed fallback | Bounded fallback | Malformed backend output не сохраняется как частичная карта и не передаётся LLM как факт. |
| Product validators | Natal, synastry, transit, composite, solar return | Проверяются precision compatibility, roles, exact longitudes, shortest midpoint, timestamps и return ordering. |
| Specialized placements | Moon, Venus, Rising, Nodes, Asteroids и другие Western placements | Используют canonical `astro.compute_chart`; legacy response shape сохранён, provenance propagated. |
| Provenance disclosure | API, chat, full chart, PDF | `OracleAI Engine`, adapter, Kerykeion, Swiss Ephemeris и licensing notice раскрыты явно. |
| Chart image integration | Validated snapshot → render-only adapter | Snapshot input/configuration is authoritative; stale configuration is rejected; render cache includes request/config/runtime fingerprints; raw SVG remains transient. |

## 3. Platform и product components

| Область | Текущее состояние | Ограничение |
|---|---|---|
| Mini App | Enabled with limitation | Реальный Telegram WebView/device matrix требует внешней проверки. |
| API/auth | Enabled with limitation | Signed Telegram identity реализована; real initData/device QA внешний gate. |
| Chat/agents/LLM evidence | Enabled with limitation | Deterministic facts отделены от LLM prose; live provider quality и p95 требуют staging. |
| Tarot/numerology/matrix/palm | Enabled with limitations | Domain-specific corpus, visual assets и live quality требуют отдельных gates. |
| Reports/PDF/history | Enabled with limitations | Unified bounded history и immutable report versions есть; полная visual regression ещё расширяется. |
| Payment/entitlements | Enabled with limitation | Server-side idempotency, webhook signature и history есть; provider certification/settlement drill внешние. |
| Admin/payment health/reconciliation | Enabled with limitation | Owner-only reconciliation, safe aggregate export, webhook timeline, cooldown/quiet hours и provider dashboard links реализованы. |
| Privacy center | Enabled with limitation | Export/anonymization/self-service endpoints есть; legal retention sign-off и real deletion E2E внешние. |
| User notifications | Enabled with limitation | Mini App inbox, unread count, mark-all-read и morning forecast preference реализованы; Telegram delivery/device QA внешний gate. |

## 4. QA metrics

| Gate | Результат |
|---|---|
| Domain QA | **8/8 PASS**; direct Swiss comparison классифицируется как same-kernel adapter QA. |
| Non-Palm regression suite | **PASS**; Palm/ONNX environment-specific tests не считаются Engine gate. |
| Placement/product/API focused suites | **PASS**; notification inbox tests включают owner isolation, dedupe, privacy redaction и idempotent read-all. |
| Python lint/compile | **PASS**: Ruff и `compileall`. |
| Frontend | **PASS**: provenance contract, JS syntax, hashed build, static asset, design, contrast и cache-busting checks. |
| Browser smoke | **PASS**: RU/EN full-chart provenance, details toggle, localized license copy, v107 notification inbox, unread/read action and morning forecast toggle. |
| Release gate | **PASS** для локального non-Palm product scope. |
| Selfcheck | **PASS**; ожидаемые skips: live LLM/provider credentials и production configuration values. |
| Overall public production readiness | **BLOCKED by external gates**, а не локальным Engine failure. |

## 5. Что реализовано после Engine rollout

В post-Engine iteration добавлен настоящий user-facing notification center. Новые owner-scoped endpoints — `GET /api/notifications`, `POST /api/notifications/read-all`, `GET/PATCH /api/notifications/preferences`. Inbox материализует только уже сохранённые server-owned forecasts, использует dedupe key, unread/read timestamp и не принимает пользовательский notification body. Mini App bell теперь показывает входящие summaries, unread count, mark-all-read и toggle утреннего прогноза. Provider alerts и secondary channels остаются admin-only.

Также обновлены API documentation, product-surface readiness matrix, completion plan/report и regression tests. Это расширяет пользовательскую функциональность без добавления второго источника астрологических расчётов и без передачи LLM права вычислять chart facts.

## 6. Следующие задачи

| Приоритет | Задача | Что требуется | Статус |
|---|---|---|---|
| P0 external | Telegram auth/device QA | HTTPS staging bot, disposable accounts, iOS/Android/Desktop WebView matrix, signed initData evidence | Не выполняется честно из sandbox без реального staging. |
| P0 external | Live LLM quality/SLO | Approved provider/model route, cost cap, latency rubric, grounding/safety evaluation dataset | Local fallback PASS; live evidence отсутствует. |
| P0 external | Production backup/restore/rollback | PostgreSQL/off-site encrypted backup, checksum, RPO/RTO, restore and rollback drill | Runbook/local SQLite checks есть; production drill external. |
| P0 external | Docker/HTTPS game day | Compose build, healthchecks, SIGTERM, TLS/DNS, provider outage injection | Требует deployment environment. |
| P1 evidence | Independent differential corpus | Equivalent NASA/JPL/Horizons UTC planetary cases; comparable/non-comparable field classification | Same-kernel QA есть; independent artifact остаётся открытым. |
| P1/P2 | Notification expansion | Practice/lunar/subscription events, per-category preferences, delivery audit and retry policy | Базовый inbox/preferences реализован; новые categories требуют product copy and scheduler contract. |
| P2 product | History/favorites expansion | Generalized saved-results contract, cross-tool archive, explicit favorite/delete semantics | Unified bounded history есть; generalized favorites остаются partial. |
| P2 product | More astrology products | Lunar return, progressions, Davison and relocation contracts with validators and precision envelope | Не включать в UI до contract/evidence completion. |
| P2 quality | Memory contradiction workflow | User-visible stale/contradiction review, correction, provenance and adversarial corpus | Current bounded retrieval and edit/delete работают; workflow не завершён. |
| External/legal | Licensing and assets review | Kerykeion AGPL/commercial model, Swiss Ephemeris distribution terms, Tarot/visual asset rights, DPA/retention review | Документы и disclosure есть; formal sign-off внешний. |

## 7. Ограничение accuracy claim

OracleAI Engine улучшает **семантику входов, воспроизводимость, precision truthfulness, cache safety, output validation, fail-closed behavior, product consistency и provenance**. Поскольку численный backend остаётся Kerykeion/Swiss Ephemeris, этот документ не заявляет превосходство OracleAI над Swiss Ephemeris по астрономической точности. Независимый differential corpus должен сравнивать только эквивалентные UTC planetary fields и отдельно отмечать несопоставимые ASC/MC, Placidus, nodes, Lilith и product semantics.

## References

[1]: [ENGINE_COMPLETION_PLAN.md](DOMAIN/ENGINE_COMPLETION_PLAN.md) — полный implementation plan и acceptance criteria.
[2]: [ENGINE_COMPLETION_REPORT.md](DOMAIN/ENGINE_COMPLETION_REPORT.md) — выполненные Engine steps и QA evidence.
[3]: [ENGINE_PROVENANCE_AND_ACCURACY_ROADMAP.md](DOMAIN/ENGINE_PROVENANCE_AND_ACCURACY_ROADMAP.md) — roadmap accuracy/provenance и external evidence boundaries.
[4]: [FULL_PRODUCT_SURFACE.md](FULL_PRODUCT_SURFACE.md) — inventory product components and limitations.
[5]: [PRODUCTION_GAUNTLET.md](PRODUCTION_GAUNTLET.md) — production readiness gates and external blockers.
[6]: [API.md](API.md) — HTTP contracts, notification endpoints and privacy rules.
[7]: [NOTIFICATION_INBOX_BROWSER_TEST.md](DOMAIN/NOTIFICATION_INBOX_BROWSER_TEST.md) — interactive RU notification inbox evidence.
[8]: [https://github.com/g-battaglia/kerykeion](https://github.com/g-battaglia/kerykeion) — disclosed backend source.
[9]: [https://www.astro.com/swisseph/swephinfo_e.htm](https://www.astro.com/swisseph/swephinfo_e.htm) — Swiss Ephemeris distribution/licensing reference.
[10]: [DOMAIN/ENGINE_INTEGRATION_AUDIT_2026-08-27.md](DOMAIN/ENGINE_INTEGRATION_AUDIT_2026-08-27.md) — caller, timing, render boundary and cache integration audit.
