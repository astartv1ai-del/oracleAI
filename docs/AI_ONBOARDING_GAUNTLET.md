# OracleAI — AI / Onboarding / Telegram Gauntlet Ledger

**Дата проверки:** 2026-08-27
**Ветка:** `master`
**Метод:** inspect → define quality bar → implement → test → critic review
**Область:** локальная реализация и воспроизводимые проверки; production gates помечены отдельно.

> Этот документ — evidence ledger текущего артефакта, а не общий backlog. Локальный PASS не является доказательством production readiness.

## Quality bar

Поверхность может считаться готовой локально только если она одновременно **корректна, безопасна, объяснима, ограничена по бюджету, восстанавливаема и покрыта регрессией**. Критические дефекты в авторизации, приватности, оплате, safety или grounding дают автоматический FAIL.

## Evidence ledger

| Surface | Status | Owner | Acceptance criteria | Evidence | Last critic | Last verdict | Remaining risk |
|---|---|---|---|---|---|---|---|
| Agent identity and specialization | PASS локально | AI/backend | Каждый enabled agent имеет отдельную роль, правила и narrow tool set | [`app/core/agents/registry.py`](../app/core/agents/registry.py), [`tests/test_agent_context_integrity.py`](../tests/test_agent_context_integrity.py) | Fresh code review 2026-08-27 | PASS | Нужна live blind evaluation на выбранных production providers |
| Deterministic routing | PASS локально | AI/backend | Ясные доменные сигналы маршрутизируются предсказуемо; смешанные hard domains не drift-ят молча | [`app/core/agents/routing.py`](../app/core/agents/routing.py), [`tests/test_agent_routing.py`](../tests/test_agent_routing.py) | Fresh code review 2026-08-27 | PASS | Нужна staging-выборка реальных пользовательских формулировок |
| Prompt hierarchy and context integrity | PASS локально | AI/privacy | System rules выше profile, memory, diary, history, tool/model text; untrusted data явно размечено | [`app/core/agents/base.py`](../app/core/agents/base.py), [`tests/test_agent_context_integrity.py`](../tests/test_agent_context_integrity.py) | Fresh code review 2026-08-27 | PASS | Provider/model changes требуют повторной prompt-injection evaluation |
| Tool schemas and progressive disclosure | PASS локально | AI/backend | В prompt попадает ограниченный index; specialist получает только allow-listed tools | [`app/core/agents/file_loader.py`](../app/core/agents/file_loader.py), [`app/core/tool_registry.py`](../app/core/tool_registry.py) | Fresh code review 2026-08-27 | PASS | Полная route-by-route schema matrix требует отдельного внешнего QA |
| Runtime tool authorization | PASS локально | AI/backend | Model-generated forbidden tool call не исполняется даже при обходе advertised schema | [`app/core/agents/runtime.py`](../app/core/agents/runtime.py), regression test `test_runtime_rejects_forbidden_model_tool_call` | Fresh code review 2026-08-27 | PASS | Нужна live provider adversarial run |
| Tool loop, limits and recovery | PASS локально | AI/backend | Нулевой/один/несколько calls, timeout, exception, malformed args, max iterations и provider fallback дают bounded outcome | [`app/core/llm.py`](../app/core/llm.py), [`tests/test_llm.py`](../tests/test_llm.py) | Fresh code review 2026-08-27 | PASS | Production latency and cancellation behavior не подтверждены |
| Grounding and interpretation | PASS локально | Domain/AI | Deterministic facts не выдумываются; date-only state не создаёт house/ASC claims; fact отделён от interpretation/action | [`app/core/interpretation.py`](../app/core/interpretation.py), [`tests/test_interpretation_guardrails.py`](../tests/test_interpretation_guardrails.py), [`docs/CHART_PRODUCT_CONTRACTS.md`](CHART_PRODUCT_CONTRACTS.md) | Fresh code review 2026-08-27 | PASS | Нужна независимая астрологическая authority comparison |
| Memory privacy and lifecycle | PASS локально | AI/privacy | Opt-in, owner scope, pause/delete, cache invalidation and injection-shaped data are covered | [`app/core/memory.py`](../app/core/memory.py), [`app/repo/dialog.py`](../app/repo/dialog.py), [`tests/test_security_regressions.py`](../tests/test_security_regressions.py), [`MEMORY_EVALUATION.md`](MEMORY_EVALUATION.md) | Fresh code review 2026-08-27 | PASS локально | Longitudinal stale-fact telemetry and production retention review remain open |
| Shared context | PASS локально | AI/backend | Historical recommendations are scoped, labelled as data and checked for contradictions | [`app/core/shared_context.py`](../app/core/shared_context.py), [`tests/test_shared_context.py`](../tests/test_shared_context.py) | Fresh code review 2026-08-27 | PASS | Staging multi-device journey remains external |
| Unified chat persistence | PASS локально | Backend | User/thread owner scope, idempotency, append-only messages and refund-on-failure are preserved | [`app/services/chat.py`](../app/services/chat.py), [`app/repo/dialog.py`](../app/repo/dialog.py), [`tests/test_api.py`](../tests/test_api.py) | Fresh code review 2026-08-27 | PASS | Real Telegram retry/device behavior remains external |
| Onboarding data quality | PASS локально | Bot/product | Invalid date/time is recoverable; city purpose is explained; unknown city and chart failure keep the user on a retryable state | [`app/bot/onboarding.py`](../app/bot/onboarding.py), [`tests/test_bot_fsm.py`](../tests/test_bot_fsm.py) | Fresh code review 2026-08-27 | PASS | Real network/geocoder outage and duplicate Telegram updates require staging |
| First value | PASS локально | Bot/product | First chart reveal uses stored deterministic facts and exposes date-only limitations before persona choice | [`app/bot/onboarding.py`](../app/bot/onboarding.py) | Fresh code review 2026-08-27 | PASS | Manual Russian/English content review remains open |
| Mini App intro and chat micro-interactions | PASS локально | Frontend/product | Intro, chat preparation, loading, recovery and contextual actions use product language rather than implementation jargon | [`miniapp/js/05-app.js`](../miniapp/js/05-app.js), [`miniapp/js/07-chat.js`](../miniapp/js/07-chat.js), [`miniapp/css/11-misc.css`](../miniapp/css/11-misc.css) | Fresh code review 2026-08-27 | PASS локально | Full six-viewport screenshot matrix and device review remain external |
| Telegram `/start`, menu and deep links | PASS локально | Bot/product | New, returning, referral/promo, incomplete onboarding and admin cases are routed through one entry path | [`app/bot/onboarding.py`](../app/bot/onboarding.py), [`app/bot/keyboards.py`](../app/bot/keyboards.py), [`tests/test_bot_fsm.py`](../tests/test_bot_fsm.py) | Fresh code review 2026-08-27 | PASS локально | Signed-initData, Telegram clients and duplicate update staging remain external |
| Admin visibility and authorization | PASS локально | Security/backend | Dashboard button is server-derived; direct API, role changes and revoked roles are denied by current request | [`app/api/deps.py`](../app/api/deps.py), [`app/api/routers/admin.py`](../app/api/routers/admin.py), [`app/repo/admin.py`](../app/repo/admin.py), [`tests/test_security_regressions.py`](../tests/test_security_regressions.py) | Fresh code review 2026-08-27 | PASS локально | Real Telegram signed session, cache revocation and deployment proxy review remain external |
| Admin observability | PASS локально | Operations | Dashboard exposes aggregate health, users, events, costs, safety, payment health and audit paths by permission | [`app/api/routers/admin.py`](../app/api/routers/admin.py), [`admin/admin.js`](../admin/admin.js) | Fresh code review 2026-08-27 | PASS локально | Production dashboards and alert delivery remain external |
| Cost and latency | PARTIAL | AI/operations | Workflow, tool-call and cost budgets exist; representative benchmark is recorded; live LLM p95 meets target | [`app/core/llm.py`](../app/core/llm.py), [`EVIDENCE/PERFORMANCE_BASELINE_2026-08-27.md`](EVIDENCE/PERFORMANCE_BASELINE_2026-08-27.md), [`RELEASE/TASKS.md`](RELEASE/TASKS.md) | Fresh code review 2026-08-27 | FAIL gate | Current local docs record live p95 above 15 seconds; provider optimization/staging required |
| Payments and production operations | BLOCKED external | Billing/operations | Sandbox settlement, refund, reconciliation, production backup/restore and rollback are certified | [`RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md`](RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md), [`docs/BACKUP_RESTORE_DRILL.md`](BACKUP_RESTORE_DRILL.md) | Fresh code review 2026-08-27 | BLOCKED | Requires provider sandbox, production storage/deployment and operational approval |

## Local run evidence

| Check | Result |
|---|---|
| Full pytest | PASS, one expected live-LLM skip |
| Python compileall | PASS |
| JavaScript `node --check` | PASS |
| Ruff | PASS |
| Selfcheck with LLM disabled | PASS; expected credential/live-provider skips only |
| Release gate | PASS |
| Targeted runtime/onboarding regression tests | PASS, 21 tests |
| `git diff --check` | PASS |

## Gauntlet loop record

The implementation pass identified two concrete local gaps. First, runtime execution trusted the advertised tool list but did not independently reject a model-requested tool outside the current agent's allow-list; the runtime now returns a neutral refusal without invoking the tool. Second, onboarding silently converted arbitrary invalid time strings into unknown time and allowed city/chart failures to escape without a user-facing retry path; invalid time now stays on the time step, while city and chart failures are rendered as recoverable messages.

The targeted critic checked the changed code and regression tests without relying on builder explanations. The local artifact passed the changed-surface gates. The integration-level verdict remains **BLOCKED** because live Telegram signed sessions, provider latency, payment certification, deployment backup/restore, independent calculation comparison and legal/privacy approvals are outside this local repository run.

## References

[1]: ../app/core/agents/registry.py "OracleAI agent specifications"
[2]: ../app/core/agents/runtime.py "OracleAI agent runtime"
[3]: ../app/bot/onboarding.py "OracleAI Telegram onboarding"
[4]: ../app/api/deps.py "OracleAI API authentication and admin dependencies"
[5]: ../docs/TASKS.md "OracleAI production task ledger"
