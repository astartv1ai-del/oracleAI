# Документация OracleAI

Этот каталог — единственный актуальный комплект документации OracleAI. Он описывает **существующее поведение кода и продукта**, а не список идей или историю промежуточной разработки. При изменении поведения приложения соответствующий документ обновляется в том же pull request.

## Навигация

| Документ | Для кого | Когда использовать |
|---|---|---|
| [PRODUCT.md](PRODUCT.md) | Product, support, маркетинг | Чтобы понять аудиторию, границы обещания и пользовательские сценарии. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Разработка, техлид, QA | Чтобы менять код, API, модели данных или интеграции. |
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Дизайн, frontend, QA | Чтобы добавлять экраны, компоненты и motion без визуального дрейфа. |
| [API.md](API.md) | Frontend, backend, интеграции | Чтобы вызывать или изменять HTTP-контракты. |
| [DEPLOYMENT.md](DEPLOYMENT.md) | DevOps, владелец продукта | Чтобы подготовить окружение, выпустить релиз и откатить его. |
| [SECURITY.md](SECURITY.md) | Разработка, support, legal | Чтобы работать с 16+, согласиями, личными данными и инцидентами. |
| [ANALYTICS_EVENT_DICTIONARY.md](ANALYTICS_EVENT_DICTIONARY.md) | Product, analytics, privacy | Чтобы добавлять KPI-события без PII и трактовать funnel одинаково. |
| [LLM_EVALUATION.md](LLM_EVALUATION.md) | LLM, QA, product | Чтобы проверять grounding, safety, language, next step и latency до релиза. |
| [LAUNCH_GOVERNANCE.md](LAUNCH_GOVERNANCE.md) | Product, operations, legal, support | Чтобы вести P0/P1 launch gates, владельцев, SLO и go/no-go decisions. |
| [PRODUCTION_READINESS_AND_LAUNCH_PLAN.md](PRODUCTION_READINESS_AND_LAUNCH_PLAN.md) | Все владельцы релиза | Чтобы пройти путь от beta до public launch и определить масштабирование. |
| [COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md](COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md) | Product, astrology, backend, QA | Чтобы реализовать будущие composite и planetary returns без неявных precision-правил. |
| [DESIGN_COMPONENT_INVENTORY.md](DESIGN_COMPONENT_INVENTORY.md) | Design, frontend, QA | Чтобы сохранять состояния компонентов, accessibility и visual regression matrix. |
| [SCALE_AND_MIGRATION.md](SCALE_AND_MIGRATION.md) | Operations, database, performance | Чтобы измерять SQLite/WAL triggers и репетировать migration без production риска. |
| [CHART_PRODUCT_CONTRACTS.md](CHART_PRODUCT_CONTRACTS.md) | Frontend, backend, agent, QA | Чтобы вызывать текущие natal, synastry и transit contracts одинаково. |
| [CHART_TYPE_CAPABILITIES.md](CHART_TYPE_CAPABILITIES.md) | Product, astrology, release owner | Чтобы отличать enabled product paths от upstream capabilities. |
| [MONETIZATION_BASELINE.md](MONETIZATION_BASELINE.md) | Product, billing, finance | Чтобы сверить текущие планы, SKU, платёжные пути и открытые gaps без PII. |
| [MONETIZATION_UNIT_ECONOMICS.md](MONETIZATION_UNIT_ECONOMICS.md) | Product, finance, operations | Чтобы считать net revenue, variable COGS, contribution, ARPPU, CAC и break-even по сценариям. |
| [MONETIZATION_RESEARCH_PACK.md](MONETIZATION_RESEARCH_PACK.md) | Product, finance, growth | Чтобы сверить verified market anchors, price ladder 1 490/4 990/9 990 ₽, scenario model, sensitivity и rollout gates. |
| [MONETIZATION_EXTERNAL_SOURCES.md](MONETIZATION_EXTERNAL_SOURCES.md) | Finance, legal, billing | Чтобы проверять официальные platform/payment sources и не подменять settlement data сниппетами. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Все участники разработки | Чтобы подготовить ветку, изменения и pull request. |
| [DOMAIN_METHODS.md](DOMAIN_METHODS.md), [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md), [MEMORY.md](MEMORY.md) | Domain, AI, product | Расчётные школы, evidence-first агенты и memory policy. |
| [PDF_SYSTEM.md](PDF_SYSTEM.md), [TESTING.md](TESTING.md) | QA, backend, product | Отчёты, visual regression и проверочные слои. |
| [FULL_PRODUCT_SURFACE.md](FULL_PRODUCT_SURFACE.md), [TASKS.md](TASKS.md), [TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md), [BASELINE.md](BASELINE.md) | Все владельцы | Surface matrix, backlog, evidence и baseline. |
| [COMPETITOR_MATRIX.md](COMPETITOR_MATRIX.md) | Product, strategy | First-party competitor benchmark и product gaps. |
| [CHANGELOG.md](CHANGELOG.md) | Все стейкхолдеры | Чтобы сверить состав версии и пользовательские изменения. |

## Локальная среда

Для работы нужен Python 3.11+ и доступ к Telegram-боту только при проверке настоящей авторизации. Установка зависимостей и создание `.env` выполняются один раз.

```bash
cd /path/to/oracleAI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Для быстрого просмотра интерфейса допустим локальный development-режим. Он открывает доступ через параметр `dev_user`; запускать его на публичном адресе нельзя.[1]

```bash
APP_ENV=dev DEV_MODE=1 uvicorn app.api.main:app --host 127.0.0.1 --port 8080
# http://127.0.0.1:8080/?dev_user=10001
```

В production следует использовать `DEV_MODE=0`, реальную HTTPS-базу в `WEBAPP_URL` и подпись `initData` от Telegram. Полный процесс приведён в [DEPLOYMENT.md](DEPLOYMENT.md).

## Рабочий цикл

| Этап | Минимальное действие | Артефакт проверки |
|---|---|---|
| Изменение продукта | Сверить сценарий с PRODUCT и DESIGN_SYSTEM. | Обновлённые тексты, состояния и аналитическое событие при необходимости. |
| Изменение данных | Обновить `schema.py` и миграции для существующих БД. | Новый запуск и регрессионный тест. |
| Изменение API | Изменить роутер и клиентский вызов. | Сверка с API.md и негативные сценарии. |
| Изменение UI | Использовать токены, каскад CSS и делегирование событий. | Проверка на мобильном viewport и `prefers-reduced-motion`. |
| Перед релизом | Прогнать синтаксис, тесты, selfcheck и review diff. | Запись в CHANGELOG и зелёный CI/локальный QA. |

## Источники правды

| Вопрос | Авторитетный источник |
|---|---|
| Таблицы и индексы | [`app/data/schema.py`](../app/data/schema.py) |
| Единый архив | [`app/repo/history.py`](../app/repo/history.py), [`app/api/routers/history.py`](../app/api/routers/history.py) |
| Изменение существующих таблиц | [`app/data/migrations.py`](../app/data/migrations.py) |
| Маршруты и статическая раздача | [`app/api/main.py`](../app/api/main.py), [`app/api/routers/`](../app/api/routers/) |
| Runtime-конфигурация | [`app/config.py`](../app/config.py), [`.env.example`](../.env.example) |
| Клиентские модули | [`miniapp/js/`](../miniapp/js/), [`miniapp/css/`](../miniapp/css/) |
| Проверки | [`tests/`](../tests/), [`pytest.ini`](../pytest.ini), [`scripts/selfcheck.py`](../scripts/selfcheck.py) |

## Версионирование документации

Новая версия продукта отражается в [CHANGELOG.md](CHANGELOG.md). В репозитории хранятся только текущие контракты, решения, инструкции и policy-документы. Временные аудиты, выгрузки, персональные данные, скриншоты с идентификаторами Telegram, terminal dumps и секреты хранятся вне source tree. Исследовательские материалы попадают в репозиторий только после отдельного утверждения и превращения в действующее решение.

## References

[1]: [app/api/main.py](../app/api/main.py) — проверка режима разработки в lifecycle FastAPI.
