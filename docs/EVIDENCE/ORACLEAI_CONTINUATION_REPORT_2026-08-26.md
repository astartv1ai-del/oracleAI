>
> **STATUS: HISTORICAL**
> **SUPERSEDED BY:** [`docs/RELEASE/CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md)
> **LAST VERIFIED:** 2026-08-26
> This file is retained as dated evidence or context. It is not the current source of truth.

# OracleAI — continuation implementation report

**Дата:** 2026-08-27
**Ветка:** `master`
**Репозиторий:** `astartv1ai-del/oracleAI`
**Статус:** локально завершённый implementation pass; public launch не заявляется

## Executive summary

Новый implementation pass выполнен автономно по полному реестру рекомендаций из [ARCHIVE/NEXT_STEPS_2026-08-26.md](../ARCHIVE/NEXT_STEPS_2026-08-26.md) и authoritative backlog [RELEASE/TASKS.md](../RELEASE/TASKS.md). Дополнительно закрыты локальные gaps по memory evaluation, API resilience, account deletion, Tarot invariants, PDF golden cases, backup/restore drill, performance measurement, seeded browser visual coverage и end-to-end LLM-agent context integrity. Добавлены единые untrusted-data wrappers, consistency gate, intent-gated pre-tools и auxiliary palm-line CV evidence. Все изменения проходят локальные gates; public launch по-прежнему не заявляется.

> Локальный green gate не равен production readiness. Реальные Telegram WebView/initData, production deployment, payment settlement, backup/restore, legal/licensing approval, independent calculator comparison и полный PDF golden-case matrix требуют внешней среды и sign-off владельца.

## Полный список рекомендаций и результат

| Приоритет | Рекомендация | Выполнено в этом pass | Остаток / честный статус |
|---|---|---|---|
| P0 | Безопасный production startup, Telegram signed initData, secret hygiene и fail-closed режим | Усилены локальные self-check, release gate и hygiene checks; dev-only fallback остаётся защищённым | Реальный Telegram device/initData и production deployment не проверены; внешний gate открыт |
| P0 | Достоверность natal/date-only, immutable report history и PDF truth-state | Append-only history, explicit refresh/report identity и date-only sign-only PDF behavior сохранены и покрыты regression tests | Независимое сравнение с внешним калькулятором и полная PDF matrix остаются открыты |
| P0 | Evidence-first agent, safety и grounded LLM behavior | Offline evaluation расширен; live synthetic runner добавлен с safety, language, next-step, calibration и p95 gates; shared prompt builder separates deterministic profile evidence from untrusted memory and rejects opposing start/stop directives | Нужна provider/model review на staging и human review production-like cases; latest p95 remains above target |
| P0 | Privacy, memory consent/deletion и owner isolation | Unified history не возвращает raw bodies, owner isolation покрыта API tests, memory evaluator 7/7, confirm-gated deletion and disposable backup drill added | Production privacy/legal sign-off, encrypted storage permissions and rollback ceremony remain external |
| P1 | Unified cross-tool history | Добавлен `GET /api/history` для reports, Tarot, chat sessions и diary; exact owner-scoped Tarot/diary routes; Profile History cards/actions | Palm намеренно исключён: first-class retained palm-history artifact отсутствует; это explicit product boundary |
| P1 | Chart product surface and capability honesty | Existing natal, synastry, transit, composite and returns contracts retained; expanded-chart/direct scripts now run from repo root | Extended planets/houses/wheels, full route E2E и independent oracle comparison остаются открыты |
| P1 | Visual UX and accessibility | Seeded Playwright harness captures RU/EN age gate, home, chat, profile, chart, history, memory and Tarot at 360×800, 390×844 and 430×932; checks overflow, unnamed focusables, image alt and reduced-motion reference | Full desktop matrix, manual keyboard/screen-reader/contrast review and loading/error states remain open |
| P1 | Localization and copy integrity | English home hero/helper fallback moved to `HOME_I18N`; regression prevents the previous Russian leakage | Full glossary, pluralization, long-label and all-PDF locale review remain open |
| P1 | LLM latency, provider correctness and evaluation repeatability | Catalog discovery, bounded concurrency, cost cap, reusable response mode, provider metadata, GPT-5 `extra_body.reasoning.effort`, safe-negation scoring, calibration patterns, intent-gated pre-tools and deterministic consistency gate added | Latest 12-case live run: quality passes (mean `0.9583`, next-step `1.0`), but p95 is `23.899 s` versus `<=15 s`; latency blocker remains open |
| P1 | Billing, payments and monetization | Existing signed-webhook/idempotency code and documentation retained; no production action attempted | Payment sandbox, settlement/reconciliation/refund and entitlement E2E require credentials and provider access |
| P1 | Operations, migration and backup/restore | Local reproducibility, migration tests, pip-audit, release gates and disposable SQLite backup/restore drill pass | Production encrypted storage permissions, monitoring/alerting and rollback rehearsal remain external |
| P2 | Design-system and visual regression coverage | Deterministic seeded mobile baseline now covers chart/history/memory/Tarot and reduced-motion; stale mixed-language state corrected | Expand to desktop, loading/empty/error and manual visual review |
| P2 | Accessibility | Automated DOM checks pass for covered states; focus-visible and tap-target styles added | Manual assistive-technology and contrast review remains open |
| P2 | Account lifecycle and upload retention | Confirm-gated idempotent deletion API and anonymization tests pass; palm upload matrix covers type/size/format/low-quality and raw-image non-retention; Mira now has topic-aware reshoot guidance and auxiliary ONNX line evidence | Consented capture-distribution accuracy, optional MediaPipe asset/device validation, legal retention sign-off and real storage lifecycle review remain external |
| P2 | Report template catalog and performance budget | PDF template catalog and directional chart/Tarot/memory/PDF/palm-line p50/p95 benchmark added | Synastry/Tarot export templates, production SLOs, palm CV model choice and live LLM p95 optimization remain open |
| P3 | Growth, analytics, competitor learning and future product expansion | Existing analytics, competitor, composite and returns documentation retained and linked | Experimentation, public SEO/content, additional chart schools and growth rollout need product decisions and production data |

The complete per-item register, owners and acceptance criteria remain in [RELEASE/TASKS.md](../RELEASE/TASKS.md), while traceability from requirement to implementation and evidence is in [EVIDENCE/TRACEABILITY_MATRIX_2026-08-26.md](TRACEABILITY_MATRIX_2026-08-26.md). The unified archive contract is in [FEATURES/HISTORY.md](../FEATURES/HISTORY.md).

## Implemented source changes

The backend now exposes a normalized, owner-scoped cross-tool archive without raw message, diary or memory bodies. Reports, Tarot readings, active chat sessions and diary entries have stable `source`/`source_id` identities and deep-link semantics; Palm is explicitly not presented as historical data. Exact Tarot and diary routes enforce the same owner boundary. Account deletion is confirm-gated and idempotent; anonymization clears personal history and disables memory, push and age flags.

The Mini App Profile History tab renders normalized archive cards with source labels, dates, previews, status and action routing. Card actions use existing delegation, show focus-visible states and maintain mobile tap targets. The English home fallback now resolves through locale dictionaries rather than embedding Russian copy in a shared fallback path.

The LLM quality path now separates catalog discovery, synthetic sampling, bounded requests, response envelopes and deterministic scoring. The scorer does not treat a safe limitation as an unsupported affirmative claim, and it recognizes broader date-only overclaim patterns. GPT-5-compatible requests receive configurable reasoning effort only when supported by the provider path. The shared prompt builder labels chart/Matrix as deterministic profile evidence and memory/summary/diary/history as bounded untrusted data; a deterministic consistency gate rejects opposing start/stop directives.

Direct invocation of quality scripts is reproducible from the repository root because the scripts bootstrap the project path. New synthetic memory, API resilience, PDF golden-case, backup/restore, agent-context-contract and extended performance runners are also repository-root reproducible. The vendored palm-line helper verifies an allow-listed SHA-256 and never stores raw masks; Mira receives only bounded CV summaries and actionable reshoot instructions. Repository hygiene now permits the required traceability matrix. Generated screenshots, raw response JSONL and gate logs are kept outside the source tree and are not committed.

## Verification evidence

The final local verification was rerun after code and documentation synchronization. The following checks passed: full `pytest`, Ruff, Python compilation, JavaScript syntax, self-check, release gate, design contract, agent quality, domain evaluations, skill-routing benchmark, repository hygiene, cache-busting, expanded chart checks, deterministic visual baseline, offline LLM evaluation, synthetic memory evaluation, backup/restore drill, PDF golden-case matrix, agent-context contract checker, palm-line model contract/inference and extended performance benchmark. The previous full gate summary was `overall_status=0`; targeted post-hardening tests also pass. Generated logs remain outside the repository.

The deterministic seeded visual harness passed for every covered RU/EN state and viewport: 6 viewports × 9 states, no horizontal overflow, zero unnamed focusable controls and zero images without `alt` attributes; the 390px reference context reports reduced-motion preference. This is an automated baseline, not a claim of complete manual accessibility approval.

The latest bounded live synthetic LLM run used `gpt-5-mini`, 12 synthetic cases, maximum 350 output tokens, four workers and a `$0.25` cap. It recorded estimated worst-case cost `$0.009036`, zero critical violations, mean score `0.9583`, language `1.0`, symbolic next-step `1.0`, symbolic calibration `0.9` and p95 latency `23.899 s`. Safety and quality dimensions passed; the explicit p95 target `<=15 s` failed and remains a release blocker.

## External blockers and release decision

No production claim is made for the following items because they require access that is not available in a local repository run: real Telegram device/WebView signed `initData`, production HTTPS deployment and rollback, payment provider sandbox plus settlement/reconciliation/refunds, production encrypted backup/storage permissions and rollback rehearsal, independent astrology calculator comparison, full route-level E2E with real authentication, complete desktop/PDF golden-case visual review, Kerykeion/Swiss Ephemeris licensing confirmation, and legal/privacy review.

**Decision:** the repository is ready for the next controlled staging review, not for an unconditional public launch. The immediate engineering blocker is LLM p95 latency at `22.14 s`; the immediate operational blockers are the external gates above. This report deliberately does not convert any unavailable check into a pass.

## References

[1]: [ARCHIVE/NEXT_STEPS_2026-08-26.md](../ARCHIVE/NEXT_STEPS_2026-08-26.md) — полный реестр P0–P3 рекомендаций.
[2]: [RELEASE/TASKS.md](../RELEASE/TASKS.md) — authoritative backlog and acceptance criteria.
[3]: [EVIDENCE/TRACEABILITY_MATRIX_2026-08-26.md](TRACEABILITY_MATRIX_2026-08-26.md) — requirement-to-code-to-evidence mapping.
[4]: [LLM_EVALUATION.md](../LLM_EVALUATION.md) — LLM quality contract and live-run policy.
[5]: [EVIDENCE/LOCAL_BROWSER_BASELINE_2026-08-27.md](LOCAL_BROWSER_BASELINE_2026-08-27.md) — browser, PDF and deterministic visual findings.
[6]: [FEATURES/HISTORY.md](../FEATURES/HISTORY.md) — cross-tool archive contract and privacy boundary.
[7]: [LLM_AGENT_TECHNICAL_AUDIT.md](../AI_SYSTEM.md) — agent context, prompt integrity, tool scope and palm vision audit.
[8]: [PALM_ENGINE_RESEARCH.md](../PALM_ENGINE_RESEARCH.md) — palm engine research and integration rationale.
