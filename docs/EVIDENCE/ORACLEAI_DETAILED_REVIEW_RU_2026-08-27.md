>
> **STATUS: HISTORICAL**
> **SUPERSEDED BY:** [`docs/RELEASE/CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md)
> **LAST VERIFIED:** 2026-08-27
> This file is retained as dated evidence or context. It is not the current source of truth.

# OracleAI — подробный технический разбор

**Дата анализа:** 26 августа 2026 года
**Репозиторий:** [`astartv1ai-del/oracleAI`](https://github.com/astartv1ai-del/oracleAI)
**Проанализированная ветка:** `master`
**Последний commit:** `bb84773` — `merge: integrate remote quality gates`
**Автор отчёта:** Manus AI

## 1. Executive summary

OracleAI — не просто Telegram-бот, а цельный продукт саморефлексии с двумя пользовательскими поверхностями: Telegram-ботом и Telegram Mini App. В проекте реализованы ежедневные ритуалы, AI-диалоги с несколькими проводниками, Таро, натальные расчёты, совместимость, транзиты, соляры, дневник, память, сканер ладони, тарифы, кристаллы, Telegram Stars, web-платежи, рефералы, рассылки, админ-панель и аналитика. Заявленная продуктовая рамка — бережное самопознание без медицинских, юридических, финансовых и категоричных предсказательных обещаний [1] [2].

По инженерной зрелости репозиторий заметно выше типичного MVP. Код разделён на API, бота, доменные сервисы, ядро расчётов и агентов, репозитории, миграции, frontend, инфраструктуру и тесты. В репозитории около 190 Python-файлов, 45 тестовых файлов, отдельные load/evaluation harnesses и подробный набор эксплуатационной документации. Архитектура последовательно использует SQLite/WAL, единые сервисы для бота и Mini App, серверную авторизацию Telegram, owner-scoped доступ к данным, idempotency для платежей и webhook, а также offline fallback для AI [3] [4].

Локальная проверка показала хорошее состояние baseline: синтаксис Python и JavaScript проходит, `ruff` не находит ошибок, `scripts.selfcheck` завершается успешно с ожидаемым пропуском live LLM и отсутствующими production credentials, `scripts.release_gate` проходит, `pip-audit` не обнаружил известных уязвимостей. HTTP smoke в dev-режиме подтвердил доступность публичных страниц, health endpoint, статических файлов и корректное отклонение защищённых API-запросов без Telegram-подписи.

При этом **проект ещё нельзя считать доказанно готовым к публичному production-запуску**. Самая существенная проблема — возрастной gate 16+ реализован в основном как клиентский overlay: просмотренные пользовательские API используют `current_user`, но не отдельную server-side проверку `age_confirmed`. Вторая важная проблема — в схеме новый пользователь получает `memory_enabled = 1`, что противоречит заявленному принципу opt-in памяти. Кроме того, deployment-документация содержит команду перехода на ветку `main`, тогда как в репозитории присутствует `master`; это способно сломать стандартный сценарий выкладки.

| Оценка области | Состояние | Комментарий |
|---|---|---|
| Архитектура | **Сильная** | Единый domain/service слой, понятные границы, отдельные repositories и contracts. |
| Backend | **Хорошая** | FastAPI, Pydantic, async SQLite, миграции, rate limits, ownership. |
| AI/safety | **Хорошая локально, неполная внешне** | Есть routing, evidence, guardrails и fallback; live provider QA остаётся gate. |
| Data integrity | **Хорошая** | Исправлена append-only история отчётов, платежи и ledger покрыты тестами. |
| Frontend | **Рабочий, но сложный в сопровождении** | Vanilla JS без bundler; порядок 20+ модулей является ручным контрактом. |
| Production readiness | **Частичная** | Локальные проверки зелёные, реальные Telegram/payment/backup/device gates не закрыты. |
| Главный риск | **Высокий** | Server-side enforcement 16+ и реальный memory opt-in требуют исправления до публичного запуска. |

## 2. Что представляет собой продукт

Продуктовая идея сформулирована аккуратно: помочь пользователю заметить состояние, сформулировать вопрос и выбрать один бережный следующий шаг. Астрология, Таро и AI используются как язык рефлексии, а не как источник гарантированного будущего. Основные проводники — Лилит для общего диалога, Урания для астрологии, Мадам Ленорман для карточных сценариев и Мира для visual evidence ладони [5].

Пользовательский цикл построен вокруг Mini App: экран «Сегодня», карта дня или ритуал, выбор проводника, диалог, интерпретация, сохранение мысли и добровольный возврат. Помимо основного чата, продуктовая поверхность включает профиль, память, дневник, лунный календарь, натальную карту, совместимость, Таро, palm flow, отчёты, тарифы и реферальную механику.

| Поверхность | Реализуемая задача | Основные backend-компоненты |
|---|---|---|
| Telegram bot | Онбординг, команды, уведомления, платежи, рассылки | `app/bot/`, `app/services/scheduler.py`, `app/services/broadcast.py` |
| Mini App | Сегодня, чат, агенты, профиль, продукты | `miniapp/`, `app/api/routers/` |
| AI-диалог | Вопрос, routing, tools, safety, история | `app/services/chat.py`, `app/core/agents/`, `app/core/agent.py` |
| Астрология | Natal, synastry, transit, composite, returns | `app/core/astro.py`, `chart_contract.py`, `chart_products.py` |
| Таро | Draw, replay, interpretation, outcome | `app/core/tarot.py`, `app/services/chat.py`, readings repository |
| Palm | Проверка снимка, evidence-наблюдения, ограничения | `app/api/routers/placements.py`, palm analysis modules |
| Память и дневник | Opt-in факты, diary, bounded context | `app/repo/dialog.py`, `app/core/skills.py`, `app/core/agents/runtime.py` |
| Commerce | Stars, Paddle, CryptoBot, entitlements, crystals | `app/services/billing.py`, `app/api/routers/webhooks.py` |
| Admin/ops | Контент, флаги, CRM, рассылки, audit | `admin/`, `app/api/routers/admin.py` |

## 3. Архитектура и структура репозитория

Архитектурно проект представляет собой единый Python-домен с двумя входами. Бот и FastAPI используют общие сервисы, правила лимитов, SQLite/WAL, AI runtime и safety boundaries. Это удачное решение: бизнес-правило не должно быть реализовано отдельно в Telegram handler и HTTP endpoint, иначе со временем появляются расхождения в списании, доступах и сохранении истории [3].

Поток запроса в Mini App выглядит так: Telegram WebView передаёт `initData`, frontend вызывает FastAPI, dependency проверяет Telegram-подпись и владельца ресурса, router валидирует payload через Pydantic, service/core выполняет доменную операцию, repository обращается к SQLite, а затем API возвращает contract-shaped JSON. API не должен принимать PII в URL, а общий history endpoint намеренно возвращает метаданные и action descriptors без полного текста личных записей [3] [6].

| Уровень | Назначение | Наблюдение |
|---|---|---|
| `app/api` | FastAPI app, dependencies, routers, contracts | Хорошо отделён транспортный слой. |
| `app/bot` | aiogram handlers, onboarding, shop, profile | Бот владеет polling, scheduler и broadcast loop. |
| `app/services` | Chat, billing, scheduler, analytics, referrals | Здесь сосредоточены основные use cases. |
| `app/core` | Astrology, agents, safety, LLM, tools, PDF/chart rendering | Самая крупная и доменно насыщенная зона. |
| `app/repo` | SQL access и преобразование строк БД | Owner-scoped queries и typed-ish mapping. |
| `app/data` | Schema, migrations, seed, DB sessions | Центральный источник DDL и миграций. |
| `miniapp` | Vanilla JS, CSS, images, static shell | Нет bundler; загрузка модулей ручная и упорядоченная. |
| `infra` | Docker Compose, Caddy, Dockerfile | Четыре runtime-сервиса. |
| `tests` | Unit/integration/regression/security tests | Покрыты деньги, safety, миграции, charts, API и frontend contracts. |
| `load`, `data/llm_eval` | Нагрузка и evaluation harness | Хорошая основа для дальнейшей внешней валидации. |

Frontend намеренно построен без bundler. `miniapp/index.html` подключает нумерованные JavaScript-модули, начиная с runtime и utilities и заканчивая actions/events. Такой подход минимизирует build-инфраструктуру и делает ассеты легко обозримыми, но переносит ответственность за порядок загрузки, глобальное состояние, совместимость имён и cache-busting на разработчика. При текущем размере Mini App это уже является заметным фактором стоимости сопровождения [7].

## 4. Backend, авторизация и privacy

Telegram-аутентификация реализована через проверку HMAC-подписи `initData`, ограничение размера и числа полей, проверку `auth_date`, запрет заметного будущего timestamp и защиту от duplicate keys. В production startup запрещается `DEV_MODE=1`; при этом отсутствие `BOT_TOKEN`, `ADMIN_ID` или HTTPS `WEBAPP_URL` блокирует запуск [8] [9].

Общие dependencies разделяют `current_user`, `active_user`, `touched_user` и `current_admin`. Персональные ресурсы получают пользователя из подписанной Telegram identity, а repositories должны дополнительно проверять ownership. Rate limiter в памяти процесса разделён на read/write/llm/admin buckets. Для одной API-инстанции и небольшого VPS это разумный компромисс, но при горизонтальном масштабировании потребуется внешний shared limiter, например Redis.

Память и личный контекст в runtime обрабатываются значительно лучше, чем в большинстве AI-MVP. `app/services/chat.py` передаёт memory context только при включённой настройке, `runtime.py` ограничивает history и context, tools проверяют privacy state, а отключение памяти блокирует чтение и ручное добавление фактов. Общая история также не превращает чаты и дневник в один большой raw-content dump [6] [10].

Однако есть существенное расхождение между документацией и кодом. В `users` поле `memory_enabled` имеет `DEFAULT 1`, а `users.ensure()` создаёт пользователя без явного значения этого поля. Следовательно, новый пользователь получает память включённой до отдельного выключения. Это противоречит формулировке «память включается только сознательным решением пользовательницы» и должно быть исправлено либо изменением default на `0`, либо явным consent-step до любого использования и сохранения памяти [2] [11].

Второе расхождение относится к возрастному ограничению. `age_confirmed` хранится на сервере и отображается через `/api/me`, а Mini App показывает overlay до основного onboarding. Но просмотренные chat, tarot, palm, profile, shop и другие пользовательские роутеры используют `Depends(current_user)`, а не dependency, проверяющую `age_confirmed`. Поэтому подписанный пользователь с `age_confirmed = 0` потенциально может напрямую вызвать API, минуя UI-overlay. Для 16+ safety boundary это недостаточно: проверка должна существовать на сервере в общем dependency или в чётко определённом наборе разрешённых pre-age endpoints.

| Контроль | Фактическое состояние | Оценка |
|---|---|---|
| Telegram HMAC | Реализован, включая freshness и duplicate-key rejection | Хорошо |
| Production `DEV_MODE` guard | Реализован на startup | Хорошо |
| Owner isolation | Реализуется через current user и repository queries | Хорошо, нужен внешний E2E |
| Memory-off runtime guard | Присутствует в chat/runtime/tools/diary | Хорошо |
| Memory opt-in по умолчанию | Не подтверждается: schema default равен `1` | **Исправить до запуска** |
| Server-side age gate | В просмотренных пользовательских API не найден общий guard | **Исправить до запуска** |
| Log redaction | Formatter маскирует email, секреты и числовые Telegram IDs | Хорошо |
| Admin access | Telegram identity + роль из БД + `admin_audit` | Хорошо, нужен реальный staging QA |

## 5. AI, safety и доменная корректность

AI runtime разделяет deterministic evidence, interpretation и варианты действия. Агент получает профиль, язык, bounded memory, chart/product evidence и разрешённые skills; LLM не должна вычислять эфемериды, карты или product contracts. При ошибках провайдера предусмотрена цепочка custom/Anthropic/OpenAI и offline fallback. Для crisis-классификации ответ создаётся без вызова модели и без списания лимита, что является правильным приоритетом для safety [3] [10].

В чате порядок операции также выбран корректно: проверка доступа, списание, сохранение вопроса, генерация ответа, сохранение ответа. Если генерация падает, выполняется refund. Для конкурентных запросов используется пользовательский lock; crystal balance списывается SQL-условием `crystals >= amount`, что защищает от типичной гонки двойного списания [10] [12].

Астрологическая часть оформлена как набор контрактов, а не как свободный текст модели. Exact-time и date-only режимы различаются; при неизвестном времени не должны появляться дома, ASC, MC и natal wheel. Отдельные JSON-first contracts для synastry, transit, composite и solar returns уменьшают риск смешения методологий и ложной точности.

Palm scanner построен как visual evidence flow: проверяются формат, размер и качество кадра, исходное фото не сохраняется, а результат должен ограничиваться видимыми признаками. Это хорошая safety-модель, но сама область остаётся чувствительной: `analysis_json`, fingerprint снимка и история чтений требуют формальной retention/deletion policy, полноценного malicious-upload тестирования и ручного UX review. В `docs/RELEASE/TASKS.md` эти пункты всё ещё отмечены как открытые [13].

## 6. Данные и целостность

Схема SQLite охватывает пользователей, threads/messages, memories, diary, forecasts, reports, tarot/palm readings, partners, practices, plans/products/orders/payments/entitlements, crystal ledger, referrals, analytics, LLM usage, safety events, scheduler leases, webhook events и административные сущности [14]. Для проекта такого масштаба это логичная доменная модель, хотя SQLite уже является архитектурным ограничением для будущего многорегионального или multi-instance сценария.

Сильным местом является исправление истории отчётов. Старый unique key вместе с `INSERT OR REPLACE` мог удалять старую версию при регенерации. Сейчас отчёты сохраняются append-only, выдаётся immutable `report_id`, а retrieval ограничен владельцем. Для legacy databases есть data migration и regression tests. Это хороший пример работы с реальным data-integrity инцидентом, а не только с happy path [15].

Миграции сериализуются через `BEGIN IMMEDIATE`, а порядок запуска разделён на таблицы, новые колонки и индексы. Такой порядок снижает риск, что старый production database сломается из-за индекса на ещё не добавленной колонке. При этом в документации правильно подчёркнуто, что SQLite backup нужно делать через SQLite-aware backup, а не произвольное копирование файла во время записи [4].

## 7. Commerce и webhook

Платёжная модель включает Telegram Stars для bot flow, Paddle для web checkout, CryptoBot для крипто-платежей, планы, товары, entitlements, crystals и ledger. Сначала создаётся pending order, затем провайдер возвращает payload, а фактическая выдача происходит после серверной верификации. Paddle webhook проверяет HMAC по raw body, возраст подписи, transaction ID, price ID, pending order и event type. Доступ открывается только для `transaction.completed`; повторное событие журналируется в `webhook_events` [16].

С точки зрения кода это сильная часть проекта. Тем не менее локальные тесты не равны provider certification. До запуска нужны реальные sandbox-сценарии: успешная оплата, duplicate webhook, out-of-order event, refund, chargeback, несовпадение цены, повторная доставка после временной ошибки и reconciliation с кабинетом провайдера. Сам проект это честно фиксирует как внешний gate, что лучше, чем объявлять платежный контур полностью готовым только на основании unit tests [13].

## 8. Инфраструктура и эксплуатация

Production Compose состоит из `bot`, `api`, `caddy` и `backup`. Bot и API делят именованный volume с SQLite, Caddy завершает TLS и проксирует трафик, backup создаёт SQLite snapshot, проверяет integrity, шифрует его через OpenSSL и может отправлять в S3-совместимое хранилище. Для API явно зафиксирован `--workers 1`, поскольку rate limiter и outbound bucket находятся в памяти процесса [17].

Основное эксплуатационное ограничение — backup container при старте выполняет `apk add --no-cache openssl sqlite s3cmd`. Это удобно для MVP, но менее воспроизводимо и менее безопасно, чем собственный versioned image с заранее установленными и зафиксированными пакетами. Дополнительно локальный volume `oracle_backups` сам по себе не является disaster recovery: off-site копирование, шифрование ключа, retention и реальный restore drill остаются обязательными операционными задачами.

В deployment-документации обнаружена конкретная ошибка: пример обновления выполняет `git checkout main`, тогда как текущий репозиторий содержит ветку `master`, а `origin/HEAD` указывает на `origin/master`. Для оператора, который следует инструкции буквально, команда завершится ошибкой. Следует либо унифицировать ветку на `main`, либо заменить инструкцию на `master`, либо рекомендовать только approved commit/tag. Сейчас tags отсутствуют, поэтому release pinning фактически опирается на commit hash [4].

## 9. Результаты локальных проверок

Проверки выполнялись после установки pinned dependencies из `requirements-dev.txt` и `requirements.txt`. Для сборки `pyswisseph` потребовались системные пакеты `build-essential`, `pkg-config`, `libsqlite3-dev` и `python3-dev`; это важно учитывать в CI и локальной документации.

| Проверка | Результат | Комментарий |
|---|---|---|
| `pytest -q` | **PASS по завершённому прогону** | Прогресс достиг 100%, сообщений об ошибках нет. |
| `python -m scripts.selfcheck` | **PASS** | Ожидаемо пропущены live LLM и production credentials. |
| `python -m compileall -q app scripts tests` | **PASS** | Python-файлы компилируются. |
| `node --check` для Mini App/admin JS | **PASS** | Синтаксических ошибок не найдено. |
| `ruff check app scripts tests` | **PASS** | Статический lint чистый. |
| `python -m scripts.release_gate` | **PASS** | Документы и статические product gates присутствуют. |
| `pip-audit -r requirements.txt` | **PASS** | Известные уязвимости не обнаружены. |
| HTTP smoke в dev | **PASS** | `/`, landing, privacy/terms, health, robots, sitemap и static вернули 200. |
| Защищённые API без initData | **PASS** | `/api/me`, `/api/agents`, `/api/chat/oracle` вернули 401. |
| Live LLM | **НЕ выполнялся** | Нужен staging/provider configuration и отдельная evaluation evidence. |
| Реальный Telegram device E2E | **НЕ выполнялся** | Внешний production gate. |
| Реальные платежи/refund/reconciliation | **НЕ выполнялись** | Нужен sandbox provider certification. |
| Реальный backup/restore drill | **НЕ выполнялся** | Требует disposable production-like host. |

Важно не смешивать зелёный локальный baseline с готовностью к launch. Сам проект корректно перечисляет незакрытые gates: signed-initData на реальном устройстве, live LLM grounding/safety evaluation, payment settlement/refund, backup/restore, независимое сравнение астрологических расчётов, лицензирование Swiss Ephemeris/Kerykeion, юридический review, browser E2E и визуальную матрицу PDF [13].

## 10. Приоритетные проблемы и рекомендации

### P0 — исправить до публичного запуска

| Приоритет | Проблема | Почему важно | Рекомендуемое действие |
|---|---|---|---|
| P0 | Server-side age gate отсутствует как общий enforcement | UI можно обойти прямым вызовом API; это нарушает заявленный 16+ boundary | Добавить `age_confirmed_user` dependency и подключить её ко всем обычным пользовательским read/write/LLM/product endpoints. Оставить до подтверждения только `/api/me`, `/api/profile` для согласия, health и минимально необходимые публичные routes. Добавить regression tests. |
| P0 | `memory_enabled` по умолчанию равен `1` | Пользователь получает память без явно подтверждённого opt-in | Изменить schema/migration default на `0`; существующих пользователей мигрировать по согласованной политике; добавить consent copy, audit event и tests на новый аккаунт. |
| P0 | Реальные Telegram/payment/restore gates не пройдены | Unit tests не подтверждают поведение внешних провайдеров и устройства | Поднять disposable staging, пройти signed-initData, sandbox payment, refund, duplicate webhook, backup/restore и real-device smoke с evidence. |

### P1 — исправить перед масштабированием

| Приоритет | Проблема | Почему важно | Рекомендуемое действие |
|---|---|---|---|
| P1 | Deployment docs используют `git checkout main` | Инструкция не соответствует фактической ветке `master` | Исправить docs, CI/release script и добавить test, проверяющий branch/ref instructions. |
| P1 | In-memory rate limits и outbound buckets | Несколько API-инстансов получают независимые лимиты; второй bot создаёт дубли рассылок | До масштабирования оставить один worker и явно enforce single-bot lease; затем вынести limiter/leases в Redis или другой shared store. |
| P1 | Vanilla JS без bundler при большом числе модулей | Ошибка порядка загрузки или stale asset может ломать весь Mini App | В краткосрочной перспективе добавить smoke import/load test и генерацию manifest; в среднесрочной — рассмотреть ES modules или Vite без потери CSP. |
| P1 | Live LLM latency выше продуктового target | Offline fallback безопасен, но ухудшает ценность и себестоимость живого опыта | Зафиксировать provider/model matrix, p50/p95, timeout budget, cost budget и quality score; измерять отдельно по agent, language и purpose. |
| P1 | Palm retention/deletion и hostile uploads ещё не закрыты полностью | Visual evidence и fingerprint могут быть чувствительным контекстом | Зафиксировать retention, delete semantics, max decoded size, MIME sniffing, decompression bomb protection, rate limits и UX states. |

### P2 — усилить качество и управляемость

Следует добавить полноценные browser/E2E сценарии для onboarding, age gate, memory-off, chat, natal, date-only, synastry, tarot, palm и paywall. Отдельно нужен manual accessibility review: keyboard navigation, focus management, screen readers, contrast, reduced motion и touch target sizes. В текущем виде статические checks и unit tests являются хорошей базой, но не доказывают реальный WebView UX.

Также полезно формализовать retention и deletion для `diary`, `messages`, `memories`, `safety_events`, `palm_readings` и `reports`. Поле `safety_events.excerpt` предназначено для операционного контроля, но должно иметь явную минимизацию, срок хранения, owner deletion policy и проверяемый redaction/retention contract.

Для production deployment стоит перейти от динамической установки пакетов в backup container к versioned image, добавить image scanning, SBOM, pinned base image digest и отдельную проверку прав на backup key. Для Git-процесса желательно выпускать подписанные tags/releases: сейчас публичных releases и tags нет, поэтому операционная воспроизводимость зависит от ручного выбора commit.

## 11. Что сделано особенно хорошо

Во-первых, проект серьёзно относится к границе между вычислимым фактом и AI-интерпретацией. Натальная карта, карточный расклад и product contracts строятся детерминированно, а модель получает evidence, а не право «додумывать» факты. Это существенно уменьшает риск hallucinated placements/cards и ложной точности.

Во-вторых, хорошо реализованы платежные и конкурентные инварианты: pending order до оплаты, idempotent payload, ledger для crystals, атомарное списание, user-level lock, refund при неудачной генерации и duplicate webhook journal. Для небольшого продукта это уже уровень, который обычно появляется только после реальных инцидентов.

В-третьих, документация не скрывает незакрытые внешние проверки. `docs/RELEASE/TASKS.md` и `docs/EVIDENCE/ORACLEAI_FINAL_AUDIT_2026-08-26.md` прямо отделяют local PASS от real-device, provider, payment, licensing, legal и restore evidence. Такая честность повышает доверие к baseline и облегчает дальнейшую работу команды.

Наконец, исправление append-only report history является сильным примером зрелой работы с данными. Проект не просто добавил новый endpoint, а исправил схему, миграцию, repository semantics, API retrieval, Mini App deep link и regression tests так, чтобы старая версия отчёта не исчезала при регенерации.

## 12. Итоговый вердикт

**OracleAI — функционально богатый и технически хорошо организованный продуктовый foundation, близкий к staging-ready, но не к доказанно production-ready.** Локальная инженерная база сильная: код импортируется, тесты и статические проверки проходят, критические домены имеют contracts и regression coverage, а инфраструктурная модель описана подробно.

Перед публичным запуском необходимо в первую очередь закрыть два несоответствия безопасности: сделать 16+ проверяемым на сервере и превратить память в настоящий opt-in с безопасным default. Затем нужно пройти внешние gates на реальном Telegram WebView, платежном sandbox, live LLM, backup/restore и визуальном UX. После этого проект можно рассматривать как кандидат на контролируемый beta launch с ограниченным числом пользователей и наблюдаемыми rollback-процедурами.

### Краткий порядок действий

1. Добавить server-side `age_confirmed` dependency и регрессионные тесты обхода UI.
2. Перевести `memory_enabled` в default `0`, мигрировать legacy-пользователей и проверить все memory paths.
3. Исправить `main`/`master` в deployment документации и закрепить release commit/tag.
4. Поднять staging с реальными Telegram signed-initData и пройти browser/device E2E.
5. Сертифицировать Paddle/CryptoBot/Stars sandbox, включая duplicate/refund/reconciliation.
6. Выполнить encrypted backup/restore drill на disposable host.
7. Провести live LLM safety/grounding/latency evaluation и зафиксировать p95 target.
8. Закрыть palm retention/upload policy, accessibility review и production visual matrix.

## References

[1]: https://github.com/astartv1ai-del/oracleAI/blob/master/README.md "OracleAI README — продукт, стек и запуск"

[2]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/PRODUCT.md "OracleAI Product — назначение, аудитория и privacy-принципы"

[3]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/ARCHITECTURE.md "OracleAI Architecture — топология и потоки данных"

[4]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/DEPLOYMENT.md "OracleAI Deployment — production-развёртывание и восстановление"

[5]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/FULL_PRODUCT_SURFACE.md "OracleAI Full Product Surface — карта пользовательских возможностей"

[6]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/routers/history.py "OracleAI history router — owner-scoped архив"

[7]: https://github.com/astartv1ai-del/oracleAI/blob/master/miniapp/index.html "OracleAI Mini App shell — порядок frontend-модулей"

[8]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/security.py "OracleAI Telegram initData verification"

[9]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/main.py "OracleAI FastAPI startup and production guards"

[10]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/services/chat.py "OracleAI chat service — safety, limits, refund and memory flow"

[11]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/data/pg_schema.py "OracleAI shared PostgreSQL schema rendering"

[12]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/repo/billing.py "OracleAI billing repository — orders, ledger and atomic spending"

[13]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/RELEASE/TASKS.md "OracleAI Tasks — local checks and open production gates"

[14]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/data/schema.py "OracleAI domain tables and indexes"

[15]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/EVIDENCE/ORACLEAI_FINAL_AUDIT_2026-08-26.md "OracleAI Final Audit — append-only reports and verification baseline"

[16]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/routers/webhooks.py "OracleAI payment webhooks — signatures and idempotency"

[17]: https://github.com/astartv1ai-del/oracleAI/blob/master/infra/docker-compose.yml "OracleAI Docker Compose — bot, API, Caddy and backup"
