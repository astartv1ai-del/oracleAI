> STATUS: HISTORICAL
> SUPERSEDED BY: `../AI_SYSTEM.md and ../RELEASE/CURRENT_STATUS.md`
> This dated evidence is retained for audit context; it is not a current source of truth.

# OracleAI — AI System Final Review

**Дата:** 2026-08-27
**Ветка:** `master`
**Scope:** локальный source-tree review и deterministic QA после Gauntlet pass.

## Verdict

**BLOCKED**

Репозиторий локально проходит автоматические проверки и закрывает выявленные в этом pass дефекты runtime allow-list и onboarding recovery. Публичный production verdict заблокирован конкретными внешними gates: реальная Telegram signed-initData/device E2E, staging live-LLM latency, payment provider certification, production deployment/backup-restore, independent astrology authority comparison и legal/privacy/licensing approval.

## AI

### Agents

Проверены четыре enabled agents: Lilith/Oracle (`oracle`), Urania/Astrology (`astro`), Madame Lenormand/Tarot (`tarot`) и Mira/Palm (`chiromant`). Их identity, domain, skills, greetings, suggestions, language rules and risk contracts остаются отдельными; specialist agents не превращены в один general chatbot. Source of truth: [`app/core/agents/specs.py`](../../app/core/agents/specs.py) и [`app/core/agents/file_loader.py`](../../app/core/agents/file_loader.py).

### Skills and tools

Skill selection uses a compact index and progressive activation. Advertised tools are derived from `AgentSpec.skills`. В ходе review найден и исправлен критичный defense-in-depth gap: до патча runtime доверял только advertised schema, но executor не делал самостоятельную проверку имени tool. Теперь `app/core/agents/runtime.py` отклоняет model-generated call, если имя отсутствует в allow-list текущего агента, и возвращает нейтральное сообщение без вызова `skills.execute`.

### Routing

Routing remains deterministic and explainable. Explicit agent selection wins; default Oracle auto-routes only for a sufficiently strong signal; mixed hard domains stay on the default agent and request clarification. Matrix coverage is in [`tests/test_agent_routing.py`](../../tests/test_agent_routing.py).

### Prompt integrity and grounding

Prompt assembly separates global dialogue rules, agent identity, deterministic chart/matrix evidence, language, bounded profile summary, consent-aware memory, shared context, tool protocol, skills and safety. Memory, diary, history, tool output and user/model text are labelled as untrusted data. Date-only charts do not receive invented houses, ASC or MC. Relevant contracts are [`app/core/agents/base.py`](../../app/core/agents/base.py), [`app/core/agents/runtime.py`](../../app/core/agents/runtime.py) and [`app/core/interpretation.py`](../../app/core/interpretation.py).

### Memory and shared context

Memory is opt-in, owner-scoped, deletion-aware and cache-invalidating. Disabled memory blocks recall, writes and diary retrieval. Shared recommendations remain historical context rather than authority and are checked for scope/date conflicts. Local privacy regressions pass; longitudinal stale-fact telemetry is still an external launch gate.

### Tool loop and fallback

`run_agent` bounds workflow deadline, iterations, tool calls, output size and cost. Tool timeout/exception paths return safe neutral text; provider errors move through the configured fallback chain; an offline answer uses deterministic chart/matrix/card data rather than claiming unavailable capabilities. Full provider truthfulness and p95 latency still require staging.

## Onboarding

The Telegram onboarding path is age-gated, collects name/gender/date/time/city, explains why birth time and city are requested, generates the chart before persona selection and returns a first-value reveal from stored chart facts. The first-value copy no longer relies on generic “three things about you” claims: it shows Sun, Moon where available and an explicit precision limitation when birth time is not confirmed.

The review found two concrete recovery gaps. Invalid time input was silently treated as unknown time; it now remains on the time step with a format hint. Geocoding and chart calculation failures could leave the user without an actionable response; they now preserve `Onb.city` and show a localized retry/fallback-city message. Regression coverage is in [`tests/test_bot_fsm.py`](../../tests/test_bot_fsm.py).

The Mini App already includes a three-screen intro, authenticated boot recovery, chat preparation/loading/error states, contextual actions and reduced-motion-aware visual layers. The remaining screenshot/device matrix is not reproducible in this sandbox.

## Telegram

`/start` routes through a shared onboarding entry point for new, returning, incomplete, referral and promo users. The main menu puts “Open OracleAI” first and derives the admin button from a server-side role check. Commands and callbacks remain separated between normal-user features and admin operations.

Real Telegram client behavior remains unverified for Android, iOS, Desktop, WebView, slow network, expired signed sessions and duplicate updates. These are not represented as local PASS claims.

## Admin

Admin access is checked server-side at every API route through `current_admin` and permission dependencies. The role is resolved from Telegram identity or development-only local override; client-controlled role fields are not trusted. Dashboard, payment, safety, grants and role-management paths have permission boundaries and audit writes for meaningful mutations. Direct API requests from normal users are covered by tests; stale frontend state and real WebView revocation behavior require staging.

The Dashboard button is generated only when `_is_admin()` resolves an authorized role. Normal users do not receive the button in the Telegram menu. Static `/admin` shell delivery remains intentionally separate from data authorization: the admin page cannot load operational data without a valid authorized session. A local browser smoke of direct `/admin` without `initData` rendered only the auth gate and no dashboard data; details are recorded in [`docs/local_admin_smoke.md`](LOCAL_ADMIN_SMOKE_2026-08-27.md).

## Evidence

| Check | Result |
|---|---|
| Full `pytest -q` with `LLM_PROVIDER=off` | PASS; one expected live-provider skip |
| Targeted agent/onboarding tests | PASS; 21 tests |
| `python3 -m compileall -q app scripts tests` | PASS |
| `node --check` for Mini App and admin JS | PASS |
| `ruff check app scripts tests` | PASS |
| `python3 -m scripts.selfcheck` | PASS; expected live/provider credential skips only |
| `python3 -m scripts.release_gate` | PASS |
| `git diff --check` | PASS |
| Living evidence ledger | [`docs/AI_ONBOARDING_GAUNTLET.md`](../AI_ONBOARDING_GAUNTLET.md) |

## Concrete external blockers

| Blocker | Required evidence before SHIP IT |
|---|---|
| Telegram authentication and devices | Staging test with real signed and tampered/expired initData on Android, iOS, Desktop and WebView; verify owner isolation and no sensitive URL/log leakage |
| Live LLM quality and latency | Run the synthetic safety/grounding set on production provider chain; zero critical violations and p95 at or below the documented 15-second target |
| Payment operations | Provider sandbox certification for invoice, duplicate webhook, refund, chargeback, failure and reconciliation |
| Deployment and recovery | Production backup/restore, migration rollback and storage isolation drill |
| Independent domain authority | Record identical-setting comparisons against an independent astrology calculator for normal, DST, historical timezone, unknown-time, high-latitude and midnight cases |
| Licensing and legal/privacy | Swiss Ephemeris/Kerykeion licensing confirmation and legal/privacy review for memory, palm images, retention and 16+ product claims |

## References

[1]: ../app/core/agents/runtime.py "OracleAI agent runtime"
[2]: ../app/core/llm.py "OracleAI LLM workflow"
[3]: ../app/bot/onboarding.py "OracleAI Telegram onboarding"
[4]: ../app/api/deps.py "OracleAI authentication and admin dependencies"
[5]: ../docs/TASKS.md "OracleAI production task ledger"
