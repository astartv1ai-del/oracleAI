# OracleAI — remaining tasks and blockers before public launch

**Дата статуса:** 25 августа 2026 года  
**Source of truth:** `docs/audit/MASTER_REQUIREMENTS_STATUS_2026-08-25.md` и `docs/LAUNCH_GOVERNANCE.md`  
**Current release decision:** **NO-GO for public launch; controlled beta only after owner-approved staging gates.**

## Executive summary

The local engineering baseline is green: 469 tests pass, static checks and domain/routing checks pass, the scheduler has persistent single-owner recovery, and the evidence set is committed. The remaining work is primarily **production evidence and external acceptance**, not a reason to mark unverified capabilities as complete. The highest-risk items are the nine P0 gates that must be closed before any external traffic, followed by seven P1 gates required before public launch.

The list below separates implementation work that can be performed in the repository from actions that require a production-like environment, qualified external reviewers, payment-provider sandbox access, real Telegram devices, or an accountable release owner.

## P0 — required before any external traffic

| Priority | Task / blocker | Current status | Acceptance evidence required | Owner / dependency |
|---|---|---|---|---|
| P0-1 | Production configuration and fail-closed deployment | **OPEN** | A production-like run with `APP_ENV=production`, `DEV_MODE=0`, HTTPS `WEBAPP_URL`, externally provisioned Telegram/admin secrets, secure headers and no dev-user bypass | Operations; requires isolated staging secrets/domain |
| P0-2 | Staging isolation | **OPEN** | Separate bot token, database, LLM/payment credentials and domain; seeded synthetic users only; proof that staging cannot address production resources | Operations / Security |
| P0-3 | Live LLM safety and reliability | **OPEN** | Versioned live-provider evaluation: strict JSON success, grounding, safety red-team, prompt-injection resistance, timeout/retry/circuit-breaker behavior, p95 latency, token/cost budget and fallback rates | AI/Safety + Operations; requires provider access |
| P0-4 | Palm quality gate | **OPEN** | Approved synthetic/licensed image benchmark, ≥99% valid response schema rate, observed p95 vision latency, quality/`needs_photo` fallback, no medical or longevity claims, and privacy/retention evidence | AI/Product; requires live multimodal provider and image fixture set |
| P0-5 | Real-device UX | **OPEN** | Telegram iOS, Android and Desktop matrix covering first launch, 16+ gate, onboarding, RU/EN, permissions, chart, chat, Stop/retry, Palm upload, offline/slow provider, share, PDF and checkout return | Product/QA; requires device access |
| P0-6 | Privacy and legal review | **EXTERNAL** | Qualified review of Privacy/Terms/16+, retention/deletion, cross-border LLM processing, intended first-wave countries, age/payment eligibility and claims | Product/Legal; cannot be closed by local tests |
| P0-7 | Production backup and restore | **PARTIAL** | Encrypted off-site backup, key custody, checksum, retention, scheduled job evidence, isolated restore drill, post-restore integrity/selfcheck and RPO/RTO result | Operations; local disposable encrypted fixture already passes |
| P0-8 | Incident response | **OPEN** | Severity matrix, contact tree, named on-call owner, provider/payment/data incident tabletop, escalation templates and recovery/rollback commands | Operations / Support |
| P0-9 | Production monitoring | **PARTIAL** | Real dashboards and test alerts for health, HTTP 5xx, webhook failures, LLM success/fallback/cost, scheduler freshness, backup age, funnel and safety signals; confirmed recipients and runbook ownership | Operations; local scheduler status/alert parser already passes |

## P1 — required before public launch

| Priority | Task / blocker | Current status | Acceptance evidence required | Owner / dependency |
|---|---|---|---|---|
| P1-1 | Capacity and SQLite ceiling | **OPEN** | Approved representative load profile with p50/p95/p99, 5xx/lock rate, LLM/vision separation, disk growth, backup duration and an explicit SQLite-versus-PostgreSQL/Redis/queue decision | Operations; Docker/load environment required |
| P1-2 | Payment sandbox certification | **PARTIAL** | Paddle sandbox logs for order creation, server-owned SKU/amount, signed webhook, duplicate/out-of-order replay, entitlement grant, cancellation, failure, refund, restore and reconciliation | Billing/Operations; provider sandbox access |
| P1-3 | Support readiness | **OPEN** | FAQ, response templates, deletion/privacy/payment/safety escalation paths, named support owner and SLA report | Product/Support |
| P1-4 | Privacy-safe analytics and funnel | **OPEN** | Event dictionary implementation from landing → age gate → onboarding → first value → retention, D1/D7 cohorts, cost and conversion; no raw chat/diary/memory/palm text or hidden PII | Data/Product/Privacy |
| P1-5 | Accessibility and visual device acceptance | **PARTIAL** | Touch target, keyboard/focus, screen reader, contrast/WCAG AA where applicable, reduced motion, Telegram safe area, small viewport and long-localized-content review with fresh screenshots | Product/QA; device/browser access |
| P1-6 | Controlled beta evidence | **OPEN** | Two invite-only beta waves with capped traffic, feature flags, release owner, stop conditions, SLO/trust/support/cost thresholds and no critical incidents | Product/Operations; depends on P0 closure |
| P1-7 | Rollout and rollback | **OPEN** | Versioned release, backup confirmation, canary, feature flags, rollback command, migration rehearsal and 72-hour monitoring rota | Operations; depends on P0/P1 evidence |

## Product and domain follow-up tasks

| Area | Current status | Remaining work |
|---|---|---|
| Memory value | **PARTIAL** | Demonstrate privacy-safe before/after relevance, opt-in comprehension, deletion across primary/cache/index/summary and cross-user isolation in a controlled cohort |
| Full E2E journey | **PARTIAL** | Execute the mandatory real Telegram path through share, PDF, paywall sandbox, duplicate webhook, restore, logout/re-login and account deletion |
| Domain source registry | **PARTIAL** | Expand `AGENT_DOMAIN_SOURCES.md` with canonical school, exact settings, primary sources, licensing, fixture IDs, tolerances and verification dates for each tool |
| PDF regression | **PASS locally / follow-up** | Add malicious markup, long unbroken text, long names, font fallback, repeated-generation and fresh print/device snapshot cases |
| Competitive analysis | **PARTIAL** | Refresh the full current RU/EN competitor matrix with dated primary URLs, confirmed feature/pricing evidence, unknowns, WONT_DO decisions and OracleAI differentiation |
| Monetization | **PARTIAL / sandbox only** | Create a versioned server-owned price book and reviewed unit economics using verified tax/fee/settlement inputs; do not publish or enable live prices without owner sign-off |
| Dubai/UAE GTM | **BLOCKED** | Complete legal/payment/privacy feasibility, dated audience research, interviews/paid-intent tests, AED offer economics and go/no-go approval |
| Runtime line audit | **PARTIAL** | Continue high-risk file-by-file review; current cycle directly audited scheduler operations but does not claim every legacy file was reviewed |

## What is not a blocker anymore

The following items have local evidence and should not be reopened as launch blockers unless the implementation changes: the 469-test regression suite, Ruff, Python compileall, Mini App/Admin JavaScript syntax, design contract, deterministic domain evaluation (54 cases), skill library validation (4 agents/139 skills), routing benchmarks, structured natal evidence guards, PDF profile smoke, custom SVG wheel integration, scheduler lease/recovery tests and indexed secret scan.

These are **local PASS results**, not substitutes for production or external approval. Their purpose is to reduce engineering uncertainty before the P0/P1 evidence work begins.

## Recommended execution order

1. Build an isolated staging environment and assign an accountable release owner.
2. Run live LLM/Palm synthetic benchmarks and capture latency, safety, schema and cost evidence.
3. Perform real Telegram device QA in RU/EN and close the highest-severity UX/accessibility defects.
4. Establish encrypted off-site backups, restore rehearsal, alert routing and incident ownership.
5. Certify payment sandbox flows and implement privacy-safe funnel/cost analytics.
6. Run capacity/load testing and decide whether SQLite remains within the controlled-beta ceiling.
7. Obtain legal/privacy approval for the intended country scope, then run two controlled beta waves.
8. Close rollout/rollback evidence and make a documented go/no-go decision; until then, public launch remains blocked.

## References

[1]: [Master requirements status](MASTER_REQUIREMENTS_STATUS_2026-08-25.md)  
[2]: [Launch governance](../LAUNCH_GOVERNANCE.md)  
[3]: [Traceability matrix](../TRACEABILITY_MATRIX.md)  
[4]: [Executive completion audit](MASTER_COMPLETION_AUDIT_2026-08-25.md)
