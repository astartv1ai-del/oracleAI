> STATUS: HISTORICAL
> SUPERSEDED BY: `../README.md and ../RELEASE/CURRENT_STATUS.md`
> This dated evidence is retained for audit context; it is not a current source of truth.

# OracleAI — documentation final review

**Review date:** 2026-08-27
**Repository:** `astartv1ai-del/oracleAI`
**Branch:** `master`
**Starting commit:** `68e3945`
**Verdict:** **BLOCKED** for public launch; documentation and repository hygiene work is complete for this audit scope.

## Documentation

The repository now has one map in [`../README.md`](../README.md), one current release status in [`CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md), and one unresolved backlog in [`TASKS.md`](../RELEASE/TASKS.md). The root README is a short quick-start and boundary document; long explanations remain under `docs/`.

| Measure | Before | After | Notes |
|---|---:|---:|---|
| Markdown files in repository | 240 | 253 | Increase is intentional: canonical AI/operations/domain/feature/release indexes and focused contracts were added. |
| Markdown files under `docs/` | 76 | 91 | Evidence and archive files were moved, not discarded; new category indexes make them discoverable. |
| Current root README | 1 long entry point | 1 concise entry point | Product, stack, quick start, validation, documentation link and launch boundary only. |
| Current backlog/status sources | Several competing locations | 1 backlog + 1 status | `RELEASE/TASKS.md` and `RELEASE/CURRENT_STATUS.md`. |

### Consolidated and reclassified

| Action | Result |
|---|---|
| Current map | Rewrote `docs/README.md` with purpose, when-to-read, source of truth and related code for every canonical area. |
| AI architecture | Added `docs/AI_SYSTEM.md` covering agents, AgentSpec, skills, tools, context, memory, safety, fallback and cost/latency controls. |
| Operations | Added `docs/OPERATIONS.md` linking deployment, Compose, migrations, workers, backup/restore and incident response. |
| Domain | Added `docs/DOMAIN/README.md`, `ASTROLOGY.md`, `TAROT.md` and `PALM.md`; retained shared policy in `DOMAIN/CONTRACTS.md`. |
| Features | Added `docs/FEATURES/README.md`; moved memory, history and billing contracts into that category. |
| Release | Added `docs/RELEASE/CURRENT_STATUS.md`; moved the current backlog, readiness plan, launch governance, P0 plans and changelog into `RELEASE/`. |
| Orientation | Added a predictable Purpose/Source of truth/Scope/Do not change/Key files/Validation block to canonical documents. |
| Map | The active documentation map is maintained in `docs/README.md`; generated file-by-file inventories are not tracked. |

### Deleted and archived

| Action | Files | Reason |
|---|---|---|
| Deleted | the generated palm benchmark JSON output | Generated benchmark output with absolute sandbox paths, no repository references and no role as a reproducible fixture. The benchmark script and palm test fixture remain. |
| Archived | `docs/ARCHIVE/NEXT_STEPS_2026-08-26.md`, `docs/ARCHIVE/UI_PREMIUM_PLAN_RU_2026-08-09.md` | Superseded planning/design material retained for context and explicitly labeled historical. |
| Reclassified as evidence | Root audit/review files, baseline/QA/visual/performance/traceability/P2 reports and dated audit notes | Valuable historical verification was preserved under `docs/EVIDENCE/` with dates and historical labels. |
| Moved into domain/features | `DOMAIN_METHODS.md`, `MEMORY.md`, `UNIFIED_HISTORY.md`, `MONETIZATION_BASELINE.md` | Each now has one clear category home and is linked from the documentation map. |

No Git history was rewritten. Source code, migrations, tests, model notices, legal pages, deployment configuration and production scripts were preserved.

## Repository hygiene

The hygiene gate now scans all Markdown recursively, not only top-level `docs/*.md`, and validates the curated `docs/EVIDENCE/AUDIT/` directory. The repository-native documentation link checker is available through `make docs-check` and runs in CI. `.gitignore` now excludes local generated artifacts such as browser captures, coverage, traces, temporary files, patches, dumps, logs and generated PDFs while preserving tracked source fixtures and input data.

The temporary audit dumps created during inspection were removed before final review. No large generated documentation output remains under `docs/`, and the tracked secret-pattern scan returned no private-key or API-key matches outside the intended example/evidence exclusions.

## Validation

| Check | Result | Limitation |
|---|---|---|
| `APP_ENV=dev DEV_MODE=1 LLM_PROVIDER=off pytest -q` | **PASS**; 100% reached, one skipped test | Local synthetic/dev environment; no production services. |
| `ruff check app scripts tests` | **PASS** | Static analysis only. |
| `python3 -m compileall -q app scripts tests` | **PASS** | Syntax/import compilation only. |
| `node --check miniapp/js/*.js admin/*.js` | **PASS** | Does not replace device/WebView QA. |
| `APP_ENV=dev DEV_MODE=1 LLM_PROVIDER=off python3 -m scripts.selfcheck` | **PASS**; two expected live/config skips | Live LLM, Telegram credentials and production configuration were not supplied. |
| `APP_ENV=dev DEV_MODE=1 LLM_PROVIDER=off python3 -m scripts.release_gate` | **PASS** | Release gate is repository/static evidence, not external certification. |
| `python3 -m scripts.check_p2_quality` | **PASS**; all listed checks true | Manual, staging and provider checks remain open where labeled. |
| `python3 -m scripts.check_repository_hygiene` | **PASS** | Recursive local Markdown/path hygiene. |
| `python3 scripts/check_documentation_links.py` | **PASS** | Repository-native recursive check of repository-relative Markdown targets; external URL availability is not checked. |
| `git diff --check` | **PASS** | Whitespace check only. |
| Secret-pattern scan | **PASS**; no matches | Pattern scan is not a full secret-management audit. |

## Source of truth

| Area | Canonical document | Implementation anchors |
|---|---|---|
| Product | [`../PRODUCT.md`](../PRODUCT.md) | `app/api/`, `app/bot/`, `miniapp/` |
| Architecture | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | `app/`, `miniapp/`, `infra/` |
| AI | [`../AI_SYSTEM.md`](../AI_SYSTEM.md) | `app/core/agents/`, `app/core/skills.py`, `app/core/llm.py` |
| Design | [`../DESIGN_SYSTEM.md`](../DESIGN_SYSTEM.md) | `miniapp/css/`, `miniapp/js/` |
| API | [`../API.md`](../API.md) | `app/api/`, `app/api/contracts/` |
| Security | [`../SECURITY.md`](../SECURITY.md) | `app/api/security.py`, `app/api/deps.py`, `app/core/safety.py` |
| Deployment | [`../DEPLOYMENT.md`](../DEPLOYMENT.md) | `infra/`, `Makefile`, `.env*.example` |
| Operations | [`../OPERATIONS.md`](../OPERATIONS.md) | `infra/`, `scripts/`, `app/tasks/` |
| Testing | [`../TESTING.md`](../TESTING.md) | `tests/`, `scripts/`, CI |
| Release status | [`CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md) | Current code, tests, CI and dated evidence |
| Current tasks | [`TASKS.md`](../RELEASE/TASKS.md) | Release gates, acceptance criteria and blockers |
| Domain | [`../DOMAIN/README.md`](../DOMAIN/README.md) | `app/core/astro.py`, `tarot.py`, `palm.py`, `vedic.py` |
| Features | [`../FEATURES/README.md`](../FEATURES/README.md) | `app/core/`, `app/services/`, `app/repo/`, feature routers |
| Evidence | [`../EVIDENCE/README.md`](../EVIDENCE/README.md) | Dated reports only; not current truth |

## Remaining concerns

The documentation work does not close the product’s external launch gates. Public launch remains blocked by real Telegram signed-`initData` and device/WebView verification, payment sandbox/settlement/refund/reconciliation, live-provider quality and latency, production backup/restore and rollback, legal/privacy approval, licensing confirmation, independent astronomy comparison, and manual device/accessibility review. These are recorded in [`TASKS.md`](../RELEASE/TASKS.md) and separated by environment in [`CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md).

The final verdict for this audit is **BLOCKED**, not because the repository lacks a usable implementation, but because the remaining concerns require external evidence that cannot be honestly manufactured by documentation changes.

## References

[1]: [Documentation map](../README.md) — canonical navigation and source-of-truth mapping.
[2]: [Current status](../RELEASE/CURRENT_STATUS.md) — environment-separated release verdict.
[3]: [Current tasks](../RELEASE/TASKS.md) — acceptance criteria, evidence and blockers.
[4]: [Repository inventory](../README.md) — file-by-file audit inventory.
[5]: [Repository hygiene gate](../../scripts/check_repository_hygiene.py) — recursive local documentation and artifact checks.
