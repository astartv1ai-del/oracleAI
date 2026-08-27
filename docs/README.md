# OracleAI — documentation map

## Document orientation

| Field | Definition |
|---|---|
| **Purpose** | Provide one navigable map of current product, engineering, operations, domain and release documentation. |
| **Source of truth** | This map points to the canonical document for each subsystem; implementation truth remains in the referenced code and tests. |
| **Scope** | Current contracts, operating procedures, feature/domain references, dated evidence and historical archive. |
| **Do not change** | Do not create a second backlog, audit, status or architecture source of truth. Do not promote evidence or research notes into current behavior without code validation. |
| **Key files** | `README.md`, `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/AI_SYSTEM.md`, `docs/RELEASE/CURRENT_STATUS.md`. |
| **Validation** | Follow [`CONTRIBUTING.md`](CONTRIBUTING.md), run the commands in [`TESTING.md`](TESTING.md), and check links before release. |

## Start here

| Topic | Canonical document | When to read it | Related code |
|---|---|---|---|
| Product | [`PRODUCT.md`](PRODUCT.md) | Understand the audience, promise, boundaries and enabled surfaces. | `miniapp/`, `app/bot/`, `app/api/routers/` |
| Architecture | [`ARCHITECTURE.md`](ARCHITECTURE.md) | Change data flow, modules, storage, agents or client loading order. | `app/`, `miniapp/`, `infra/` |
| AI system | [`AI_SYSTEM.md`](AI_SYSTEM.md) | Change agents, skills, tools, context, memory, safety or provider behavior. | `app/core/agents/`, `app/core/skills.py`, `app/core/llm.py` |
| Design | [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) | Change screens, tokens, components, motion, localization or accessibility. | `miniapp/css/`, `miniapp/js/`, `miniapp/index.html` |
| API | [`API.md`](API.md) | Add or change an HTTP route, request, response, auth or error contract. | `app/api/`, `app/services/` |
| Security | [`SECURITY.md`](SECURITY.md) | Change identity, owner scope, consent, privacy, uploads, payments or safety. | `app/api/deps.py`, `app/api/security.py`, `app/core/safety.py` |
| Deployment | [`DEPLOYMENT.md`](DEPLOYMENT.md) | Build, configure, migrate, deploy or roll back the stack. | `Makefile`, `infra/`, `.env*.example` |
| Operations | [`OPERATIONS.md`](OPERATIONS.md) | Operate services, workers, backups, recovery or incidents. | `infra/docker-compose.yml`, `scripts/`, `app/tasks/` |
| Testing | [`TESTING.md`](TESTING.md) | Select checks for a change and interpret local versus external evidence. | `tests/`, `scripts/`, `.github/workflows/ci.yml` |
| Contributing | [`CONTRIBUTING.md`](CONTRIBUTING.md) | Prepare a branch, review a diff and complete a pull request. | `.github/`, `Makefile` |

## Domain and feature contracts

| Area | Canonical document | Related code |
|---|---|---|
| Domain index | [`DOMAIN/README.md`](DOMAIN/README.md) | `app/core/` |
| Shared calculation/evidence policy | [`DOMAIN/CONTRACTS.md`](DOMAIN/CONTRACTS.md) | `app/core/astro.py`, `chart_contract.py`, `tarot.py`, `palm.py` |
| Astrology and chart products | [`DOMAIN/ASTROLOGY.md`](DOMAIN/ASTROLOGY.md) and [`CHART_PRODUCT_CONTRACTS.md`](CHART_PRODUCT_CONTRACTS.md) | `app/core/astro.py`, `vedic.py`, `chart_products.py` |
| Tarot and card reflection | [`DOMAIN/TAROT.md`](DOMAIN/TAROT.md) | `app/core/tarot.py`, `app/api/routers/tarot.py` |
| Palm and visual evidence | [`DOMAIN/PALM.md`](DOMAIN/PALM.md) | `app/core/palm*.py`, `app/api/routers/placements.py` |
| Memory | [`FEATURES/MEMORY.md`](FEATURES/MEMORY.md) | `app/core/memory.py`, profile routes, repositories |
| Unified history | [`FEATURES/HISTORY.md`](FEATURES/HISTORY.md) | `app/api/routers/history.py`, `app/repo/readings.py` |
| Billing and monetization | [`FEATURES/BILLING.md`](FEATURES/BILLING.md) | `app/services/billing.py`, shop/webhook routes |

## Release and evidence

| Type | Canonical document | Purpose |
|---|---|---|
| Current status | [`RELEASE/CURRENT_STATUS.md`](RELEASE/CURRENT_STATUS.md) | The only current go/no-go statement, separated by LOCAL, STAGING, PRODUCTION and EXTERNAL. |
| Current backlog | [`RELEASE/TASKS.md`](RELEASE/TASKS.md) | The only authoritative list of unresolved work, acceptance criteria, evidence and blockers. |
| Production readiness | [`RELEASE/PRODUCTION_READINESS.md`](RELEASE/PRODUCTION_READINESS.md) | Release process and readiness gates. |
| Launch governance | [`RELEASE/LAUNCH_GOVERNANCE.md`](RELEASE/LAUNCH_GOVERNANCE.md) | Owners, gates, SLO placeholders and go/no-go rules. |
| P0 execution | [`RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md`](RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md) | Owner-led procedures for the four public-launch blockers. |
| Changelog | [`RELEASE/CHANGELOG.md`](RELEASE/CHANGELOG.md) | User- and engineering-visible release history. |
| Documentation final review | [`RELEASE/DOCUMENTATION_FINAL_REVIEW.md`](RELEASE/DOCUMENTATION_FINAL_REVIEW.md) | Audit result, before/after shape, validation and remaining concerns. |
| Final QA matrix | [`RELEASE/FINAL_QA_MATRIX.md`](RELEASE/FINAL_QA_MATRIX.md) | Functional, browser and red-team checks with reproducible evidence. |
| Final release certification | [`RELEASE/FINAL_RELEASE_CERTIFICATION.md`](RELEASE/FINAL_RELEASE_CERTIFICATION.md) | Final build, QA, security scorecard, blockers and verdict. |
| Dated evidence | [`EVIDENCE/`](EVIDENCE/) | Historical audits, QA baselines, traceability and benchmark records. Evidence is not current truth unless explicitly revalidated. |
| Archive | [`ARCHIVE/`](ARCHIVE/) | Superseded plans and design proposals retained for context, each labeled historical. |

## Supporting references

These documents provide focused implementation, research or operational context without competing with the canonical contracts above.

| Area | Reference |
|---|---|
| Observability | [`OBSERVABILITY.md`](OBSERVABILITY.md) |
| AI evaluation and agent audit | [`LLM_EVALUATION.md`](LLM_EVALUATION.md), [`LLM_AGENT_TECHNICAL_AUDIT.md`](LLM_AGENT_TECHNICAL_AUDIT.md), [`AGENT_ARCHITECTURE.md`](AGENT_ARCHITECTURE.md), [`AGENT_QUALITY_STANDARD.md`](AGENT_QUALITY_STANDARD.md) |
| AI onboarding and skills | [`AI_ONBOARDING_GAUNTLET.md`](AI_ONBOARDING_GAUNTLET.md), [`AGENTS.md`](AGENTS.md), [`AGENT_SKILL_LIBRARY.md`](AGENT_SKILL_LIBRARY.md) |
| Chart and product boundaries | [`CHART_ENGINE_DECISION.md`](CHART_ENGINE_DECISION.md), [`CHART_ENGINE_LICENSING.md`](CHART_ENGINE_LICENSING.md), [`CHART_TYPE_CAPABILITIES.md`](CHART_TYPE_CAPABILITIES.md), [`COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md`](COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md) |
| Astronomy and visual domain research | [`ASTRONOMY_REFERENCE_QA.md`](ASTRONOMY_REFERENCE_QA.md), [`PALM_ENGINE_RESEARCH.md`](PALM_ENGINE_RESEARCH.md), [`CHIROMANT_AVATAR_BRIEF.md`](CHIROMANT_AVATAR_BRIEF.md) |
| API, memory and localization | [`API_RESILIENCE_MATRIX.md`](API_RESILIENCE_MATRIX.md), [`MEMORY_EVALUATION.md`](MEMORY_EVALUATION.md), [`LOCALIZATION_GLOSSARY.md`](LOCALIZATION_GLOSSARY.md) |
| Analytics and payments | [`ANALYTICS_EVENT_DICTIONARY.md`](ANALYTICS_EVENT_DICTIONARY.md), [`PAYMENTS_UX_AND_INTEGRATION.md`](PAYMENTS_UX_AND_INTEGRATION.md), [`PAYMENT_MONITORING.md`](PAYMENT_MONITORING.md) |
| PDF, backup and visual QA | [`PDF_SYSTEM.md`](PDF_SYSTEM.md), [`PDF_TEMPLATE_CATALOG.md`](PDF_TEMPLATE_CATALOG.md), [`BACKUP_RESTORE_DRILL.md`](BACKUP_RESTORE_DRILL.md), [`VISUAL_QA.md`](VISUAL_QA.md) |
| Scale and competition | [`SCALE_AND_MIGRATION.md`](SCALE_AND_MIGRATION.md), [`COMPETITOR_MATRIX.md`](COMPETITOR_MATRIX.md) |
| Legal and model provenance | [`LEGAL_REVIEW.md`](LEGAL_REVIEW.md), [`models/THIRD_PARTY_NOTICES.md`](../models/THIRD_PARTY_NOTICES.md) |

## Docker-first launch

For the full stack, use Docker Engine with Compose v2 from the repository root:

```bash
cp .env.example .env
# Fill BOT_TOKEN/ADMIN_ID and an LLM provider key when required.
make up
make ps
make selfcheck
```

Compose starts PostgreSQL + pgvector, Redis, migrations, API, Telegram bot, Celery worker/Beat and Caddy. The application image also contains the Mini App, admin, landing, astrology engine, palm assets and LLM runtime. Development ports are `8080` (HTTP) and `8443` (HTTPS). The observability contour includes Grafana, Loki, Prometheus, Alloy, cAdvisor and node-exporter; Grafana is bound to `127.0.0.1:3000` by default. See [`OBSERVABILITY.md`](OBSERVABILITY.md) and [`DEPLOYMENT.md`](DEPLOYMENT.md).

For the optional local OpenAI-compatible LLM, set `CUSTOM_LLM_BASE_URL=http://ollama:11434/v1`, `CUSTOM_LLM_MODEL` and `CUSTOM_LLM_MODEL_LITE`, then run `make up-local-llm`.

## Local development

For a manual run without Docker, use Python 3.11+ and keep real Telegram authorization checks limited to a controlled environment. Install dependencies and create `.env` once:

```bash
cd /path/to/oracleAI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

A local development mode is available for interface inspection. It accepts `dev_user` and must never be exposed on a public address.

```bash
APP_ENV=dev DEV_MODE=1 uvicorn app.api.main:app --host 127.0.0.1 --port 8080
# http://127.0.0.1:8080/?dev_user=10001
```

Production uses `DEV_MODE=0`, a real HTTPS `WEBAPP_URL` and server validation of Telegram `initData`. The complete process is in [`DEPLOYMENT.md`](DEPLOYMENT.md).

## Working cycle

| Stage | Minimum action | Verification artifact |
|---|---|---|
| Product change | Reconcile the scenario with PRODUCT and DESIGN_SYSTEM. | Updated copy, states and analytics event when needed. |
| Data change | Update `schema.py` and migrations for existing databases. | New migration run and regression test. |
| API change | Update the router and client call. | API.md review and negative-path tests. |
| UI change | Use tokens, CSS cascade and delegated events. | Mobile viewport and `prefers-reduced-motion` check. |
| Before release | Run syntax, tests, selfcheck and diff review. | Changelog entry and green CI/local QA. |

## Operating rules

Current behavior must be established from code, tests and configuration first. A document change that alters a contract must update the corresponding canonical page in the same pull request. A local or synthetic check must name its environment and limitation; it cannot close a staging, production, legal, payment or provider gate.

Before opening a pull request, validate relative links, stale path references, documented commands and generated artifacts. Keep raw screenshots, logs, local databases, generated reports and secrets outside the tracked source tree unless a reproducible fixture or legal notice requires them.

## References

[1]: [Repository README](../README.md) — repository-level quick start and boundary.
[2]: [Current status](RELEASE/CURRENT_STATUS.md) — current release verdict.
[3]: [Current tasks](RELEASE/TASKS.md) — current backlog.
[4]: [Repository inventory](REPOSITORY_INVENTORY.md) — file-by-file inventory.
[5]: [Documentation link checker](../scripts/check_documentation_links.py) — repository-relative Markdown checker.
