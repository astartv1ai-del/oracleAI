# OracleAI — traceability matrix

**Дата:** 2026-08-26  
**Правило:** only executed checks or explicit external blockers may be marked as evidence.

| Requirement | Implementation | Files | Test / verification | Evidence | Status |
|---|---|---|---|---|---|
| Safe production startup | Fail-closed config and DEV_MODE guard | `app/api/main.py`, `app/config.py` | `tests/test_stage0_operations.py`, release gate | Self-check/release gate pass; real deploy not run | Local pass; external gate |
| Telegram authentication | Signed initData dependency and dev-only fallback | `app/api/security.py`, `app/api/deps.py` | `tests/test_security_regressions.py`, API tests | Automated suite pass | Local pass; device gate open |
| Owner isolation | Owner-scoped dependencies/repositories | `app/api/deps.py`, `app/repo/` | security and API tests | Full pytest pass | Local pass |
| Evidence-first AI | Deterministic tool → evidence → interpretation | `app/core/skills.py`, `app/core/interpretation.py`, `app/core/agent.py` | interpretation/agent tests, self-check | Full pytest and self-check pass | Local pass; live provider gate open |
| Date-only truth state | `time_known=false`, suppress houses/ASC/MC/wheel | `app/core/chart_contract.py`, `app/api/routers/chart.py`, `miniapp/js/10-chart.js` | chart contract, natal, PDF tests | Full pytest pass | Local pass |
| Natal calculation contract | Swiss Ephemeris/Kerykeion canonical source | `app/core/astro.py`, `app/core/chart_contract.py` | chart and placement tests | dependency audit and pytest pass | Local pass; independent calculator comparison open |
| Synastry/composite/transits/returns | JSON-first product builders and owner-scoped API | `app/core/chart_products.py`, `app/api/routers/chart_products.py` | chart product tests | Full pytest pass | Local pass; visual/report expansion open |
| Tarot random draw separation | Persisted cards/positions/orientation before interpretation; finalization is owner-scoped and append-only | `app/core/tarot.py`, `app/api/routers/tarot.py`, `app/repo/readings.py`, `app/services/chat.py` | Tarot tests, `tests/test_security_regressions.py` | Full pytest pass; cross-user and overwrite regression pass | Local pass; explicit public replay/seed contract remains open |
| Memory consent and deletion | Server-side memory flag, sanitized inspectable list/delete API, owner scope and recall-cache invalidation | `app/api/routers/profile.py`, `app/core/memory.py`, `app/repo/dialog.py`, `miniapp/js/12-misc.js` | `tests/test_security_regressions.py`, memory/context/security tests | Full pytest pass; embedding fields absent from public listing | **Implemented locally**; relevance/contradiction dataset open |
| Historical report immutability | Append-only report table and migration from legacy unique schema | `app/data/schema.py`, `app/data/migrations.py`, `app/repo/readings.py`, `app/core/agent.py` | `tests/test_report_history.py` | Targeted tests pass; old rows preserved | **Implemented locally** |
| Explicit report regeneration | `?refresh=true` and `report_id` response | `app/api/routers/chart.py`, `app/core/agent.py` | API regression plus report-history test | Targeted/full tests pass | **Implemented locally** |
| PDF fallback honesty | Explicit HTML fallback when PDF engine unavailable | `app/pdfgen/render.py` | `tests/test_pdfgen.py` | Full pytest pass | Local pass; full visual matrix open |
| Unified cross-tool history | Owner-scoped metadata read model across reports, Tarot, palm and chat sessions; no sensitive bodies or vector payloads | `app/repo/history.py`, `app/api/routers/history.py`, `app/api/routers/__init__.py` | `tests/test_api.py::test_unified_history_is_owner_scoped_and_actionable` | Full pytest, API test and hygiene pass | **Implemented locally**; client visual/E2E adoption remains open |
| Repository reproducibility | Pinned dependencies, CI, syntax/lint/hygiene gates | `requirements*.txt`, `.github/workflows/ci.yml`, scripts | Ruff, compileall, node check, pip-audit, release gate | All baseline checks pass | Local pass |
| Product surface documentation | Full matrix, backlog, baseline, domain/AI/memory/PDF/testing docs | `docs/*.md` | Documentation review and future traceability updates | Files created in this change | **Implemented locally** |
| Competitor benchmark | First-party product mechanics and gaps | `docs/COMPETITOR_MATRIX.md` | Source review | Astro.com, Astro-Seek, Kerykeion, AstroMatrix, Labyrinthos, Co-Star, Steer URLs | Benchmark documented |
| Production launch | Telegram, live LLM, payments, deploy, restore, licensing/legal | Infrastructure and external providers | Requires real environment and owner sign-off | No local simulation claimed | **External blocker** |

## Evidence index

Baseline commands and results are recorded in [BASELINE.md](BASELINE.md). The prioritized unresolved work is in [TASKS.md](TASKS.md). Domain methodology is in [DOMAIN_METHODS.md](DOMAIN_METHODS.md), agent behavior in [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md), memory in [MEMORY.md](MEMORY.md), PDF in [PDF_SYSTEM.md](PDF_SYSTEM.md), and verification strategy in [TESTING.md](TESTING.md).

## References

[1]: ../app/core/interpretation.py "Evidence and grounding implementation"  
[2]: ../app/data/migrations.py "Database migration implementation"  
[3]: ../tests/test_report_history.py "Report history regression tests"  
[4]: ../docs/COMPETITOR_MATRIX.md "First-party competitor benchmark"
