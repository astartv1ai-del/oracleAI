# OracleAI traceability matrix

**Baseline date:** 2026-08-25
**Baseline commit:** `c1a296c4fe5f25fe3a99b7d2fff2ab246b2e1681`
**Verification policy:** a local deterministic test is evidence for code behavior only; it is not evidence of live providers, real devices, production infrastructure, legal approval, or payments.

| ID | Area | Acceptance claim | Evidence | Status | Next proof / owner |
|---|---|---|---|---|---|
| G0-01 | Repository | Runtime map and file inventory exist and are reproducible | `docs/PROJECT_MAP.md`, `docs/FILE_AUDIT.csv`, `scripts/generate_project_audit.py` | PASS | Regenerate after structural changes / Engineering |
| G0-02 | Baseline | Current lint, tests, syntax, selfcheck and release gate are recorded | `docs/audit/baseline_master_2026-08-25.txt` | PASS | Repeat on final commit / QA |
| G0-03 | Configuration | Production mode fails closed and required production settings are documented | `docs/SECURITY.md`, `docs/DEPLOYMENT.md`, `scripts/selfcheck.py` | UNVERIFIED | Production-like staging rehearsal / Operations |
| G0-04 | Staging | Bot, DB, domain, LLM and payment credentials are isolated from production | `docs/LAUNCH_GOVERNANCE.md` Gate P0 | OPEN | Staging environment evidence / Operations |
| G0-05 | Legal/privacy | Intended country scope has external legal/privacy review | `docs/LEGAL_REVIEW.md`, `web/privacy*.html`, `web/terms*.html` | EXTERNAL | Qualified counsel sign-off / Product-Legal |
| G0-06 | Safety | Deterministic safety, crisis and evidence-boundary tests pass | `tests/test_safety.py`, `tests/test_interpretation_guardrails.py`, `docs/PRODUCTION_READINESS_EVIDENCE.md` | PASS (local) | Live/provider red-team and release sign-off / AI-Safety |
| G0-07 | Live LLM | Live provider success, strict JSON, latency and fallback are proven | `scripts/live_llm_probe.py`, selfcheck skip | OPEN | Staging provider benchmark with synthetic fixtures / AI-Operations |
| G0-08 | Palm | Vision schema, quality fallback and p95 are proven on an approved benchmark | `tests/test_palm_*.py`, `docs/CHIROMANT_QA_FINDINGS.md` | OPEN | Provider/device benchmark / AI-Product |
| G0-09 | Backup/restore | Encrypted backup and isolated restore are executable | `scripts/backup_db.sh`, `scripts/restore_db.sh`, disposable plaintext/encrypted drill on 2026-08-25 | PASS (fixture) | Off-site production copy, checksum and scheduled restore drill / Operations |
| G0-10 | Monitoring | Alerts and dashboards have been tested against real signals | `scripts/ops_alerts.py`, `tests/test_stage0_operations.py`, `docs/audit/risk_audit_2026-08-25.txt` | PARTIAL | Scheduler lease/status and local alert parsing are verified; production routing, dashboards and test alerts remain open / Operations |
| G1-01 | Domain calculations | Natal contract and golden cases are deterministic and cross-checked | `app/core/chart_contract.py`, `tests/test_chart_contract.py`, `scripts/benchmark_natal_engines.py` | PASS (local) | Add/retain edge fixtures and release artifact / Domain-QA |
| G1-02 | Structured interpretation | Schema validation and fallback prevent fabricated chart fields | `app/core/chart_interpretation.py`, `tests/test_chart_interpretation.py` | PASS (local) | Live provider evaluation / AI-Safety |
| G1-03 | Routing | Agent/skill routing benchmarks pass | `scripts/benchmark_agent_routing.py`, `scripts/benchmark_skill_routing.py`, existing release artifacts | PASS (local) | Expand ambiguous/adversarial set / AI-QA |
| G1-04 | Memory | Opt-in, deletion, isolation and no fabricated context are tested | `tests/test_agent_context.py`, `tests/test_diary.py`, `tests/test_security_regressions.py` | PASS (local) | Re-run cross-user and stale-summary fixture / Privacy-QA |
| G1-05 | Payments | Sandbox billing, idempotency, refund and restore are proven end-to-end | `tests/test_billing.py`, `docs/MONETIZATION_BASELINE.md` | PARTIAL | Add provider sandbox log/reconciliation fixture / Billing-Operations |
| G1-06 | PDF | RU/EN, unknown time and dense chart profiles render without corruption/overflow | `scripts/qa_pdf_profiles.py`, `docs/audit/pdf_samples_v2/`, `tests/test_pdfgen.py` | PASS (local) | Extend long-name, malicious-markup and font checks / PDF-QA |
| G1-07 | Visual UX | Mobile, desktop, keyboard, reduced-motion and error-state review is complete | `docs/DESIGN_SYSTEM.md`, `docs/audit/` | PARTIAL | Fresh browser/device matrix / Product-QA |
| G1-08 | Scheduler | Background jobs are idempotent, consent-aware and operationally monitored | `app/services/scheduler.py`, `app/data/schema.py`, `tests/test_scheduler.py`, `scripts/ops_alerts.py`, `tests/test_stage0_operations.py` | PARTIAL → improved | Single-owner lease, stale recovery, failure accounting and privacy-safe status are verified locally; missed-run policy, dead-letter operations and production alert routing remain open / Operations |
| G1-09 | Share/privacy | Public artifacts exclude private birth/memory/chat fields and support revoke/expiry | share/API tests and `docs/SECURITY.md` | UNVERIFIED | Fresh share payload/expiry test / Privacy-QA |
| G1-10 | Export/delete | Export and account deletion cover primary and derived stores | API/data tests and `docs/SECURITY.md` | PARTIAL | End-to-end fixture with memory/index/cache audit / Privacy-QA |
| G1-11 | Infrastructure | Docker, health, migrations and rollback are reproducible | `infra/`, `scripts/healthcheck.py`, `tests/test_migrations.py` | PARTIAL | Docker build/config and fresh+upgrade drill / Operations |
| G1-12 | Capacity | Representative load and SQLite ceiling are measured | `load/`, `docs/SCALE_AND_MIGRATION.md` | OPEN | Run approved load profile and capture p50/p95/p99 / Operations |
| GTM-01 | Competitor research | Current public competitor matrix has dated primary-source evidence | `docs/COMPETITOR_STEER_COMPARISON.md` | PARTIAL | Refresh required competitor set and dates / Product-Growth |
| GTM-02 | Monetization | Price book and unit economics are modelled without enabling production pricing | `docs/MONETIZATION_BASELINE.md`, `docs/MONETIZATION_UNIT_ECONOMICS.md` | PARTIAL | Versioned scenario model and sandbox offer tests / Product-Finance |
| GTM-03 | Dubai/UAE | Legal, payment and market go/no-go is evidenced | No complete current pack | BLOCKED | External legal/payment research and owner approval / Product-Legal |

## Release interpretation

The repository is **code/CI-ready for continued controlled-beta work**, but it is not approved for public launch. The highest-priority unresolved gates are staging isolation, live provider/palm evidence, legal/privacy sign-off, off-site backup/restore operations, monitoring/incident ownership, payment sandbox reconciliation, device QA, and capacity testing.
