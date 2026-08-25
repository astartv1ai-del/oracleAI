# OracleAI project map

**Generated:** 2026-08-25 from the current checkout.
**Scope:** runtime source, clients, infrastructure, tests, tooling and source-of-truth documentation.

## Runtime topology

The repository contains a Python FastAPI/backend and Telegram bot under `app/`, a vanilla JavaScript/CSS Telegram Mini App under `miniapp/`, static landing/legal pages under `web/`, a small admin surface under `admin/`, and Docker/Caddy deployment material under `infra/`. Deterministic domain calculations and safety/evidence boundaries live in `app/core/`; persistence and migrations live in `app/data/` and `app/repo/`; HTTP contracts live in `app/api/`; Telegram handlers live in `app/bot/`; PDF generation lives in `app/pdfgen/`.

## Critical flows

| Flow | Primary entrypoints | Evidence/checks |
|---|---|---|
| Telegram onboarding and chat | `app/bot/`, `app/core/agents/`, `app/core/agent.py` | `tests/test_bot_fsm.py`, `tests/test_agent_context.py`, `tests/test_safety.py` |
| Mini App authenticated API | `app/api/main.py`, `app/api/routers/`, `miniapp/js/` | `tests/test_api.py`, `tests/test_miniapp_actions.py`, JS syntax gate |
| Natal calculation and chart rendering | `app/core/chart_contract.py`, `app/core/astro.py`, `miniapp/js/04-nativity.js` | `tests/test_chart_contract.py`, `tests/test_natal_sections.py`, `tests/check_nativity_svg.js` |
| Structured LLM interpretation | `app/core/chart_interpretation.py`, `app/core/interpretation.py`, `app/core/llm.py` | `tests/test_chart_interpretation.py`, `tests/test_interpretation_guardrails.py`, `tests/test_llm.py` |
| Memory and diary | `app/core/memory.py`, `app/repo/`, `app/api/routers/`, `miniapp/js/08-widgets.js` | `tests/test_diary.py`, `tests/test_agent_context.py`, `tests/test_security_regressions.py` |
| Tarot/Lenormand/palm | `app/core/tarot.py`, `app/agents/lenormand/`, `app/core/palm.py`, `miniapp/js/09-tarot.js`, `miniapp/js/13-palm.js` | domain/routing/palm test suite and benchmark scripts |
| PDF/report | `app/pdfgen/`, `scripts/gen_pdf.py`, `scripts/qa_pdf_profiles.py` | `tests/test_pdfgen.py`, `docs/audit/pdf_samples_v2/`, PDF profile QA |
| Billing and entitlements | `app/services/billing.py`, `app/api/routers/payments.py`, `tests/test_billing.py` | sandbox/fixture tests only; live payment remains gated |
| Scheduled/background work | `app/services/scheduler.py`, `app/bot/`, `scripts/ops_alerts.py` | `tests/test_scheduler.py`, `tests/test_broadcast.py`; production scheduler evidence remains open |
| Backup/restore | `scripts/backup_db.sh`, `scripts/restore_db.sh` | disposable plaintext/encrypted restore drill; production off-site evidence remains open |

## External boundaries

Telegram authentication and bot API, LLM provider chain, geocoding/timezone services, payment providers, Sentry/observability, and deployment infrastructure are external boundaries. Local tests use fixtures/mocks unless explicitly marked otherwise; live provider/device/payment/production-host evidence is not inferred from unit tests.

## Inventory counts

- **backend:** 274 files
- **documentation:** 188 files
- **frontend:** 153 files
- **infrastructure:** 3 files
- **repository:** 54 files
- **test:** 44 files
- **tooling:** 41 files

## Source-of-truth documents

`docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DESIGN_SYSTEM.md`, `docs/SECURITY.md`, `docs/LAUNCH_GOVERNANCE.md`, `docs/DEPLOYMENT.md`, `docs/LLM_EVALUATION.md`, and `docs/MONETIZATION_BASELINE.md` define current contracts. `docs/FILE_AUDIT.csv` is the generated per-file inventory; regenerate it with `python scripts/generate_project_audit.py` after structural changes.
