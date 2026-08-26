# OracleAI — security-аудит и пошаговый план устранения рисков

**Дата статического анализа:** 26 августа 2026 года  
**Репозиторий:** [`astartv1ai-del/oracleAI`](https://github.com/astartv1ai-del/oracleAI)  
**Ветка/commit:** `master` / `bb84773`  
**Формат:** анализ исходного кода, конфигурации, тестов, Docker/CI и документации; без утверждения, что это полноценный penetration test.

## 1. Резюме

OracleAI имеет сильную локальную инженерную базу: Telegram `initData` проверяется через HMAC с ограничением срока действия, production startup запрещает небезопасный `DEV_MODE`, пользовательские ресурсы в основных repository-запросах ограничиваются `tg_id`, память имеет server-side guards, платежи используют pending orders и idempotent webhooks, а CI запускает pytest, ruff, compile checks, selfcheck, release gate и dependency audit [1] [2] [3] [4].

Тем не менее **публичный запуск следует отложить до закрытия P0-находок и прохождения внешних gates**. Наиболее важны два подтверждённых несоответствия: возрастное ограничение 16+ фактически не оформлено как единая серверная authorization boundary, а `memory_enabled` создаётся со значением по умолчанию `1`, хотя публичная политика обещает выключенную по умолчанию память и явный opt-in [5] [6] [7].

Дополнительные риски относятся к неполному anonymize, чрезмерно широкому доступу support к чувствительным данным, выдаче crisis excerpts роли `users:read`, Telegram HTML markup injection в bot-сообщениях, отсутствию явной pixel/body-защиты для изображений, открытым retention-политикам, плавающим Docker base images и незакрытым реальным Telegram/payment/backup E2E gates.

> **Вердикт:** текущий проект можно использовать как основу для закрытого staging или ограниченной внутренней альфа-проверки после исправления P0. Публичный beta/production запуск допустим только после повторного security regression run и подтверждения реальных внешних сценариев.

## 2. Baseline, который уже подтверждён

После установки системных build dependencies, необходимых для сборки `pyswisseph`, локально прошли `pytest -q`, `python -m compileall -q app scripts tests`, `node --check` для Mini App/admin JavaScript, `ruff check app scripts tests`, `python -m scripts.selfcheck`, `python -m scripts.release_gate` и `pip-audit -r requirements.txt`. Selfcheck пропускает live LLM и production credentials, поэтому эти результаты не следует трактовать как доказательство работы внешних провайдеров [8] [9].

HTTP smoke в dev-режиме подтвердил доступность Mini App shell, русской и английской landing-страниц, privacy/terms, robots/sitemap, static assets и `/api/health`. Запросы к `/api/me`, `/api/agents` и `/api/chat/oracle` без Telegram identity вернули `401`. Это подтверждает базовый fail-closed behavior для отсутствующей подписи, но не заменяет проверку реальным подписанным Telegram WebView.

| Область | Уже есть | Что ещё не доказано |
|---|---|---|
| Auth | HMAC, freshness, duplicate-field rejection, production guard | Реальный signed `initData`, replay/tamper/device E2E |
| Ownership | Repository queries с `tg_id` и owner-scoped history | Полная автоматическая IDOR-матрица для всех routes |
| Privacy | Memory-off checks, redacted logs, private share cache | Полный deletion/retention drill и legal data map |
| Commerce | Pending orders, atomic ledger, signature/idempotency tests | Sandbox settlement, refunds, chargebacks, reconciliation |
| AI safety | Classifier, crisis code path, deterministic evidence, fallback | Live providers, p95 latency и adversarial prompt/image evaluation |
| Operations | Docker Compose, Caddy, encrypted backup script | Реальный restore drill, image hardening, off-site recovery |

## 3. Приоритетная матрица находок

Оценка учитывает потенциальное влияние, эксплуатируемость и то, подтверждена ли проблема напрямую статическим анализом. **P0** означает блокер публичного запуска; **P1** — существенный риск, который нужно закрыть в том же release train; **P2** — важная hardening/операционная работа.

| ID | Риск | Приоритет | Уверенность | Основные места |
|---|---|---:|---:|---|
| SEC-01 | Нет общей server-side проверки `age_confirmed` для обычных API | **P0** | Высокая | `app/api/routers/*.py`, `app/api/deps.py` |
| SEC-02 | Память включена default `1` при обещанном opt-in | **P0** | Высокая | `app/data/schema.py`, `app/repo/users.py`, `web/privacy.html` |
| SEC-03 | `anonymize()` не очищает palm/events/safety и часть owner-linked следов | **P0/P1** | Высокая | `app/repo/users.py` |
| SEC-04 | Crisis excerpts доступны широким admin-ролям | **P1** | Высокая | `app/core/safety.py`, `app/repo/analytics.py`, `app/api/routers/admin.py` |
| SEC-05 | CRM user-card раскрывает слишком широкий набор данных support/read ролям | **P1** | Высокая | `app/repo/crm.py`, `app/repo/admin.py` |
| SEC-06 | Support имеет `grants`; refund защищён только этой permission | **P1** | Высокая | `app/repo/admin.py`, `app/api/routers/admin.py` |
| SEC-07 | Telegram HTML markup injection через пользовательские строки | **P1** | Высокая | `app/bot/main.py`, `app/bot/chat.py`, `app/bot/onboarding.py`, `app/bot/profile.py` |
| SEC-08 | Palm decode/body/pixel resource limits недостаточно независимы | **P1/P2** | Средняя/высокая | `app/api/routers/placements.py`, `app/core/palm.py`, `infra/Caddyfile` |
| SEC-09 | Birth city попадает в лог в открытом виде | **P1/P2** | Высокая | `app/core/geo.py`, `app/core/observability.py` |
| SEC-10 | Retention не охватывает safety/admin и зависит от scheduler | **P1/P2** | Высокая | `app/repo/analytics.py`, `app/services/scheduler.py` |
| SEC-11 | Плавающие Docker/OS dependencies и runtime `apk add` | **P1/P2** | Высокая | `infra/Dockerfile`, `infra/docker-compose.yml` |
| SEC-12 | Background tasks могут терять analytics/memory/audit при shutdown | **P2** | Средняя | `app/services/analytics.py`, `app/bot/main.py`, `app/repo/users.py` |
| SEC-13 | Deployment docs используют ветку `main`, текущий repo — `master` | **P1 operational** | Высокая | `docs/DEPLOYMENT.md`, Git refs |

## 4. Детальные находки и исправления

### SEC-01 — серверный age gate 16+

Mini App показывает age-gate и отправляет `age_confirmed` через `/api/profile`, но просмотренные обычные пользовательские routes получают только `Depends(current_user)`. В частности, chat, tarot, placements/palm, shop и другие surfaces не используют отдельную dependency, которая блокирует пользователя с `age_confirmed = 0`. Это означает, что клиентский overlay можно обойти прямым подписанным API-запросом [10] [11].

**Исправление.** В `app/api/deps.py` добавить dependency вида `confirmed_age_user`, которая после `current_user` проверяет `bool(user["age_confirmed"])` и возвращает контролируемый `403` с кодом, например `age_confirmation_required`. Затем подключить её ко всем обычным пользовательским endpoints. До подтверждения оставить только минимальный allowlist: `/api/me`, `POST/PATCH /api/profile` для записи подтверждения, возможно `GET /api/faq`, health и технически необходимые публичные routes. Не разрешать отрицательное подтверждение обходить состояние через другой route.

**Обязательные тесты.** Создать API regression matrix для чистого пользователя с валидной Telegram identity: каждый chat/tarot/palm/chart/shop/practice/report/share route должен вернуть `403`; `/api/me` и `POST /api/profile {age_confirmed:true}` должны работать; после подтверждения тот же запрос должен перейти к обычной авторизации/валидации. Добавить тест на попытку менять `age_confirmed` обратно в `false` и явно определить policy: блокировать доступ повторно или считать первое подтверждение необратимым до support review.

### SEC-02 — memory opt-in

В `users` поле `memory_enabled` объявлено как `INTEGER DEFAULT 1`, а `users.ensure()` не задаёт его явно. Значит, новый аккаунт получает memory-enabled state до отдельного действия пользователя. Это противоречит privacy policy, где сказано, что память выключена по умолчанию и включается явным действием [6] [7] [12].

**Исправление.** Изменить canonical schema и migration default на `0`. Для существующих пользователей не делать бездумный массовый перевод в `0` или `1`: принять продуктово-юридическое решение, зафиксировать его в migration note и, при необходимости, показать повторный consent prompt. Новый onboarding должен явно объяснять, что именно сохраняется, зачем это используется и как удалить факт. `memory_enabled=true` должен появляться только после явного server-side write.

**Обязательные тесты.** Проверить свежую регистрацию, отсутствие memory facts в `/api/me`, отсутствие вызова extraction task, отсутствие memory/diary context в agent runtime и блокировку ручного `POST /api/memories` до consent. Отдельно проверить миграцию legacy DB, выключение памяти после ранее сохранённых фактов и удаление конкретного факта.

### SEC-03 — неполная anonymize/deletion boundary

`users.anonymize()` очищает базовые профильные поля и удаляет messages, memories, diary, forecasts, tarot readings, partners, synastry cache, reports, threads и user notes. Однако статически видно, что она не затрагивает `palm_readings`, `events`, `safety_events`, платежные/заказные сущности, entitlements, crystal ledger и другие связанные записи [13] [14]. Сохранение минимального финансового следа может быть оправдано обязательствами по учёту, но это нельзя называть безусловным удалением всех материалов аккаунта.

**Исправление.** Составить data inventory с классификацией: удалить немедленно; обезличить; сохранить по законному основанию; сохранить только агрегат; удалить по retention expiry. Для `palm_readings` удалить `analysis_json`, fingerprint и строки либо перевести их в irreversibly anonymized aggregate. Для events/safety events удалить `tg_id`, excerpt и user-linked identity по истечении минимального safety/operational window. Для payments/orders оставить только минимальный legally required record с отдельной retention policy и без прямого пользовательского контекста.

**Обязательные тесты.** Завести fixture пользователя с данными во всех таблицах, выполнить anonymize дважды и проверить idempotency. Затем убедиться, что поиск, user-card, history, scheduler targets, safety admin view и все owner-scoped routes не возвращают удалённого пользователя. Для retained finance records проверить отсутствие имени, username, birth data, message text, memory, palm analysis и safety excerpt.

### SEC-04 — crisis excerpts и admin least privilege

`core/safety.py` сохраняет до 300 символов кризисного вопроса в `safety_events.excerpt`. `analytics_repo.safety_events()` отдаёт excerpt вместе с `tg_id`, категорией, действием, датой и именем. Endpoint `/api/admin/safety` защищён permission `users:read`, а эта permission присваивается не только owner/admin, но также analyst/support [15] [16]. Кризисный текст относится к особо чувствительному контексту и не должен быть доступен всем ролям, которые могут просматривать обычные CRM-метрики.

**Исправление.** Разделить endpoint на безопасную агрегированную статистику и отдельный restricted incident view. Для обычных ролей возвращать только category/action/count/day. Full excerpt заменить на минимизированный сигнал, хеш/incident ID или ограниченный ручной access для owner и специально назначенной safety role. Ввести audit на каждый просмотр crisis record, retention и redaction.

### SEC-05 — слишком широкая CRM-карточка

`crm.user_card()` одним ответом возвращает профиль, chart, notes, memories, threads, readings, reports, partners, orders, entitlements, crystal history, referrals и events. Это удобная CRM-модель, но она нарушает принцип минимально необходимого доступа: support-сотруднику для ответа на вопрос не требуется видеть всю память, карту рождения, платежи и реферальные данные одновременно [17].

**Исправление.** Разделить представления: `support_profile`, `support_conversation`, `billing_view`, `safety_view`, `owner_full_view`. Для каждого поля определить purpose, role, retention и masking. Память и diary-derived content выдавать только при отдельном праве и явной причине просмотра. Ввести audit reason или ticket ID для доступа к sensitive views; не передавать всё одним JSON payload в браузер админки.

### SEC-06 — separation of duties для grants/refunds

В `PERMISSIONS` роль `support` получает permission `grants`, а refund endpoint требует только `require("grants")`. Следовательно, support может вручную выдавать entitlements/crystals и инициировать refund Stars. Это не обязательно баг при сознательной политике продукта, но является избыточным финансовым полномочием для стандартной поддержки [15] [18].

**Исправление.** Убрать `grants` из support либо разделить `grant:nonfinancial`, `grant:financial`, `refund`. Refund и ручные начисления должны требовать owner/admin approval, reason, target, amount, idempotency key и audit. Для крупных или повторных операций добавить second approver. В админке показывать предупреждение о последствиях и блокировать повторное действие по тому же order/grant reference.

### SEC-07 — Telegram HTML markup injection

Глобально Bot настроен с `DefaultBotProperties(parse_mode=ParseMode.HTML)`. При этом пользовательские значения вставляются в сообщения без escape: имя и город в onboarding, имя в welcome/profile, oracle name и memory text в profile, а voice transcript echo отправляется как `<i>...</i>`. `_send_long()` отправляет AI output с тем же HTML default [19] [20] [21].

Это не browser JavaScript XSS, но это подтверждённая content-injection проблема в Telegram markup layer: пользователь может закрыть/испортить разметку, вставить разрешённые ссылки или визуально замаскировать текст; модельный output и malformed markup могут также приводить к ошибкам Telegram API.

**Исправление.** Ввести единый `html_escape()` через `html.escape()` и применять его ко всем пользовательским значениям. Сообщения, которые не требуют форматирования, отправлять с `parse_mode=None`. Для LLM output использовать либо plain text, либо строгий renderer, который разрешает только закрытые пары `<b>`/`<i>` без атрибутов и удаляет ссылки/остальные теги. Админские шаблоны должны иметь отдельный trusted-content path и не смешиваться с user content.

**Обязательные тесты.** Для name, city, oracle_name, memory, voice transcript, diary preview и AI answer использовать payloads `<b>`, `</i><a href="https://example.com">x</a>`, `&`, quotes и длинные строки. Проверить, что Telegram payload содержит экранированный текст или отсутствует parse mode, а trusted templates сохраняют только разрешённое форматирование.

### SEC-08 — image resource exhaustion и несогласованные лимиты

Palm endpoint проверяет MIME header и `Content-Length`, но если заголовок отсутствует, затем сразу читает `request.body()`. Далее Pillow выполняет verify, EXIF transpose и RGB conversion. Явного decoded pixel/dimension ceiling в `palm.py` не видно. Caddy ограничивает общий request body 2 MB, в то время как endpoint и core говорят о максимуме 8 MB, поэтому публичный путь и application contract расходятся [22] [23] [24].

**Исправление.** Добавить независимый ASGI/body limit с чтением чанками и немедленным отказом после лимита. До полного decode ограничить ширину, высоту и произведение пикселей; обработать `DecompressionBombWarning/Error`, truncated images и pathological EXIF. Установить единую policy: например, 8 MB end-to-end, если это действительно нужно, или 2 MB во всех слоях. Для каждого upload ввести rate limit, timeout, temporary-memory budget и negative tests.

### SEC-09 — birth city в логах

В `app/core/geo.py` логируются значения `city` при ошибке геокодирования и нераспознанном городе. Общий formatter маскирует email, секреты и числовые Telegram IDs, но не произвольные названия городов. Birth city является персональным контекстом профиля, поэтому текущий код не соответствует заявлению о whitelisted operational logs [25].

**Исправление.** Не писать исходное значение города в лог; использовать `city_key_hash`, длину, код результата и provider status. Если диагностика требует воспроизводимого ключа, применять keyed HMAC, а не обычный SHA-256 от небольшого словаря городов. Добавить тест formatter/geo logger, который убеждается, что «Казань» и произвольная строка не присутствуют в output.

### SEC-10 — retention и scheduler dependency

`prune_analytics()` удаляет только `events` и `llm_usage`. Из просмотренного кода нет аналогичной очистки для `safety_events`, `admin_audit`, user notes и других чувствительных таблиц. Analytics pruning вызывается через scheduler в конкретном daily window, поэтому при остановленном/зависшем bot process cleanup может не выполниться [26] [27].

**Исправление.** Создать retention matrix по типам данных и отдельную idempotent housekeeping job. Не связывать privacy deletion только с bot polling: запускать cleanup как отдельный controlled job или health-monitored scheduler task. Для каждой таблицы определить TTL, legal hold, deletion event, metrics и failure alert. Включить cleanup/retention в restore drill и privacy regression tests.

### SEC-11 — supply chain и container hardening

Основные образы указаны плавающими тегами `python:3.12-slim`, `caddy:2`, `alpine:3`; Dockerfile ставит OS-пакеты без digest pinning, а backup container при каждом запуске выполняет `apk add --no-cache openssl sqlite s3cmd`. Python dependencies version-pinned, но без hash lock. Non-root user в app image — сильное решение, однако оно не устраняет риск изменения upstream artifacts или непредсказуемой runtime-сборки [28] [29].

**Исправление.** Зафиксировать base images digest, собрать отдельный versioned backup image, включить SBOM и image vulnerability scan, добавить `pip --require-hashes` или lockfile с hashes, закрепить apt/apk repositories и периодически обновлять зависимости контролируемым PR. Установить read-only root filesystem там, где возможно, drop Linux capabilities, `no-new-privileges`, resource limits и отдельную network policy для backup.

### SEC-12 — graceful shutdown фоновых задач

Analytics, last-seen и memory extraction создаются как background tasks. Bot shutdown отменяет scheduler/broadcast и закрывает DB, но не видно общего drain для analytics/last_seen/memory extraction перед закрытием соединения. Это прежде всего риск потери operational/audit/consent telemetry, а не прямой exploit, но он усложняет расследования и может нарушить ожидаемую durability [30] [31].

**Исправление.** Ввести единый task registry для фоновых задач, остановку новых задач, bounded drain, запись shutdown metric и graceful timeout. Не удерживать пользовательский request бесконечно: для memory extraction допустим durable queue или повторяемая job-модель. Добавить test на SIGTERM-like shutdown с проверкой, что критические events и deletion markers сохранились.

### SEC-13 — deployment branch drift

Deployment guide содержит `git checkout main`, а текущий remote имеет `master` как HEAD и рабочую ветку. Это не классическая уязвимость, но может привести к выкладке несуществующей ветки или ручной ошибке в критическом процессе [4].

**Исправление.** Использовать approved commit/tag вместо branch-only deployment. Синхронизировать docs, CI и release script; добавить проверку, что указанный ref существует и совпадает с release manifest. Публиковать immutable release artifact и rollback target.

## 5. Пошаговый план до публичного запуска

### Шаг 0. Заморозить опасные изменения и создать security branch

Создать отдельную ветку remediation от текущего `bb84773`, зафиксировать baseline-команды и включить правило: ни одна новая feature не закрывает security finding без теста, traceability entry и rollback note. Не публиковать production credentials в issue, CI logs, screenshots или тестовых fixtures.

### Шаг 1. Закрыть identity/safety boundary

Сначала реализовать `confirmed_age_user`, подключить его к route registry и написать route matrix. Одновременно поменять memory default на `0`, обновить migration и onboarding copy. Это минимальный обязательный релизный блок, потому что он меняет реальный доступ и обработку личного контекста.

**Definition of done:** все обычные routes закрыты до age confirmation; новый пользователь не попадает в memory context; тесты проходят в чистой и legacy DB; `/api/me` выдаёт только минимальный pre-consent payload.

### Шаг 2. Перепроектировать deletion/retention contract

Составить таблицу данных: `users`, `messages`, `memories`, `diary`, `reports`, `tarot_readings`, `palm_readings`, `partners`, `synastry_cache`, `events`, `safety_events`, `orders`, `payments`, `entitlements`, `crystal_ledger`, `admin_audit`, backup copies. Для каждой категории определить delete/anonymize/retain basis и TTL. После этого переписать anonymize, cleanup jobs, privacy text и tests как единый contract.

**Definition of done:** fixture пользователя проверяет отсутствие остаточных personal artifacts; retained finance rows не содержат прямой identity/context; deletion повторяем, аудируется и не возвращает account в push/scheduler/CRM.

### Шаг 3. Ужесточить admin RBAC и data minimization

Разделить analyst, support, billing operator, safety reviewer, admin и owner. Убрать grants/refunds из обычного support, ограничить safety data, разрезать CRM card и добавить audit reason. Ввести deny-by-default для новых admin routes и отдельный тест, который перечисляет permissions каждой роли.

**Definition of done:** для каждой role есть allow/deny matrix; sensitive field access создаёт audit event; refund/grant не выполняются одним недостаточно привилегированным оператором; `/api/admin/safety` не отдаёт raw excerpt обычным ролям.

### Шаг 4. Закрыть content injection и upload hardening

Ввести shared escaping helpers для Telegram и frontend, удалить raw user data из HTML parse paths, добавить trusted template renderer и regression payloads. Для palm унифицировать лимиты Caddy/API/core, внедрить streaming body limit и pixel ceiling, проверить hostile JPEG/PNG/WebP fixtures.

**Definition of done:** markup payloadы отображаются как текст, trusted markup остаётся ограниченным; malformed/oversized/decompression-bomb files завершаются контролируемым 4xx без memory spike; ни один provider response/raw image не попадает в log/DB.

### Шаг 5. Устранить privacy leakage в logs и background durability

Убрать raw city и любые future sensitive fields из log messages, расширить redaction tests, добавить retention для safety/admin artifacts. Затем внедрить task drain и housekeeping health metric. Проверить, что при рестарте не теряются consent, deletion, payment audit и safety action events.

### Шаг 6. Укрепить supply chain и production image

Перейти на digest-pinned images, versioned backup image, hashed Python lock, SBOM и scan. Добавить container runtime hardening, resource limits, read-only filesystem, separate backup network policy и проверку прав backup key. Исправить branch drift и перейти на approved immutable commit/tag.

### Шаг 7. Пройти внешние release gates

Поднять disposable staging с production-like TLS, secrets management и off-site backup. Выполнить реальный Telegram Mini App flow: signed initData, expired/tampered data, age gate, memory consent, owner isolation и deletion. Затем пройти Paddle/CryptoBot/Stars sandbox: success, duplicate, out-of-order, wrong price/transaction, timeout, refund, chargeback and reconciliation. Выполнить restore drill и live LLM evaluation с adversarial safety/grounding cases.

### Шаг 8. Провести controlled beta и post-release monitoring

Начать с ограниченной аудитории, feature flags off для необязательных expensive paths, строгих rate/cost limits и ручного on-call. Ежедневно проверять auth failures, 4xx/5xx, LLM fallback/p95, webhook failures, backup freshness, safety events, deletion queue и unexpected admin actions. У beta должна быть заранее подготовленная rollback и incident procedure.

## 6. Минимальный security test plan

| Группа | Обязательные сценарии |
|---|---|
| Auth | Missing, expired, future, tampered, duplicate-key initData; wrong user; blocked/deleted user |
| Age | Every ordinary route before/after age confirmation; direct API bypass attempts |
| Memory | Default off; consent on/off; memory list/add/delete; runtime/tools/diary isolation |
| Deletion | Full fixture across all tables; repeated anonymize; post-delete login, CRM, scheduler, safety, history |
| Admin | Role matrix; safety excerpt denial; grants/refund separation; audit redaction and integrity |
| Telegram markup | Name, city, transcript, memory, diary, AI answer with tags/URLs/quotes/ampersands |
| Uploads | Missing Content-Length, over-limit body, wrong MIME, polyglot/truncated image, huge dimensions, malformed EXIF |
| Payments | Duplicate/out-of-order webhook, wrong event/status/id/price/order, replayed signature, refund retry |
| Logs | No city, name, question, diary, memory, initData, token, raw webhook, provider body or unredacted ID |
| Ops | SIGTERM drain, scheduler unavailable, migration rollback compatibility, encrypted backup and restore |
| Supply chain | Image scan, SBOM, digest verification, non-root/read-only runtime, dependency audit |

## 7. Go/no-go checklist

Публичный запуск следует считать **No-Go**, если хотя бы один из следующих пунктов не выполнен: server-side age gate; memory default/consent contract; deletion/retention contract; owner isolation regression matrix; restricted crisis/CRM admin access; markup and upload hardening; signed Telegram device E2E; payment sandbox/reconciliation; encrypted restore drill; live LLM safety/grounding evaluation; production secrets and image pinning; юридически проверенные privacy/terms/16+ тексты.

Запуск можно переводить в controlled beta, когда все P0 закрыты, P1 имеют подтверждённые тесты или формальный risk acceptance владельца, а external gates имеют сохранённые evidence artifacts. Полноценный public production требует также ручного accessibility/visual review, independent astrology-calculator comparison, licensing confirmation и наблюдаемого rollback procedure [32].

## References

[1]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/security.py "Telegram initData verification"

[2]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/main.py "FastAPI production startup guards"

[3]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/deps.py "Authentication, ownership and rate limiting dependencies"

[4]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/DEPLOYMENT.md "Deployment and recovery guide"

[5]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/routers/chat.py "Chat API routes"

[6]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/data/schema.py "Canonical SQLite schema"

[7]: https://github.com/astartv1ai-del/oracleAI/blob/master/web/privacy.html "Public privacy policy"

[8]: https://github.com/astartv1ai-del/oracleAI/blob/master/.github/workflows/ci.yml "CI quality and security checks"

[9]: https://github.com/astartv1ai-del/oracleAI/blob/master/docs/TASKS.md "Local checks and open external gates"

[10]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/routers/profile.py "Profile, age confirmation and memory API"

[11]: https://github.com/astartv1ai-del/oracleAI/blob/master/miniapp/js/05-app.js "Mini App age-gate and bootstrap"

[12]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/repo/users.py "User creation and anonymization"

[13]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/repo/users.py "Anonymize implementation"

[14]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/data/schema.py "Owner-linked data tables"

[15]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/repo/admin.py "Admin roles and permissions"

[16]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/routers/admin.py "Admin API, safety and financial operations"

[17]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/repo/crm.py "CRM user-card payload"

[18]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/services/telegram.py "Telegram API client and support messaging"

[19]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/bot/main.py "Global Telegram HTML parse mode"

[20]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/bot/chat.py "Chat and transcript message rendering"

[21]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/bot/onboarding.py "Onboarding user-input rendering"

[22]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/api/routers/placements.py "Palm upload endpoint"

[23]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/core/palm.py "Palm image validation and decode"

[24]: https://github.com/astartv1ai-del/oracleAI/blob/master/infra/Caddyfile "Caddy request-body limits"

[25]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/core/geo.py "Geocoding and raw city logging"

[26]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/repo/analytics.py "Analytics pruning and safety events"

[27]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/services/scheduler.py "Scheduler lease and housekeeping execution"

[28]: https://github.com/astartv1ai-del/oracleAI/blob/master/infra/Dockerfile "Application image build"

[29]: https://github.com/astartv1ai-del/oracleAI/blob/master/infra/docker-compose.yml "Production services and backup container"

[30]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/services/analytics.py "Background analytics tasks"

[31]: https://github.com/astartv1ai-del/oracleAI/blob/master/app/bot/main.py "Bot shutdown lifecycle"

[32]: https://github.com/astartv1ai-del/oracleAI/blob/master/ORACLEAI_FINAL_AUDIT.md "Published audit and remaining production gates"
