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

## Быстрый запуск

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# В отдельном терминале: Telegram-бот
python -m app.bot.main

# В отдельном терминале: FastAPI, Mini App и публичный лендинг
APP_ENV=dev DEV_MODE=1 uvicorn app.api.main:app --host 127.0.0.1 --port 8080
```

Откройте `http://127.0.0.1:8080/?dev_user=<telegram_id>` только в локальном режиме разработки. Значение `DEV_MODE=1` запрещено в production, поскольку оно отключает проверку Telegram-подписи.[1]

## Технологическая основа

| Слой | Реализация |
|---|---|
| Клиент | Telegram Mini App, Vanilla JavaScript, модульный CSS, Telegram WebApp API. |
| Сервер | Python, FastAPI, Pydantic, aiogram. |
| Хранилище | SQLite в WAL-режиме, схема и обратимые миграции. |
| AI | Резервируемая цепочка custom / Anthropic / OpenAI и офлайн-ответы. |
| Инфраструктура | Docker Compose, Caddy, healthcheck, Sentry и резервное копирование. |

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
