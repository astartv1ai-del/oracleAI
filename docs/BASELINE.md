# OracleAI — baseline audit

**Дата:** 2026-08-26  
**Ветка:** `master`  
**Коммит:** `0e616fb` (`feat: preserve immutable report history`)
**Репозиторий:** `astartv1ai-del/oracleAI`

## Runtime and inventory

| Item | Observed |
|---|---|
| Python | 3.12.3 |
| Node.js | v22.13.0 |
| pnpm | 11.21.0 |
| Python modules | 183 files under `app`, `scripts`, `tests` |
| Mini App JavaScript | 18 modules |
| CSS | 18 files under `miniapp` |
| Test modules | 42 `test_*.py` files |
| API routers | 14 router modules, plus FastAPI entrypoint |
| Frontend | Vanilla JavaScript, numbered module loading, Telegram Mini App surface |
| Backend | FastAPI, aiogram, SQLite/WAL, deterministic domain core |

## Reproducible checks

The following commands were executed from the repository root with `APP_ENV=dev DEV_MODE=1 LLM_PROVIDER=off` where applicable:

```text
python3 -m scripts.selfcheck       PASS
pytest -q                          PASS
python3 -m compileall -q app scripts tests  PASS
node --check miniapp/js/*.js       PASS
node --check admin/*.js            PASS
ruff check app scripts tests       PASS
python3 -m scripts.release_gate    PASS
pip-audit -r requirements.txt      PASS — No known vulnerabilities found
PDF RU/EN exact/date-only samples  PASS — A4 output generated; date-only truth-state visually/textually verified
HTTP public/health/OpenAPI smoke   PASS — expected 200s and security headers present
```

The self-check reported two expected skips: live LLM provider verification was disabled, and the local `.env` does not contain production credentials. Offline mode is intentional for deterministic local verification.

## Initial risks and blockers

The initial audit found a P1 data-integrity defect: legacy report rows used a unique key with `INSERT OR REPLACE`, so regeneration could delete history. This is fixed in commit `0e616fb` with an idempotent migration, append-only inserts, owner-scoped `report_id` reads, explicit `?refresh=true`, deterministic source metadata and regression tests. A second audit also found date-only PDF fallback prose that used placeholder house/ASC wording; this is fixed with sign-only sections and new RU/EN regressions.

This is not equivalent to production readiness. The most important unproven areas are real Telegram signed-initData/device QA, live LLM grounding and safety evaluation, external payment settlement/refund/reconciliation, production deployment validation, backup/restore drill, visual regression of the complete PDF golden-case matrix, independent astrology calculator comparison, licensing approval and legal/privacy sign-off.

## Audit evidence

The route and surface inventory was collected from `app/api/routers/`, `app/api/main.py`, `miniapp/js/`, `app/core/`, `docs/` and `tests`. Browser extraction confirmed the Mini App first-use surface; screenshot upload was unavailable in the sandbox browser, so pixel-level browser approval is not claimed. PDF page inspection evidence is recorded in [LOCAL_BROWSER_BASELINE.md](LOCAL_BROWSER_BASELINE.md). The canonical capability boundary is documented in [CHART_TYPE_CAPABILITIES.md](CHART_TYPE_CAPABILITIES.md), while the full product matrix is in [FULL_PRODUCT_SURFACE.md](FULL_PRODUCT_SURFACE.md) and prioritized work is in [TASKS.md](TASKS.md).
