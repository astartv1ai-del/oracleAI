> STATUS: HISTORICAL
> SUPERSEDED BY: `../RELEASE/CURRENT_STATUS.md and ../RELEASE/TASKS.md`
> This dated evidence is retained for audit context; it is not a current source of truth.

# OracleAI Autonomous Gauntlet Report

**Автор:** Manus AI
**Дата проверки:** 2026-08-27
**Решение:** **BLOCKED — external production gates remain; public launch is NO-GO**

## Executive decision

OracleAI прошёл локальный autonomous gauntlet по коду, disposable API, Mini App browser capture, domain contracts, payment catalog presentation, safety boundaries и deterministic release gates. Подтверждённые локальные дефекты исправлены, а regression coverage усилена. Это означает, что repository-level quality bar достигнут; это **не** означает, что проект получил production approval.

Публичный запуск остаётся **NO-GO**, потому что несколько обязательных доказательств нельзя получить в sandbox: real Telegram signed `initData` на iOS/Android/Desktop, реальное payment settlement и reconciliation, legal/operator approval, production off-site backup/restore и rollback, alert routing/on-call, а также целевой live LLM latency. Локальные synthetic identities, disposable SQLite, provider mocks и offline fallbacks не подменяют эти внешние acceptance gates.

## Quality bar and ownership

Проверка разделяла ownership по поверхностям. Frontend отвечает за state clarity, localization, accessible labels и server-owned commerce presentation; backend отвечает за auth, eligibility, idempotency, privacy и fail-closed behavior; domain layer отвечает за deterministic astronomy/tarot/palm evidence contracts; operations layer отвечает за backup, monitoring, rollback и launch evidence.

Визуальный bar оценивался не по декоративности, а по hierarchy, alignment, density, state clarity и cross-screen consistency. Такой подход сопоставлялся с публично описанным Linear redesign focus на снижении visual noise, сохранении alignment и усилении hierarchy/density интерфейса [1]. AI trust bar оценивался по explicit evidence, limitation states, privacy controls и discoverable safety/reporting paths; это соответствует публичному positioning NotebookLM вокруг grounded information, source citations и privacy/safety controls [2].

## Confirmed findings and fixes

| Finding | Evidence | Fix |
|---|---|---|
| RU daily forecast used nominative sign after `для`, producing the observed `для Близнецы` grammar defect | Deterministic `_forecast_offline` matrix across all 12 signs | Added canonical prepositional forms for all 12 signs and regression coverage in `tests/test_growth.py` |
| EN Tarot picker rendered Russian prompts, labels, placeholder and CTA | Fresh Playwright EN Tarot capture | Added explicit RU/EN Tarot dictionary, spread catalog mapping and localized pending/cards/evidence states in `09-tarot.js` and `07-chat.js` |
| EN chat shell retained Russian agent labels, composer, sessions and toolbox copy | Fresh Playwright EN Tarot/chat capture | Added `CHAT_I18N`, English agent labels, localized suggestions, session controls, composer and toolbox labels |
| Payment surface had mixed-language copy and assumed the wrong storefront shape | `/api/shop` returned root product groups (`spread`, `report`, `question`, `crystals`) while renderer read only `data.products` | Added explicit payment copy/catalog localization and normalized both nested and root product-group response shapes in `17-payments.js` |
| Payment browser evidence did not prove one-off products were rendered | Payment DOM state after shape mismatch | Capture harness now records `paymentPlanCount` and `paymentProductCount` and requires both to be non-zero |
| Visual capture used fragile nav indexes and did not prove server-side locale separation | Capture harness and seed inspection | Navigation now uses `data-goto`; RU/EN identities are separate (`10001`/`10002`), and report checks expected locale markers with the opposite marker absent |
| Production config accepted `DEV_MODE=1` when `_validate_production_config()` was called in a non-dev environment | Disposable fail-closed probe reproduced the bypass | Production validation now rejects `DEV_MODE=1` outside `APP_ENV=dev/test`; regression added in `tests/test_security_regressions.py` |
| Clean CI runner skipped declared runtime requirements, so palm ONNX/OpenCV tests failed before product code was exercised | GitHub run `33086018760` failed in Full tests while `requirements-dev.txt` omitted `requirements.txt` | CI now installs `requirements.txt -r requirements-dev.txt`; local full suite passes after matching dependency installation |

## Verification matrix

| Layer | Result | Notes |
|---|---:|---|
| Full pytest | **PASS** | 1 expected skip; remaining suite green |
| Ruff | **PASS** | `app`, `tests`, `scripts` |
| Python compileall | **PASS** | `app`, `tests`, `scripts` |
| JavaScript syntax | **PASS** | All `miniapp/js/*.js` files |
| Repository hygiene / cache / design / contrast | **PASS** | No tracked generated artifacts; cache and design contracts green |
| Domain evaluation | **PASS** | 54/54 cases |
| API integration smoke | **PASS** | `/api/health`, `/api/me`, `/api/today`, `/api/agents`, `/api/tarot/spreads`, `/api/shop` returned valid JSON/HTTP 200 in disposable dev mode |
| Visual/accessibility harness | **PASS** | RU/EN, 360×800, 390×844, 430×932; 10 states per viewport; no overflow, unnamed focusables or missing image alt attributes |
| Payment DOM contract | **PASS** | 5 plans and 5 product cards observed in inspected RU/EN payment states |
| Production fail-closed probe | **PASS** | Missing secrets and `DEV_MODE=1` in production both rejected |
| Offline selfcheck and release gate | **PASS** | Expected skips only for live LLM and absent production credentials |
| GitHub CI final run | **PASS** | Run `33094323868` for SHA `9879ec0`; `quality` and `frontend-quality` both successful |

## Visual and interaction assessment

Fresh deterministic captures covered age gate, Today, Guides/chat, payment, Profile, chart tab/modal, history, memory tab/modal and Tarot picker. The latest report passed for all six locale/viewport combinations. RU and EN used distinct server-side synthetic identities, not a client-side relabel of the same user. The inspected EN Tarot state showed English prompts, question placeholder, draw CTA, agent labels, composer presence, toolbox label and suggestion chips. The inspected EN payment state showed English hero, balance, payment methods, trust copy, plan titles/taglines and pricing presentation.

The product’s visual system is coherent in the bounded mobile frame: the primary action remains discoverable above the safe-area dock, active navigation is explicit, cards keep a consistent hierarchy, and the decorative starfield does not create measured horizontal overflow. The Tarot screenshot is a picker state, not proof that a real draw or interpretation was completed. No real Telegram WebView, device matrix or signed initData approval is claimed.

## Production blockers that remain open

| Gate | Status | Why it remains open |
|---|---|---|
| Real Telegram auth and device QA | **OPEN** | Requires signed Telegram `initData` and iOS/Android/Desktop WebView testing outside the sandbox |
| Payment sandbox settlement/reconciliation | **OPEN** | Local idempotency and provider contracts pass, but no real provider settlement evidence exists |
| Legal/operator sign-off | **OPEN** | Privacy, Terms, 16+, retention and cross-border/payment wording require accountable human approval |
| Production backup/restore/rollback | **OPEN** | Disposable backup drill passes; an off-site production restore and rollback rehearsal has not been executed |
| Alert routing and on-call | **OPEN** | Sentry/log code exists; live routing, ownership and response-time evidence are unavailable |
| Live LLM latency target | **OPEN** | Previous bounded evidence was 12/12 with 0 critical violations, but p95 was 25.088 s versus the ≤15 s target |

## Reproduction commands

The repository-level checks can be reproduced with `python3 -m pytest -q`, `ruff check app tests scripts`, `python3 -m compileall -q app tests scripts`, and `node --check` over every `miniapp/js/*.js`. Deterministic release checks are listed in `docs/README.md` and include the repository hygiene, cache, design, contrast, domain, PDF, backup, selfcheck and release gate scripts. The disposable visual harness is `python3 scripts/capture_visual_baseline.py`; its generated screenshots and `report.json` must remain outside Git history.

The current browser baseline and evidence boundaries are documented in [`docs/EVIDENCE/LOCAL_BROWSER_BASELINE_2026-08-27.md`](LOCAL_BROWSER_BASELINE_2026-08-27.md). The external gate execution procedure remains in [`docs/RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md`](../RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md), and the launch decision contract remains in [`docs/RELEASE/LAUNCH_GOVERNANCE.md`](../RELEASE/LAUNCH_GOVERNANCE.md).

## References

[1]: https://linear.app/now/how-we-redesigned-the-linear-ui "Linear — How we redesigned the Linear UI"

[2]: https://notebook.google/ "Google NotebookLM / Notebook overview"
