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
| [CONTRIBUTING.md](CONTRIBUTING.md) | Все участники разработки | Чтобы подготовить ветку, изменения и pull request. |
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
| Изменение существующих таблиц | [`app/data/migrations.py`](../app/data/migrations.py) |
| Маршруты и статическая раздача | [`app/api/main.py`](../app/api/main.py), [`app/api/routers/`](../app/api/routers/) |
| Runtime-конфигурация | [`app/config.py`](../app/config.py), [`.env.example`](../.env.example) |
| Клиентские модули | [`miniapp/js/`](../miniapp/js/), [`miniapp/css/`](../miniapp/css/) |
| Проверки | [`tests/`](../tests/), [`pytest.ini`](../pytest.ini), [`scripts/selfcheck.py`](../scripts/selfcheck.py) |

## Версионирование документации

Новая версия продукта отражается в [CHANGELOG.md](CHANGELOG.md). Не копируйте в `docs/` временные аудиты, выгрузки, персональные данные, скриншоты с идентификаторами Telegram или секреты. Для исследовательских материалов используйте отдельный защищённый рабочий контур, а в репозитории оставляйте только утверждённые решения.

## References

[1]: [app/api/main.py](../app/api/main.py) — проверка режима разработки в lifecycle FastAPI.
