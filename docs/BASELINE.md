# OracleAI — baseline audit

**Дата:** 2026-08-26  
**Ветка:** `master`  
**Коммит:** `e25c9d5870cd7acd4e65e9ca533e864b2a2181d5`  
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
```

The self-check reported two expected skips: live LLM provider verification was disabled, and the local `.env` does not contain production credentials. Offline mode is intentional for deterministic local verification.

## Initial risks and blockers

No failing P0/P1 local regression was observed in the repository’s existing automated suite. This is not equivalent to production readiness. The most important unproven areas are real Telegram signed-initData/device QA, live LLM grounding and safety evaluation, external payment settlement/refund/reconciliation, production deployment validation, backup/restore drill, visual regression of the complete PDF golden-case matrix, independent astrology calculator comparison, licensing approval and legal/privacy sign-off.

## Audit evidence

The route and surface inventory was collected from `app/api/routers/`, `app/api/main.py`, `miniapp/js/`, `app/core/`, `docs/` and `tests/`. The canonical capability boundary is documented in [CHART_TYPE_CAPABILITIES.md](CHART_TYPE_CAPABILITIES.md), while the full product matrix is in [FULL_PRODUCT_SURFACE.md](FULL_PRODUCT_SURFACE.md) and prioritized work is in [TASKS.md](TASKS.md).
