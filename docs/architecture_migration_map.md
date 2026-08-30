# Architecture Migration Map (OracleAI)

_Живой документ. Отражает состояние на момент запуска full-architecture migration gauntlet._

Легенда для колонки **Status**:

- **canonical** — единственный источник правды, консюмеры уже переведены.
- **transitional** — новый слой уже канонический, но временно сохраняется тонкая совместимость / оверлей.
- **legacy** — устаревший слой, подлежит удалению после переезда консюмеров.
- **removed** — заменён и удалён в рамках этой миграции.

## Общий обзор

| Слой | Canonical location | Notes |
| ---- | ------------------ | ----- |
| Runtime агентов | `app/core/agents/runtime.py` | Единственный path свободного диалога. |
| Профили агентов | `app/agents/<code>/agent.yaml` + `SYSTEM.md` + `skills/` | Файловые пакеты. |
| Реестр агентов | `app/core/agents/registry.py` (см. Commit 2) | Ранее часть `specs.py`. |
| Executable tools | `app/core/tool_registry.py` (см. Commit 3) | Переименование из `app/core/skills.py`. |
| Сценарии | `app/core/scenarios/` (см. Commit 4) | Ранее в `app/core/agent.py`. |
| DB session/pool | `app/data/session.py` + `app/data/postgres.py` | PostgreSQL only. |
| DB repositories | `app/repo/*.py` | SQL живёт только здесь. |
| Business services | `app/services/*.py` | Продуктовая политика. |
| DB schema | Alembic (`alembic/versions/`) | Единственный источник правды по DDL. |
| Config | `app/config.py` (Settings) | Единственный slot для env. |

## Подсистемы

### Agents

| Subsystem | Legacy | New | Active consumer | Canonical target | Status |
| --------- | ------ | --- | --------------- | ---------------- | ------ |
| Agent definitions | `app/core/agents/specs.py` (hardcoded `AgentSpec`) | `app/agents/<code>/agent.yaml` + `SYSTEM.md` | `agents/runtime.py`, все скрипты и тесты | `app/agents/<code>/*` + `app/core/agents/registry.py` | legacy → **removed** |
| Agent registry loader | Оверлей `_with_file_profile()` поверх hardcoded specs | Чистая загрузка из файловых пакетов | `runtime.resolve`, `routing`, API | `app/core/agents/registry.py` | **canonical** |
| Agent runtime | `app/core/agents/runtime.py` | тот же | Bot, Mini App API | `app/core/agents/runtime.py` | **canonical** |
| Freeform chat facade | `app/core/agent.ask_oracle` | `agents.answer` | Сервисы/боты | `app/core/agents/runtime.answer` | legacy → **removed** |
| Scenarios (natal report, forecast, tarot interpretation, memory extract) | `app/core/agent.py` (60KB mixed) | `app/core/scenarios/*.py` | Bot, Mini App, планировщик | `app/core/scenarios/{forecast,tarot,report,memory,compat}.py` + facade `app/core/agent.py` (thin re-export) | legacy split → **transitional** thin facade |

### Tools / Skills

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Executable tool registry | `app/core/skills.py` | `app/core/tool_registry.py` | agents runtime, PDF, admin | `app/core/tool_registry.py` | rename → **canonical** |
| SKILL manifest | `app/agents/<code>/skills.manifest.yaml` | Генерируется из `SKILL.md` | file_loader, admin | `skills/*/SKILL.md` (source of truth) + generated manifest | **canonical** |
| Legacy `core.skills` alias | — | — | tests, seed | Импорт `from app.core.tool_registry as skills` (transitional shim удалён после последнего consumer'а) | **removed** |

### Database access

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| DB facade | `app/db.py` | `app/repo/*` + `app/services/*` | `scripts/selfcheck.py`, ничего в runtime | Repositories + services напрямую | legacy → **removed** |
| Session/pool | `app/data/session.py` | тот же | все модули | `app/data/session.py` | **canonical** |
| Repositories | `app/repo/*.py` | тот же | services, API, bot | `app/repo/` | **canonical** |
| Services | `app/services/*.py` | тот же | API, bot | `app/services/` | **canonical** |

### DB Schema

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| DDL source | `app/data/schema.py` (SQLite-flavour) + `app/data/pg_schema.py` (transform to PostgreSQL) + `alembic/` | `alembic/versions/*.py` (native PostgreSQL DDL) | `session.connect()` (только проверка ревизии) | Alembic | legacy → **removed** |
| Runtime schema creation | Consult `session.connect` — только `SELECT version_num FROM alembic_version` | тот же | production boot | Alembic | **canonical** |
| SQLite derivation | `pg_schema.py._render_tables()` (SQLite→PG replace) | Native Alembic ops | production, tests | Alembic native DDL (0001_pg_native_baseline) | legacy → **removed** |

### Domain engines (astrology / tarot / palm / matrix / compat)

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Astrology calculation | `app/core/astro.py` + `app/core/astrology_engine.py` | тот же — правильное layering (engine vs. facade) | scenarios, skills, PDF | `astro.py` (public), `astrology_engine.py` (implementation) | **canonical** — не объединяется |
| Chart contract & rendering | `app/core/chart_contract.py`, `chart_rendering.py`, `chart_interpretation.py`, `chart_products.py` | тот же | PDF, agents, API | `app/core/chart_*` | **canonical** |
| Tarot | `app/core/tarot.py` + `app/core/cards.py` | `tarot.py` (deck + draw), `cards.py` (share image only) | scenarios, skills, share | Разные ответственности, единый source | **canonical** |
| Palm | `app/core/palm*.py` | тот же | agents/mira, admin | Единый набор с чёткими ролями | **canonical** |

### Billing / Catalog

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Product catalog | Historical `plans` table | `monetization_catalog` v2 (price_book, plans, products) | `services/catalog.py`, `services/entitlements.py` | v2 tables + `services/catalog.py` | **canonical** (v2 живой, legacy `plans` — historical only). |
| Entitlements | ledger + subscription_state | тот же | services | `services/entitlements.py` | **canonical** |
| Crystals | `services/billing.py` + `repo/billing.py` | тот же | всё | Единый source | **canonical** |

### Localization

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Bot copy | Отдельные RU/EN блоки в handler'ах | `app/bot/i18n.py` + локальные RU/EN dict'ы | bot handlers | `app/bot/i18n.py` | **canonical** — hardcoded строки в hot paths устранены в Wave 1-3. |
| API-facing copy | agent prompts (файлы `SYSTEM.md`), analytics `event_labels` | Профили агентов + i18n dict | API, notifications | Профили и i18n | **canonical** |

### Bot / Mini App

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Chat flow | Раньше был отдельный old handler → удалён | `app/bot/chat.py` через `agents.answer` | Users | Single flow | **canonical** |
| Onboarding | `app/bot/onboarding.py` | тот же | Users | Single flow | **canonical** |
| Domain data | Bot → services → repo; Mini App → API → services → repo | Тот же single-service path | Обе поверхности | Единый service слой (`app/services/*`) | **canonical** |

### Config

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Env loader | `app/config.py` (`Settings`) | тот же | всё | `app/config.py` | **canonical** |
| Duplicate env vars | нет активных дублей | — | — | — | **canonical** |

### Analytics

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Event dictionary | `docs/ANALYTICS_EVENT_DICTIONARY.md` + code sites | `app/services/analytics.py` + repo | Bot, Mini App, API | Single vocabulary | **canonical** |

### Memory

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Retrieval / summaries | `app/core/memory.py` (единственный pipeline) | тот же | agents runtime | `app/core/memory.py` | **canonical** |

### LLM Gateway

| Subsystem | Legacy | New | Consumer | Canonical | Status |
| --------- | ------ | --- | -------- | --------- | ------ |
| Completion + routing | `app/core/llm.py` | тот же | все | `app/core/llm.py` | **canonical** — единственный gateway. |
| Cost accounting | `app/core/product_cost.py` + `repo/monetization` | тот же | analytics | Single ledger | **canonical** |

### Tests / CI

| Subsystem | Legacy | New | Canonical | Status |
| --------- | ------ | --- | --------- | ------ |
| Test DB | Раньше SQLite fixtures, теперь всё Postgres | тот же | Postgres only | **canonical** |
| Import references | `from app.core.agents.specs import get, codes, REGISTRY` | `from app.core.agents.registry import get, codes, REGISTRY` | `registry` | обновлено в этой миграции |

## Итоговый target

```
presentation (bot / miniapp / admin)
        ↓
services (business policy)
        ↓
domain / core (agents runtime, tool_registry, scenarios, domain engines)
        ↓
repo / data (SQL, PG session, seeds)
        ↓
PostgreSQL (schema via Alembic)
```

`app/db.py`, `app/core/agents/specs.py`, `app/core/skills.py`, `app/data/schema.py`, `app/data/pg_schema.py` — удалены; каждая ответственность имеет одного canonical owner'а.
