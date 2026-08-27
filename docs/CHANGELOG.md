# OracleAI — changelog

Все заметные изменения пользовательского продукта, API и эксплуатационных контрактов фиксируются здесь. Временные аудиты и машинные snapshots в changelog не перечисляются как ссылки на файлы.

## Unreleased

### Added

- Добавлены `AI_ONBOARDING_GAUNTLET.md` и `AI_SYSTEM_FINAL_REVIEW.md` как evidence contracts для AI, onboarding, Telegram и admin release review.
- Добавлены regression tests для invalid-time, unknown-city и chart-failure recovery в Telegram onboarding.
- Добавлен runtime regression test на отказ от model-generated tool call вне allow-list текущего агента.
- Добавлены versioned JSON-контракты для natal, synastry, transit, composite и solar returns product paths.
- Добавлены owner-scoped маршруты `POST /api/synastry`, `POST /api/transits`, `POST /api/composite` и `POST /api/returns` с явными precision-gates.
- Mini App получил отдельные journeys «Полная синастрия», «Транзиты», «Композит пары» и «Солнечный возврат»; Astrologer agent получает deterministic evidence для всех путей.
- Реализованы circular midpoints для composite и bounded UTC ephemeris search с локальным timestamp для solar return; extended planets, houses, wheels and prediction semantics остаются отдельными gates.
- Репозиторий очищен от исторических audit snapshots, AI handoff-файлов, generated inventories и одноразовых research artifacts.
- Добавлены `FULL_PRODUCT_SURFACE.md`, `TASKS.md`, `BASELINE.md`, `DOMAIN_METHODS.md`, `AGENT_ARCHITECTURE.md`, `MEMORY.md`, `PDF_SYSTEM.md`, `TESTING.md`, `COMPETITOR_MATRIX.md` и `TRACEABILITY_MATRIX.md` как рабочие контракты завершения.
- Добавлен owner-scoped `GET /api/history`: единый мета-архив отчётов, Tarot, palm readings и chat sessions с actionable deep links без выдачи содержимого личных записей.
- Список памяти теперь отдаёт только inspectable поля; embedding BLOB и имя embedding-модели остаются внутренними. Recall-cache сбрасывается после ручного/AI сохранения, усиления и удаления факта.
- Tarot finalization повторно проверяет владельца и не позволяет перезаписать уже сохранённую интерпретацию; malformed upload size headers для palm получают явный 400.
- Добавлен формальный `tarot-replay-v1`: ledger восстанавливается из сохранённых карт, позиций и ориентаций, а checksum защищает исторический payload от незаметного изменения.
- Добавлен `scripts.pdf_matrix` для локального PDF preflight: 6 детерминированных RU/EN exact/date-only, long-field и edge-latitude кейсов с внешними HTML/PDF артефактами и `summary.json`.
- Добавлен privacy-safe `product_cost_events` ledger: server-owned SKU/catalog/channel/purpose dimensions, LLM retry/latency/token cost, delivery/refund/support categories, retention и product KPI aggregation; gross Stars не объявляются net revenue или contribution.
- Product-cost gross booking теперь присоединяется по `sku + order.surface/channel`, поэтому одинаковый SKU не дублируется между bot и Mini App rows; добавлен regression test.
- Добавлен воспроизводимый `scripts/domain_qa.py` и `ASTRONOMY_REFERENCE_QA.md`: 8/8 критических cross-implementation кейсов проходят, включая date-only и fail-closed ambiguous DST; external ephemeris authority comparison остаётся открытым.
- Добавлен `P0_PRODUCTION_EXECUTION_PLAN.md` с owner-led процедурами, acceptance evidence, go/no-go gate, redaction policy и rollback для Telegram auth, payments, live LLM и backup/restore.


### Changed

- Полная exact natal карта сохранена как canonical path: 10 традиционных планет, 12 домов, ASC/MC, Rahu/Ketu, Lilith, Chiron/Juno/Ceres/Vesta/Pallas, мажорные аспекты и precision-aware ограничения.
- Натальный визуал остаётся в Mode P: серверный Kerykeion → transient SVG → raster PNG/WebP; raw SVG не покидает серверный render pipeline.
- Документация сокращена до текущих product, architecture, API, design, security, deployment, agent, chart-contract и launch-governance источников правды.

### Security

- Синастрия использует только owner-scoped `partner_id`; birth data не принимаются через GET URL и не появляются в публичных cache keys.
- Unknown-time natal charts не получают выдуманные дома, ASC, MC или колесо.
- Transit day snapshots явно маркируются как дневные и не выдаются за точный момент Луны.
- Отчёты переведены на append-only history: `?refresh=true` создаёт новую версию и сохраняет deterministic source/evidence limitations, не удаляя предыдущую.
- Repository hygiene больше не ошибочно блокирует активную `TRACEABILITY_MATRIX.md`; проверка отделяет рабочие контракты от одноразовых audit dumps.
- Добавлена owner-scoped unified history для reports, Tarot, chat sessions и diary с exact routes, `source_id`, безопасным preview и palm boundary; profile History tab получил keyboard-visible cards.
- Live LLM evaluation получил catalog discovery, stratified synthetic run, cost cap, safety/language/calibration/latency gates и provider-correct GPT-5 reasoning effort через `LLM_REASONING_EFFORT`.
- English home fallback переведён в HOME_I18N; добавлены localization regression, Playwright visual/accessibility baseline и финальные per-check quality-gate artifacts.
- Добавлены `NEXT_STEPS.md`, `UNIFIED_HISTORY.md` и `ORACLEAI_CONTINUATION_REPORT.md`; второй pass фиксирует выполненные локальные рекомендации, внешние launch blockers и незелёный LLM p95 latency gate.
- Подготовлен research-only документ `MONETIZATION_STRATEGY.md`: Hybrid B, публичные pricing anchors, unit economics, ethical upsell guardrails и owner decisions; код, UI, цены и payment logic на этом этапе не изменялись.
- Добавлены synthetic memory evaluator, API resilience matrix, PDF golden-case runner, Tarot contract tests, disposable backup/restore drill and directional chart/Tarot/memory/PDF performance benchmark.
- Account deletion получил confirm-gated idempotent API contract; anonymization clears user history and disables memory, push and age flags. Memory recall cache now respects requested result limits.
- Playwright visual baseline расширен до chart/history/memory/Tarot states, reduced-motion reference and seeded synthetic data; localized accessible names added for the previously failing inputs and tool controls.
- Agent prompt/context hardening централизовал untrusted wrappers для memory, profile summaries, diary и evidence blocks; runtime теперь дополнительно отклоняет forbidden model tool calls по server-side agent allow-list; добавлен deterministic consistency gate против взаимоисключающих start/stop directives, а pre-tool fallback теперь intent-gated для chart/transit calls.
- Telegram onboarding больше не принимает произвольную невалидную строку времени как «время неизвестно»; неизвестный город и сбой расчёта карты оставляют FSM на retryable city state с локализованным объяснением.
- Mira получил topic-aware reshoot guidance, explicit `reading_id` retrieval и optional integrity-checked ONNX line evidence helper с vendored MIT model variants; raw masks не сохраняются, hard precheck skips heavy CV, а LLM остаётся авторитетом для видимого изображения и uncertainty.
- Последний bounded live synthetic LLM run: 12/12 cases, 0 critical violations, mean 0.9167, language 1.0, next-step 1.0, calibration 0.8; p95 25.088 s против цели 15 s остаётся staging blocker. Palm-line CPU baseline: fp16 около 8.35 s p50, int8 остаётся отдельным quality tradeoff.
- Добавлен явный authenticated boot recovery state: Mini App больше не показывает полноценный home shell после неуспешного `/api/me`, а предлагает повторить вход внутри Telegram.
- Account deletion теперь доступен из Profile Summary через локализованный confirm-gated UI, вызывает существующий idempotent `/api/account/delete` и показывает terminal success state без повторного запроса данных удалённого профиля.
- Standalone agent/skill benchmark scripts получили repository-root bootstrap; direct invocation добавлен в CI как regression contract.
- Selfcheck limits path теперь явно подтверждает `age_confirmed=1` перед проверкой платного chat flow; design contract checker учитывает visual и payments CSS layers, а VISUAL QA больше не ссылается на отсутствующие generated artifacts.

## 2.0.0 — 2026-08-12

### Added

- Ежедневный микро-ритуал, age-gate 16+, RU/EN Mini App, opt-in memory, дневник, Tarot, Matrix, palm evidence flow, аналитика и controlled-beta documentation.

### Changed

- Mini App перестроен вокруг чата с отдельными проводниками, explicit tool actions, accessibility states и responsive dark visual system.

### Security

- Server-side privacy and memory-off boundaries, safety routing and high-stakes disclaimers стали частью общего runtime-контракта.

## Release policy

Перед каждым release необходимо обновить этот файл, соответствующие canonical docs и тесты. Public launch не считается готовым только на основании локальных тестов: остаются внешние проверки production deployment, real Telegram devices, live LLM/provider quality, privacy/legal review, payments и Kerykeion/Swiss Ephemeris licensing.
