# OracleAI — автономный backlog

**Дата baseline:** 2026-08-26  
**Исходный коммит:** `e25c9d5870cd7acd4e65e9ca533e864b2a2181d5`  
**Правило:** задача считается закрытой только после implementation, tests, relevant QA, documentation and evidence.

## Completed baseline checks

| Check | Result | Evidence |
|---|---|---|
| Dependency installation | **Pass** after installing `build-essential`, `pkg-config`, `libsqlite3-dev`, `python3.12-dev` | pinned `requirements-dev.txt` installed successfully |
| Repository self-check | **Pass**, two expected skips: live LLM and incomplete local `.env` | `APP_ENV=dev DEV_MODE=1 LLM_PROVIDER=off python3 -m scripts.selfcheck` |
| Automated tests | **Pass** | `APP_ENV=dev DEV_MODE=1 LLM_PROVIDER=off pytest -q` |
| Python syntax | **Pass** | `python3 -m compileall -q app scripts tests` |
| JavaScript syntax | **Pass** | `node --check` for all `miniapp/js/*.js` and `admin/*.js` |
| Ruff | **Pass** | `ruff check app scripts tests` |
| Release gate | **Pass** | `python3 -m scripts.release_gate` |

## P0 — release blockers

| ID | Subsystem | User journey | Problem / evidence | Acceptance criteria | Status |
|---|---|---|---|---|---|
| P0-001 | Security / auth | Any authenticated request | Production auth requires real Telegram initData and secrets; local baseline cannot validate real signature or device behavior. | Run disposable staging with real signed initData, verify invalid/expired/tampered signatures, owner isolation and no PII in URLs/logs. | External gate |
| P0-002 | Payments | Purchase → webhook → entitlement | Local tests prove signature/idempotency logic, not provider settlement or refund reconciliation. | Complete sandbox provider certification for invoice, duplicate webhook, refund, chargeback/error and reconciliation; capture logs/evidence without secrets. | External gate |
| P0-003 | Safety / AI | User asks for high-stakes or deterministic fact | Offline guardrails pass, but live-provider behavior is not tested without provider credentials. | Execute live evaluation set for grounding, forbidden guarantees, medical/diagnostic claims, third-party mind reading and refusal behavior; zero critical violations. | External gate |
| P0-004 | Operations | Deploy → migrate → recover | Backup scripts and runbook exist, but a real restore drill is not executable from this sandbox alone. | Run disposable backup/restore drill and verify schema, user isolation, report snapshots and rollback. | External gate |

## P1 — highest-value local work

| ID | Subsystem | User journey | Problem / evidence | Acceptance criteria | Status |
|---|---|---|---|---|---|
| P1-001 | Product / history | Returning user → previous research → new tool | History was split across reports, tarot, sessions and palm paths. | Unified owner-scoped read model now returns kind, created-at, evidence ID, actionable deep link and deletion semantics; API isolation/privacy tests pass. | **Done locally**; client surface adoption remains a visual/E2E gate |
| P1-002 | Memory | Enable memory → chat → recall → edit/delete | Retrieval quality and contradiction UX still need a dedicated evaluation dataset. | Server-side opt-in/privacy remains enforced; memory listing no longer exposes embeddings and recall cache invalidates after manual/AI writes and deletion. | **Improved locally**; relevance/contradiction evaluation remains open |
| P1-003 | PDF | Calculate → interpret → save → regenerate | Existing PDF path passes smoke tests, but premium two-layer editorial quality and visual regression are not evidenced for the full golden-case matrix. | Generate RU/EN exact-time and date-only, long-name/city, edge-coordinate, minimal/maximal and dense-aspect reports; render and inspect pages; fix clipping, glyph, density and truth-state issues. | Open |
| P1-004 | Domain QA | Natal / date-only / products | The repo has canonical contracts and tests, but independent authoritative calculator comparison is not captured for all required cases. | Record two independent calculator comparisons with identical settings for normal, DST, historical timezone, unknown time, edge longitude, high latitude and midnight cases; explain every difference. | External/partially open |
| P1-005 | Vedic boundary | Vedic tool → interpretation | UI/agent concepts exist, while complete school/methodology/golden-case boundary documentation is incomplete. | Specify Lahiri sidereal rules, ayanamsa, nakshatra/dasha/panchang boundaries, no western semantic leakage, golden cases and error behavior. | Open |
| P1-006 | Tarot / Lenormand | Question → draw → replay → history | Tarot draw and interpretation are separated, but explicit replay/seed contract and a canonical Lenormand product are not fully evidenced. | Document and test 78-card Tarot invariants, random draw persistence, replay semantics, reversal, and separately define or remove unsupported Lenormand promises. | Open |
| P1-007 | Data integrity | Profile update → historical report | Legacy unique key plus `INSERT OR REPLACE` destroyed prior report versions. | Append-only schema/migration, immutable `report_id`, owner-scoped retrieval, deterministic source metadata and regression tests prove old rows survive regeneration. | **Done locally** |
| P1-008 | E2E | New and returning users | Existing tests are mainly API/core; real browser critical paths are not yet captured. | Add automated browser or equivalent integration flows for onboarding, natal, date-only, memory, chat, synastry and tarot with screenshots/logs. | Open |
| P1-009 | API resilience | Any tool | Error matrix requires invalid/missing input, network/backend failure, timeout, rate limit, empty/partial/stale result, duplicate, retry, cancellation and expired session UX. | Malformed palm upload size headers now return a safe 400 instead of an internal error; broader route matrix is still open. | **Improved locally**; broader resilience matrix remains open |
| P1-010 | Observability | Production incident | Structured logs exist, but journey-level evidence, correlation and tool/AI/PDF failure dashboards require verification. | Confirm correlation IDs, redaction, latency/error fields and event dictionary for key journeys without sensitive payloads. | Open |

## P2 — product quality and trust

| ID | Subsystem | Problem | Acceptance criteria | Status |
|---|---|---|---|---|
| P2-001 | UX / design | Full design contract exists, but visual QA across mobile/desktop and state variants is not evidenced. | Capture visual regression matrix for landing, home, chat, profile, chart, tarot, memory, loading, empty, error and reduced-motion states; fix inconsistencies. | Open |
| P2-002 | Accessibility | Static code checks do not prove keyboard, screen reader, focus, contrast and touch-target behavior. | Run automated accessibility checks plus manual keyboard/mobile review; document exceptions and fixes. | Open |
| P2-003 | Localization | RU/EN strings exist; mixed-language and long-form PDF/browser typography need verification. | Create glossary and test all supported locales, long labels, technical calculation labels, pluralization and report glyphs. | Open |
| P2-004 | Account lifecycle | Self-service account deletion is not confirmed as a complete product journey. | Add deletion/anonymization contract, confirmation, idempotency, audit behavior and privacy tests. | Open |
| P2-005 | Avatar / uploads | User avatar and palm uploads have different maturity levels and retention rules. | Define upload validation, size/type limits, retention/deletion, privacy and low-quality UI states; test malicious/oversized files. | Open |
| P2-006 | Unified report templates | PDF components are reusable but not yet a documented template catalog for all supported product kinds. | Document human/verification layers, page components, localization and snapshot inputs for natal, synastry, tarot and future products. | Open |
| P2-007 | Performance | Baseline has no measured latency budget for chart, chat, memory and PDF. | Run local benchmark with representative profiles and conversations; define budgets and optimize only measured regressions. | Open |
| P2-008 | Growth / monetization UX | Billing logic is tested, but paywall and cancellation UX are not visually/E2E verified. | Verify transparent pricing, entitlement errors, trial, cancellation and refund copy with no dark patterns. | Open |

## P3 — later improvements

| ID | Subsystem | Candidate | Acceptance criteria | Status |
|---|---|---|---|---|
| P3-001 | Chart products | Additional returns, lunar returns, progressions, Davison and relocation | Add only with separate domain contract, evidence, UI, export and golden cases. | Deferred |
| P3-002 | Semantic memory | Optional embeddings and relevance ranking | Add benchmark proving improvement over lexical retrieval and preserve opt-in/privacy boundaries. | Deferred |
| P3-003 | Sharing | Richer report/share cards | Add only after privacy, localization and visual regression gates pass. | Deferred |
| P3-004 | CRM | External support/CRM connector | Add only after connector/security review and minimum product need is established. | Deferred |

## Working rules

Before closing any task, record the changed files, tests, visual/domain/security QA, rollback approach and evidence link in `docs/TRACEABILITY_MATRIX.md`. Do not claim a local check proves an external production gate. Keep deterministic facts immutable and make every limitation visible in API, UI, AI and PDF.
