# OracleAI — все следующие шаги и план выполнения

**Дата:** 26 августа 2026
**Источник:** [`TASKS.md`](TASKS.md), [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md), [`ORACLEAI_FINAL_AUDIT.md`](../ORACLEAI_FINAL_AUDIT.md).
**Правило:** локальный зелёный тест не закрывает production-only gate.

## P0 — блокеры публичного релиза

| ID | Следующий шаг | Можно выполнить в sandbox | Итоговый gate |
|---|---|---:|---|
| P0-001 | Развернуть disposable staging с реальным Telegram signed `initData`; проверить tampered/expired/invalid signatures, owner isolation, URL/log redaction и реальные Telegram WebView. | Частично: усиливаем локальные regression tests и документацию. | Нужны реальные Telegram credentials/device. |
| P0-002 | Сертифицировать платёжный sandbox: invoice, duplicate webhook, refund, chargeback/error и reconciliation. | Частично: локально покрыть idempotency и negative cases. | Нужен provider sandbox и settlement evidence. |
| P0-003 | Выполнить live LLM evaluation: grounding, high-stakes refusal, forbidden guarantees, third-party mind reading, language, next step и provider fallback. | Да для deterministic harness и offline judge; live часть зависит от LLM credentials. | Нужен staging/live provider run с zero critical violations. |
| P0-004 | Выполнить backup/restore drill: schema, users, report snapshots, isolation и rollback. | Да для disposable local drill; production restore остаётся внешним. | Нужны production backup/storage permissions. |

## P1 — highest-value product and engineering

| ID | Следующий шаг | План выполнения |
|---|---|---|
| P1-001 | Создать unified cross-tool history: report, Tarot, sessions, palm; owner scope, kind, created-at, evidence/snapshot ID, deep link, deletion. | Добавить versioned read model/API/UI и security tests. |
| P1-002 | Создать memory evaluation fixtures: relevance, opt-in, pause, deletion, isolation, stale/contradictory facts и prompt-injection resistance. | Добавить deterministic dataset, evaluator и thresholds; embeddings не включать без benchmark. |
| P1-003 | Завершить PDF golden-case QA для RU/EN exact/date-only, long name/city, edge coordinates, minimal/maximal and dense-aspect cases. | Автоматизировать generation/text checks и сохранить inspected artifacts; visual pixel review ограничен sandbox. |
| P1-004 | Провести independent calculator comparison для normal, DST, historical timezone, unknown time, edge longitude, high latitude и midnight cases. | Сформировать reproducible local export; независимое сравнение требует authoritative calculator access. |
| P1-005 | Уточнить Vedic/Jyotish school boundary: Lahiri, ayanamsa, nakshatra/dasha/panchang, no Western semantic leakage и golden cases. | Добавить docs, fixtures, tests и explicit product capability state. |
| P1-006 | Закрыть Tarot/Lenormand boundary: 78-card invariants, persisted random draw, replay/seed semantics, reversal и canonical 36-card Lenormand contract. | Добавить contract, tests and UI copy; unsupported Lenormand promises must be hidden. |
| P1-007 | Сохранить immutable report versions при profile update/regeneration. | Уже реализовано в `0e616fb`; продолжить monitor/migration rollout. |
| P1-008 | Реальные E2E journeys: onboarding, natal, date-only, memory, chat, synastry, Tarot, with screenshots/logs. | Добавить browser harness and local artifacts; Telegram device run remains external. |
| P1-009 | Route-by-route API resilience matrix: invalid/missing, backend failure, timeout, rate limit, empty/partial/stale, duplicate, retry, cancellation, expired session. | Добавить matrix, deterministic negative tests, frontend state assertions. |
| P1-010 | Journey observability: correlation IDs, redaction, latency/error/tool/AI/PDF fields and dashboards. | Добавить event assertions and privacy-safe report; dashboards require deployment. |

## P2 — product quality and trust

| ID | Следующий шаг | План выполнения |
|---|---|---|
| P2-001 | Visual QA desktop/mobile for landing, home, chat, profile, chart, Tarot, memory, loading, empty, error and reduced-motion states. | Добавить deterministic screenshot harness, visual baseline and fix the highest-value inconsistencies. |
| P2-002 | Accessibility: keyboard, focus, screen reader, contrast and touch targets. | Add static rules plus automated/manual checks and document exceptions. |
| P2-003 | Localization: glossary, long labels, plurals, mixed-language technical labels and PDF glyphs. | Add glossary/fixtures and RU/EN regression checks. |
| P2-004 | Account deletion/anonymization: confirmation, idempotency, audit behavior and privacy tests. | Implement or close verified contract in API/UI/repositories. |
| P2-005 | Avatar/palm upload lifecycle: validation, size/type, retention/deletion, privacy and low-quality states. | Add malicious/oversized/unsupported/ambiguous-image tests and UI states. |
| P2-006 | Unified PDF template catalog for natal, synastry, Tarot and future products. | Document human/verification layers, localization, snapshot inputs and per-product gates. |
| P2-007 | Performance budgets for chart, chat, memory and PDF. | Run representative benchmark, publish p50/p95 and optimize only measured regressions. |
| P2-008 | Paywall/trial/cancellation/refund UX. | Add UI/API E2E and no-dark-pattern copy review; payment settlement remains external. |

## P3 — deferred expansion

Additional returns, lunar returns, progressions, Davison, relocation, semantic embeddings, richer sharing and CRM connectors remain deliberately deferred. Each requires its own domain contract, evidence, UI, export, security and golden cases before enablement.

## Execution policy for this run

This run executes every locally actionable item that can be completed without real credentials or a production account: unified history, memory fixtures/evaluator, API resilience coverage, visual QA harness and baseline, localization/accessibility checks, Vedic/Tarot contract documentation and tests, performance benchmark, observability assertions, deletion/upload audit improvements and PDF golden-case automation. External gates are kept explicit and will not be falsely marked complete.

## References

[1]: TASKS.md "Authoritative OracleAI backlog"
[2]: TRACEABILITY_MATRIX.md "Requirement-to-evidence matrix"
[3]: ../ORACLEAI_FINAL_AUDIT.md "Previous final audit and external gates"

## Status after the autonomous implementation pass

| ID | Status now | Evidence / remaining boundary |
|---|---|---|
| P0-001 | Partial | Local owner-scope and redaction checks exist; real Telegram signed initData/WebView staging remains external. |
| P0-002 | Partial | Existing local billing/idempotency coverage remains; provider sandbox settlement/refund evidence remains external. |
| P0-003 | Partial, measured | Live `gpt-5-mini` synthetic run: zero critical violations, language 1.0, symbolic next-step 0.9, calibration 0.9; p95 22.14 s misses the 15 s target. |
| P0-004 | Partial, locally drilled | Disposable Python backup/restore drill passes SQLite integrity, report preservation and owner isolation; production backup/storage permissions and rollback remain external. |
| P1-001 | Done locally with explicit palm boundary | Unified `/api/history`, exact Tarot/diary routes, profile History UI and owner-isolation tests cover reports, Tarot, sessions and diary. Palm is intentionally absent until palm artifacts are persisted with retention/deletion semantics. |
| P1-002 | Done locally for synthetic evaluator | Dedicated evaluator covers relevance, irrelevance, pause/no-write, deletion, owner isolation, contradiction detection and prompt-injection-shaped facts; no automatic winner is invented for conflicts. |
| P1-003 | Done locally for synthetic matrix | Six deterministic RU/EN cases cover exact/date-only, long name, DST-shaped input and high latitude; production font/device pixel review remains external. |
| P1-004 | External | Independent authoritative calculator comparison remains external. |
| P1-005 | Done locally for boundary | Lahiri/ayanamsa, date-only behavior, no Western semantic leakage and Vedic capability boundaries are documented and tested; independent calculator comparison remains external. |
| P1-006 | Done locally for enabled Tarot boundary | 78-card invariants, persisted draw, seeded replay, reversal ledger and unsupported Lenormand fallback are tested; a canonical 36-card Lenormand product remains intentionally disabled. |
| P1-007 | Done locally | Append-only report history and immutable IDs are implemented and tested. |
| P1-008 | Done locally for synthetic browser journey | Seeded Playwright baseline covers onboarding, home, chat, profile, chart, history, memory and Tarot at RU/EN mobile widths; Telegram WebView/device and signed-initData journeys remain external. |
| P1-009 | Improved locally | Negative matrix now covers missing identity, validation, paused memory, owner-scoped 404, rate limit and safe correlated 500; full route inventory, timeout/cancellation and expired-session staging remain. |
| P1-010 | Partial | Structured redaction and correlation fields exist; deployment dashboards remain external. |
| P2-001 | Done locally for covered states | Seeded RU/EN harness covers age gate, home, chat, profile, chart, history, memory and Tarot at three mobile widths plus reduced-motion reference; loading/error and desktop pixel review remain. |
| P2-002 | Done locally for automated checks | Playwright checks pass for overflow, unnamed focusables, missing image alt and focus-visible styling; manual screen-reader/contrast review remains. |
| P2-003 | Improved locally | English home fallback was corrected and guarded by regression; broader glossary, pluralization and long PDF typography remain. |
| P2-004 | Done locally for API contract | Confirm-gated idempotent `/api/account/delete` anonymizes PII/history, disables memory/push/age flags and has owner/lifecycle regression tests; production legal/retention sign-off remains external. |
| P2-005 | Partial | Palm visual states and quality guidance exist; full upload retention/deletion and malicious-file matrix remain. |
| P2-006 | Documented | PDF system contract exists; product-specific Tarot/synastry template catalog remains. |
| P2-007 | Measured locally | Directional benchmark reports chart, Tarot, memory and offline PDF p50/p95; live LLM p95 remains 22.14 s versus 15 s target and needs staging optimization. |
| P2-008 | External/partial | Billing logic exists; provider sandbox and visual cancellation/refund journey remain. |

The repository therefore contains no false “all green” claim: local implementation is complete for the rows explicitly marked done, while provider, Telegram, deployment, independent-calculator and production-settlement gates remain visible.
