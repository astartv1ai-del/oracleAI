# OracleAI Documentation Cleanup Report

**Дата:** 2026-08-27
**Ветка:** `p0-004-infrastructure`
**Объект:** документационная и repository-hygiene очистка OracleAI по плану cleanup.

## Итог

Документация приведена к принципу **code and tests are authoritative**. Текущий слой отделён от dated evidence и superseded archive; навигация указывает одну canonical source of truth для каждого major topic; stale paths и misleading claims исправлены; временный inventory не оставлен в репозитории.

> **Важно:** `SHIP IT` ниже относится к результату документационной очистки. Это не означает, что OracleAI сертифицирован для public production launch. Актуальный product-release verdict по-прежнему **BLOCKED** из-за внешних Telegram, payments, live AI, staging infrastructure, legal/licensing и independent-domain gates.

## Scope и classification

До очистки был собран временный inventory tracked text corpus. Он использовался для классификации, но `docs/DOCS_CLEANUP_TEMP.md` удалён до финального состояния. После очистки в tracked corpus осталось **272 текстовых документа/контракта**:

| Класс | Состав | Количество | Решение |
|---|---|---:|---|
| **KEEP — current docs** | Active `docs/` pages, including the navigation map, canonical product/architecture/API/security/operations/testing/release pages and focused feature/domain references | 75 | Оставлены и проверены как current/supporting documentation. |
| **KEEP — runtime contracts** | `app/agents/**` system, skill, domain, knowledge and evaluation documents | 157 | Оставлены обязательно: эти файлы загружаются runtime/evaluator и не являются documentation clutter. |
| **KEEP — other tracked text** | Root `README.md`, `models/THIRD_PARTY_NOTICES.md`, `load/README.md`, prompt packs, dependency/fixture/robots text | 12 | Оставлены как source, operational reference, legal notice или fixture contract. |
| **ARCHIVE/EVIDENCE** | Dated `docs/EVIDENCE/**` records and superseded `docs/ARCHIVE/**` material | 28 | Оставлены только с явными `STATUS: HISTORICAL` и `SUPERSEDED BY:` headers; не являются current truth. |
| **DELETE** | Generated `docs/REPOSITORY_INVENTORY.md`; transient cleanup inventory | Не входят в итоговый corpus | Удалены как generated/audit-only noise; transient inventory не закоммичен. |

Exact-byte duplicate search не нашёл duplicate groups. Поэтому контент не удалялся только из-за похожих заголовков: сохранены focused references с уникальной implementation или product value, а конкурирующие status/backlog/audit entries перенаправлены в canonical map.

## Removed

| Removed item | Причина |
|---|---|
| `docs/REPOSITORY_INVENTORY.md` | Сгенерированный 1031-line inventory, не являвшийся source of truth и дублировавший navigation/git tree. |
| `docs/DOCS_CLEANUP_TEMP.md` | Временный classification inventory. Удалён до commit, как требовал cleanup plan. |

## Merged and consolidated

Физически новые competing documents не создавались. Вместо этого existing knowledge consolidated through canonical routing:

| Former competing material | Canonical destination |
|---|---|
| LLM technical audit and AI final review | [`AI_SYSTEM.md`](AI_SYSTEM.md), [`AGENT_ARCHITECTURE.md`](AGENT_ARCHITECTURE.md), [`AGENT_QUALITY_STANDARD.md`](AGENT_QUALITY_STANDARD.md) and runtime `app/agents/**` contracts. |
| Astronomy reference QA | [`DOMAIN/ACCURACY_MATRIX.md`](DOMAIN/ACCURACY_MATRIX.md), with the implementation boundary retained in [`DOMAIN/ASTROLOGY.md`](DOMAIN/ASTROLOGY.md). |
| P0 infrastructure audit and local smoke evidence | [`RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md`](RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md), [`OPERATIONS.md`](OPERATIONS.md), [`RELEASE/CURRENT_STATUS.md`](RELEASE/CURRENT_STATUS.md) and dated EVIDENCE. |
| Performance/QA/release review conclusions | [`TESTING.md`](TESTING.md), [`RELEASE/PRODUCTION_READINESS.md`](RELEASE/PRODUCTION_READINESS.md), [`RELEASE/TASKS.md`](RELEASE/TASKS.md) and dated EVIDENCE. |
| Multiple navigation and status pointers | [`README.md`](README.md), root [`../README.md`](../README.md), [`RELEASE/CURRENT_STATUS.md`](RELEASE/CURRENT_STATUS.md) and [`RELEASE/TASKS.md`](RELEASE/TASKS.md). |

## Archived

The following active-looking audit/review files were moved into `docs/EVIDENCE/` and renamed with an explicit date:

| Archived file | Superseded by |
|---|---|
| `EVIDENCE/AI_SYSTEM_FINAL_REVIEW_2026-08-27.md` | `AI_SYSTEM.md` and agent quality standards. |
| `EVIDENCE/ASTRONOMY_REFERENCE_QA_2026-08-27.md` | `DOMAIN/ACCURACY_MATRIX.md`. |
| `EVIDENCE/AUTONOMOUS_GAUNTLET_2026-08-27.md` | `AI_ONBOARDING_GAUNTLET.md` and runtime contracts. |
| `EVIDENCE/DOCUMENTATION_FINAL_REVIEW_2026-08-27.md` | `README.md`, `docs/README.md` and this cleanup report. |
| `EVIDENCE/LLM_AGENT_TECHNICAL_AUDIT_2026-08-27.md` | `AI_SYSTEM.md`, `AGENT_ARCHITECTURE.md` and runtime contracts. |
| `EVIDENCE/LOCAL_ADMIN_SMOKE_2026-08-27.md` | `TESTING.md`, `SECURITY.md` and release evidence requirements. |
| `EVIDENCE/P004_INFRASTRUCTURE_AUDIT_2026-08-27.md` | `RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md` and `OPERATIONS.md`. |
| `EVIDENCE/PERFORMANCE_CI_REPORT_2026-08-27.md` | `TESTING.md` and `RELEASE/PRODUCTION_READINESS.md`. |

All dated evidence and archive documents now carry the historical status convention. Their links were repaired after relocation, and their local/synthetic results are not promoted to staging or production certification.

## Updated

The cleanup corrected navigation and truthfulness without changing application behavior:

| Area | Changes |
|---|---|
| Documentation map | `docs/README.md` now has one topic map, one current status, one current backlog, clear domain/feature routing and explicit evidence/archive policy. |
| Release truth | `RELEASE/CURRENT_STATUS.md` now identifies the checked-out candidate, separates LOCAL/STAGING/PRODUCTION/EXTERNAL and keeps the public-launch verdict **BLOCKED** until external gates are evidenced. `RELEASE/CHANGELOG.md` and `RELEASE/TASKS.md` were updated to point at canonical documents. |
| AI/domain references | Renamed astronomy and AI audit references now point to `DOMAIN/ACCURACY_MATRIX.md` and `AI_SYSTEM.md`; external evidence explicitly keeps the shared Swiss Ephemeris limitation. |
| Code/path accuracy | Removed references to nonexistent `miniapp/js/04-nativity.js`, corrected `miniapp/js/10-profile.js` to the existing profile surface, corrected memory path references to `app/core/memory.py`, corrected load-test references to `app.api.main:app` and `docs/RELEASE/PRODUCTION_READINESS.md`, and clarified palm benchmark output as generated stdout/artifact evidence rather than a tracked JSON file. |
| Evidence links | Fixed relative links in moved evidence and release docs, including references formerly pointing at deleted inventory or old active audit paths. |
| Load scripts | Updated `load/locustfile.py` and `load/simulate.py` docstrings to the current production-readiness path. |
| Hygiene | Removed trailing whitespace and verified the repository-native hygiene checker. No runtime agent contract files were deleted. |

## Canonical sources of truth

| Topic | Canonical current source | Authority boundary |
|---|---|---|
| Repository entry point | [`../README.md`](../README.md) | Short start, stack, boundaries and validation commands. |
| Documentation navigation | [`README.md`](README.md) | One map; it does not override code or tests. |
| Product and UX | [`PRODUCT.md`](PRODUCT.md), [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) | Product promise and UI contract; implementation remains in `miniapp/`. |
| Architecture and API | [`ARCHITECTURE.md`](ARCHITECTURE.md), [`API.md`](API.md) | Current module/data-flow and HTTP contracts. |
| AI and agents | [`AI_SYSTEM.md`](AI_SYSTEM.md), [`AGENT_ARCHITECTURE.md`](AGENT_ARCHITECTURE.md), runtime `app/agents/**` | Runtime code/contracts override explanatory docs. |
| Security and privacy | [`SECURITY.md`](SECURITY.md), [`LEGAL_REVIEW.md`](LEGAL_REVIEW.md) | Security implementation is code; legal approval remains external. |
| Domain | [`DOMAIN/README.md`](DOMAIN/README.md), [`DOMAIN/CONTRACTS.md`](DOMAIN/CONTRACTS.md), [`DOMAIN/ACCURACY_MATRIX.md`](DOMAIN/ACCURACY_MATRIX.md) | Deterministic calculations and evidence boundaries. |
| Feature contracts | [`FEATURES/MEMORY.md`](FEATURES/MEMORY.md), [`FEATURES/HISTORY.md`](FEATURES/HISTORY.md), [`FEATURES/BILLING.md`](FEATURES/BILLING.md) | Feature behavior and limits tied to current code. |
| Deployment/operations | [`DEPLOYMENT.md`](DEPLOYMENT.md), [`OPERATIONS.md`](OPERATIONS.md) | Current runbooks; infrastructure evidence remains environment-specific. |
| Testing | [`TESTING.md`](TESTING.md) | Commands and interpretation of local versus external evidence. |
| Release status | [`RELEASE/CURRENT_STATUS.md`](RELEASE/CURRENT_STATUS.md) | The only current go/no-go statement. |
| Release backlog | [`RELEASE/TASKS.md`](RELEASE/TASKS.md) | The only authoritative unresolved-work list. |
| P0 execution | [`RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md`](RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md) | Owner-led procedures and evidence requirements. |
| Historical records | [`EVIDENCE/README.md`](EVIDENCE/README.md), [`ARCHIVE/README.md`](ARCHIVE/README.md) | Historical context only, never implicit current truth. |

## Second-pass and fresh-context critic

A fresh-context review was performed using only the root README, `docs/README.md` and the final docs tree. It found the following:

1. The root README is short, current and correctly distinguishes local development from public launch. No expansion was needed.
2. The documentation map clearly separates current pages, supporting references, dated evidence and archive. It explicitly states that code/tests override documentation and that no second backlog/status source may be created.
3. The only current release status and backlog are `RELEASE/CURRENT_STATUS.md` and `RELEASE/TASKS.md`; the dated audit/review files no longer sit in the active navigation layer.
4. Focused supporting pages such as monetization research, PDF catalog, observability sources and visual QA were retained because they contain unique context, but the map labels them supporting references rather than canonical behavior. This avoids destructive over-deletion while preventing them from competing with current contracts.
5. The final tree contains runtime agent contracts under `app/agents/**`; these were deliberately retained because deleting them would alter runtime/evaluation behavior, not merely reduce documentation count.

## Validation

| Check | Result | Notes |
|---|---|---|
| Markdown links | `DOCUMENTATION_LINKS_PASS files=104` | Repository-native recursive link checker passes after relocation and path repairs. |
| Exact stale paths | `STALE_EXACT_PATHS_PASS` | No references remain to deleted inventory, old audit names, removed JS modules, old memory paths or old production-readiness path in current/evidence text checked. |
| Repository hygiene | `REPOSITORY_HYGIENE_PASS` | No forbidden generated artifacts or secret-like repository clutter detected. |
| Diff whitespace | PASS | `git diff --check` passes. |
| Frontend dependencies | PASS | `npm audit --audit-level=moderate` and `npm audit --omit=dev --audit-level=moderate` both report 0 vulnerabilities. Local Node 22.13 emits an engine warning for Lighthouse 13.4.1, while CI/Docker are pinned to Node 22.19. |
| Frontend build | PASS | `npm run build:frontend`, `check_frontend_build.py` and static asset reference checks pass; 19 JS and 19 CSS source modules produce two bundles. |
| Python tests | PASS | `python3 -m pytest -q` completes with no failures and the expected single skip for unavailable live/external behavior. |
| Self-check/release gate | PASS | `scripts.selfcheck` passes with expected live LLM/credential skips; `scripts.release_gate` reports `RELEASE GATE: PASS`. |
| Lint/compile | PASS | `ruff check app scripts tests` and `python3 -m compileall -q app scripts tests` pass. |
| P0/local checks | PASS | P0 infrastructure, backup/restore drill, frontend and static reference checks pass locally; the restore result is explicitly synthetic/disposable. |
| External infrastructure | NOT RUN | Docker is unavailable in this sandbox; production-like PostgreSQL/S3/restore, Telegram device, payments, live provider, legal/licensing and independent-domain gates remain external. |

## Final verdict

SHIP IT

The documentation cleanup is complete and internally consistent. Commit the cleanup change as a single reviewable documentation/hygiene commit. Do not interpret this verdict as public production approval; that decision remains governed by [`RELEASE/CURRENT_STATUS.md`](RELEASE/CURRENT_STATUS.md) and [`RELEASE/TASKS.md`](RELEASE/TASKS.md).

## References

[1]: [Repository README](../README.md) — repository-level start and safety boundary.

[2]: [Documentation map](README.md) — canonical documentation navigation and source-of-truth policy.

[3]: [Current release status](RELEASE/CURRENT_STATUS.md) — environment-separated release verdict.

[4]: [Current release backlog](RELEASE/TASKS.md) — authoritative unresolved work and acceptance criteria.

[5]: [Documentation link checker](../scripts/check_documentation_links.py) — repository-relative Markdown validation.
