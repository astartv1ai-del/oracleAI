# Staging-проверка миграции legacy-сообщений и индексов

**Дата проверки:** 2026-08-26
**Коммит кода до staging-проверки:** `279278f`
**Окружение:** локальный isolated staging, FastAPI/uvicorn, SQLite/WAL

## Ограничение стенда

В checkout не обнаружена реальная staging или production SQLite-копия. Поэтому проверка выполнена на изолированной staging-fixture базе, созданной из текущего DDL без доступа к production-данным. Стенд воспроизводим: 1 000 synthetic users, 1 800 threads, 70 000 messages, включая 10 000 legacy-сообщений с `thread_id IS NULL`.

Production-база не читалась и не изменялась.

## Запуск приложения

Приложение запущено с отдельным `DB_PATH`:

```bash
APP_ENV=dev DEV_MODE=1 \
DB_PATH=data/staging/oracle-staging.db \
uvicorn app.api.main:app --host 127.0.0.1 --port 8080
```

Startup прошёл успешно. В логах зафиксированы запуск migration chain, применение `2026_08_legacy_messages_to_default_threads`, создание/применение новых индексов, seed каталога и `Application startup complete`.

## Проверка результата миграции

| Метрика | Результат |
|---|---:|
| `messages.thread_id IS NULL` после запуска | `0` |
| Запись миграции в `migrations_applied` | `1` |
| Активные oracle-треды | `1 000` |
| Все активные треды | `2 000` |
| Новые индексы найдены | `5 из 5` |

Проверены индексы `idx_msg_user_id`, `idx_msg_user_thread_id`, `idx_msg_user_question_id`, `idx_thread_user_agent` и `idx_thread_user_recent`. Для пользователя с уже существующим oracle-тредом его `msg_count` стал `70`; для пользователя без oracle-треда был создан дефолтный тред и `msg_count` стал `10`.

## Database latency и query plans

Среднее время измерено после 20 warm-up запросов и 500 измерений для каждого запроса на каждой базе. `before` — идентичная fixture без startup-миграции и индексов; `after` — staging-база после запуска приложения.

| Запрос | Before, ms/query | After, ms/query | План после |
|---|---:|---:|---|
| Активные треды пользователя | 0.0507 | 0.0028 | `idx_thread_user_recent` |
| Сообщения конкретного треда | 1.2273 | 0.0208 | `idx_msg_thread` |
| Общая история пользователя | 1.1717 | 0.0217 | `idx_msg_user_id` |
| Подсчёт вопросов за период | 1.1576 | 0.0024 | covering `idx_msg_user` |
| Активный тред по агенту | 0.0323 | 0.0020 | `idx_thread_user_agent` |
| Последний вопрос пользователя | 1.2276 | 0.0019 | `idx_msg_user_question_id` |
| Аудит `thread_id IS NULL` | 1.1624 | 0.0015 | `idx_msg_user_thread_id` |

После миграции в проверенных планах исчезли полные table scans и временная сортировка для активных тредов, общей истории, поиска треда по агенту и последнего вопроса. История конкретного треда продолжила использовать существующий `idx_msg_thread`.

## HTTP smoke/performance

На запущенном staging FastAPI проверены 20 запросов каждого типа. Все ответы были `HTTP 200`.

| Endpoint | Среднее время | Максимальное время | Запросов |
|---|---:|---:|---:|
| `GET /api/health` | 14.547 ms | 16.046 ms | 20 |
| `GET /api/me?dev_user=1` | 2.950 ms | 3.885 ms | 20 |
| `GET /api/chat/oracle?dev_user=1` | 1.610 ms | 2.161 ms | 20 |

GET chat-history endpoint вернул мигрированный default thread с `thread_id=1`. LLM POST-flow намеренно не использовался в этом smoke-тесте: staging user был заполнен историческими вопросами, поэтому лимит платных вопросов уже исчерпан; это не должно превращаться в случайное списание или реальный внешний LLM-вызов во время проверки индексов.

## Тесты

Успешно выполнены:

```text
ruff check app/data/migrations.py app/data/schema.py tests/test_data.py tests/test_migrations.py
All checks passed!

python3 -m pytest -q
all tests passed
```

Дополнительно migration tests подтвердили reuse существующего треда, создание отсутствующего треда, пропуск orphan-сообщений, идемпотентность и single-owner поведение при двух одновременных подключениях.

## Воспроизводимость

Временные стендовые скрипты и raw-результаты оставлены в локальной папке `artifacts/` и не включены в Git-коммит, поскольку содержат synthetic staging data и отчёты конкретного запуска. Основной аудит этого прогона сохранён в этом документе.

## Итог

С точки зрения индексов и миграции staging-проверка успешна. Legacy-сообщения существующих пользователей были атомарно привязаны к активным default oracle threads, новые индексы применились на startup, API поднялся, HTTP history endpoint ответил успешно, а полный test suite не обнаружил регрессий.

Перед production rollout необходимо повторить этот же сценарий на защищённой копии реальной базы: сделать backup, проверить число legacy NULL-сообщений, измерить планы на фактическом объёме и только затем разрешить startup migration на production.

## References

[1]: ../../app/data/migrations.py — startup data migrations and legacy message migration.
[2]: ../../app/data/schema.py — messages/threads tables and new indexes.
[3]: ../../app/data/session.py — order `TABLES → reconcile_columns → INDEXES → migrations`.
[4]: ../../app/repo/dialog.py — thread lookup, message history and metadata maintenance.
[5]: ../../app/api/main.py — FastAPI lifecycle and startup logs.
