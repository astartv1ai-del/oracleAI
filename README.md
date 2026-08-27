# OracleAI

**OracleAI** — Telegram-бот и Mini App для бережного самопознания через ежедневные ритуалы, астрологические инсайты, Таро, дневник и диалог с AI-проводниками. Продукт рассчитан на русско- и англоязычную аудиторию **16+**; он поддерживает рефлексию и не заменяет медицинскую, психологическую, юридическую или финансовую помощь.

> Статус документации: **v2.0**. Этот репозиторий использует документацию как рабочий контракт между продуктом, дизайном, разработкой и эксплуатацией.

| Область | Основной документ | Назначение |
|---|---|---|
| Старт и навигация | [docs/README.md](docs/README.md) | Быстрый старт, команды и карта документации. |
| Продукт | [docs/PRODUCT.md](docs/PRODUCT.md) | Аудитория, ценность, сценарии и проводники. |
| Архитектура | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Компоненты, потоки данных, модули и хранилище. |
| Интерфейс | [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) | Токены, компоненты, motion и доступность. |
| Контракты | [docs/API.md](docs/API.md) | HTTP API, авторизация, лимиты и ошибки. |
| Эксплуатация | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Переменные окружения, запуск, релиз и мониторинг. |
| Безопасность | [docs/SECURITY.md](docs/SECURITY.md) | 16+, приватность, память, платежи и инциденты. |
| Разработка | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Ветки, стиль, тесты и требования к pull request. |
| Релизы | [docs/CHANGELOG.md](docs/CHANGELOG.md) | История изменений с версии 2.0. |

## Быстрый запуск через Docker

Docker Compose — основной способ запуска полного стека. Один общий образ содержит API, Telegram-бота, LLM-agent runtime, астрологический движок, palm/CV-модели, Mini App, admin-панель и public landing. Compose дополнительно запускает PostgreSQL + pgvector, Redis, Celery worker/Beat и Caddy.

```bash
cp .env.example .env
# Для Telegram-сценариев укажите BOT_TOKEN и ADMIN_ID.
# Для облачного LLM укажите OPENAI_API_KEY или ANTHROPIC_API_KEY.
make up
curl http://localhost:8080/api/health
```

Порты разработки по умолчанию — `8080` для HTTP и `8443` для HTTPS. Откройте `http://localhost:8080/?dev_user=<telegram_id>` только при `APP_ENV=dev` и `DEV_MODE=1`; этот режим отключает проверку Telegram-подписи и запрещён в production.[1]

Основные операции выполняются через Makefile:

```bash
make ps                         # состояние всех сервисов
make logs                       # общие логи API, бота, worker, Beat, Redis и PostgreSQL
make selfcheck                  # smoke-проверка из API-контейнера
make worker-scale N=3          # масштабировать только Celery worker
make down                      # остановить стек без удаления томов
```

Миграции PostgreSQL запускаются одноразовым сервисом `migrate` до API, бота, worker и Beat. Для локальной модели OpenAI-compatible используйте отдельный профиль после заполнения `CUSTOM_LLM_BASE_URL`, `CUSTOM_LLM_MODEL` и `CUSTOM_LLM_MODEL_LITE`:

```bash
make up-local-llm
```

Если Docker недоступен, приложение по-прежнему можно запускать вручную по старой схеме из [docs/README.md](docs/README.md), но при этом Celery/Redis и PostgreSQL придётся поднимать отдельно.

## Технологическая основа

| Слой | Реализация |
|---|---|
| Клиент | Telegram Mini App, Vanilla JavaScript, модульный CSS, Telegram WebApp API. |
| Сервер | Python, FastAPI, Pydantic, aiogram. |
| Хранилище | PostgreSQL + pgvector в Docker; SQLite/WAL остаётся fallback для offline/dev и тестов. |
| AI | Резервируемая цепочка custom / Anthropic / OpenAI и офлайн-ответы. |
| Инфраструктура | Docker Compose, Caddy, healthcheck, Sentry, PostgreSQL, Redis, Celery и encrypted backup-профиль. |

## Ключевые команды

```bash
pytest -q
python -m scripts.selfcheck
node --check miniapp/js/05-app.js
uvicorn app.api.main:app --port 8080
```

Подробнее о структуре, локальной разработке и production-релизах — в [документации проекта](docs/README.md).

## References

[1]: [app/api/main.py](app/api/main.py) — защита запуска от `DEV_MODE=1` вне `APP_ENV=dev`.
