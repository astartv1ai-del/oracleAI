# ORACLEAI — Список слабых мест (аудит 50–200)

Параллельный read-only аудит кода (без live-эксплуатации). ~80 находок, ранжировано по
влиянию. Обозначения: 🔴 critical · 🟠 high · 🟡 medium · 🔵 low · ⚪ cosmetic.
[effort] quick / medium / large.

---

## 1. БЕЗОПАСНОСТЬ (OWASP)

### 🔴 1.1 Вебхук-идемпотентность fail-open на двойное начисление
`app/api/routers/webhooks.py:110` `_already_seen()` при сбое журнала возвращает `False` и
помечает "лучше обработать дважды, чем потерять оплату". При транзиентном сбое БД каждый
повтор провайдера может двойно выдать подписку/кристаллы. Нужен второй idempotency-гейт в
`apply_payment`: условный `UPDATE ... SET status='paid' WHERE status='pending'` (TOCTOU
между проверкой и выдачей сейчас закрыт только журналом). [large]

### 🔴 1.2 Missing DB-пул в API-процессе
`app/api/deps.py:19-24` глобальный `_db`, одно соединение Postgres на процесс. При
нагрузке все запросы сериализуются на одном соединении; медленный запрос стопорит весь web.
Нужен пул + checkout на запрос. (Также `pool_recycle` не задан — долгоживущие asyncpg-конны
за PgBouncer/NAT протухают молча, `postgres.py:165`.) [medium]

### 🟠 1.3 XSS через `esc()` без экранирования одинарных кавычек
`miniapp/js/01-utils.js:116` `esc()` покрывает `& < > "`, не `'` — опасно в атрибут-контекстах
(`onclick='...${x}'`). 48 сайтов `innerHTML`,392 `esc()`; проверить динамические в
07-chat.js,12-misc.js,17-payments.js. Нет санитайзера для будущих тегов. [medium]

### 🟠 1.4 Rate-limit: очистка всего состояния разом
`app/services/rate_limit.py:44` и `app/bot/main.py:56-72`: при `len>50k/20k` делают
`self._hits.clear()` — стирают ВСЕ окна всех клиентов за один приём. Атакующий, отправив скачок
уникальных ключей, сбрасывает лимиты всем (каждый получает свежее полное окно). Заменить на
LRU-эвикцию старых записей, не clear-all. [medium]

### 🟠 1.5 `RATE_LIMIT_BACKEND=memory` по умолчанию в проде
`app/config.py` дефолт `memory` + fail-open в `allow()` (rate_limit.py:114). Мульти-воркер →
каждый своё окно → лимит ×N; сбой Redis молча сдаётся к свежему MemoryLimiter.
Продакшн не проверяет, что задан Redis (только CELERY проверяет REDIS_URL). [medium]

### 🟠 1.6 Кризис-фильтр обходится: homoglyph/emoji/translit/не-RU-EN
`app/core/safety.py` локальный regex-список; `_squash` ловит разрядку, но НЕ ловит:
emoji между буквами (нет в `_SEPARATORS`), англ. парафразы (маленький список), голосовые
(проверить путь транскрипции через `classify`). Пропуск = платящий юзер в кризисе получает
фатальный прогноз. Фолбэк: лёгкий LLM-перепроверка на SOFTEN/подозрительных. [medium]

### 🟡 1.7 Redis-рейс на первом хите rate-limit
`rate_limit.py` RedisLimiter: `INCR`/`TTL` затем `EXPIRE` отдельными round-trip'ами; два
параллельных first-hit могут оба увидеть `count==1`. Атомно: `SET key1 EX window NX`+`INCR`. [quick]

### 🟡 1.8 initData нет revoke/сессии; окно 24ч
`app/api/security.py` HMAC-проверка образцовая, но утёкший initData валиден до 24ч без
server-side kill-switch. Премиум: персистить `auth_date`/id сессии, дать per-user инвалидацию. [medium]

### 🟡 1.9 F-string SQL по колонкам (сейчас безопасно, но хрупко)
`app/repo/users.py:80,218,234`, `billing.py:70,108`, `content.py:197,266`, `comms.py:172`.
`{keys}` строятся из allowlist — не инъектится, но один рефактор от дыры. Нужен комментарий-invariant
и переход на ORM/native pg. [quick]

### ✅ 1.10 SQLite→Postgres шайм `_translate_sql` — УСТРАНЕНО (DB-001 close-out, 2026-08-30)
Шайм, `_ID_TABLES` и `_INSERT_TABLE_RE` удалены из `app/data/postgres.py`; все репозитории
переведены на native PostgreSQL dialect. См. [ADR-0003](ADR/ADR-0003-shim-removal.md).

### 🟡 1.11 `settings.ready` не блокирует старт
`app/config.py:173`: нет `BOT_TOKEN`/`ADMIN_ID` — только печать. Вебхуки fail-closed (хорошо),
но бот-мисконфиг всплывает только в рантайме. Fail-fast на старте. [quick]

### 🟡 1.12 Collation эскапед в Postgres
`users.py:316` и др. `COLLATE NOCASE`/`COLLATE` не переведены шаймом → runtime-сбой в CRM-поиске
только на Postgres (SQLite-тесты не ловят). Покрыть Postgres-путь тестами. [medium]

### 🟡 1.13 ВременнЫе метки строкой, а не timestamptz
`repo/analytics.py:195` лексикография ISO-строк `created_at < ?`, полный scan на аналитике,
нет типа `timestamptz`/индексов выражений. Работает, пока ровный формат; любая кривая запись
ломает сравнение. [medium]

### 🔵 1.14 Докторские endpoints/docs в dev
`app/api/main.py:101` ок, app_mode gate есть; но `?dev_user=<id>` и /docs живут по dev_mode.
Выключить /docs-redoc по умолчанию, не привязывая только к dev_mode. [quick]

### 🔵 1.15 `_RateLimit.acquire` busy-poll 50ms
`llm.py:126` крутит цикл при насышенном 240/мин бюджете (утренняя рассылка). `asyncio.Event`
на near-deadline или расчёт сна до следующего слота. [quick]

---

## 2. КРИПТА / МОНЕТИЗАЦИЯ

### 🟠 2.1 Stars-платёж не сверяется с ценой плана
`app/bot/shop.py:275-281`, `repo/billing.py:148`: `mark_order_paid` берёт `total_amount`
без проверки `>= order.amount_stars`. Если цена сменилась между инвойсом и оплатой, или дубль
payload после pre_checkout race — грант полного права без сверки. Явно сверять сумму. [medium]

### 🟠 2.2 Referral: циклы и self-referral не блокируются
`referrals` UNIQUE `(referrer_id, invitee_id, level)`, но нет `referrer != invitee` и cycle guard.
A→B и B→A — отдельные строки; два аккаунта = пользователь сам себе реферер, level-2 бонус
выплачивается. Инвариант документирован "одной транзакцией", но не enforced. [medium]

### 🟡 2.3 Grantly-награда рефералу один раз — только process-local lock
`app/services/referrals.py`: нет DB-уникальности/флага «бонус-раз», lock'и процесса-локальны.
Мульти-воркер/ячейка может дать бонус дважды. Сделать DB-констрейнт. [medium]

### 🟡 2.4 Cryptobot webhook-реплей: проверить event_id dedup
`webhooks.py:233+`: signature-путь лукает, dedup через `webhook_events` — убедиться, что он
покрывает провайдера cryptobot и есть проверка на replay того же события. [quick]

### 🟡 2.5 Нет дневного spend-потолка на LLM для платящих
В `app/services/limits.py`/`rate_limit.py` только request-лимиты (`llm=(12,60)`), нет дневного
USD-потолка на юзера на уровне сервиса. Абьюзер на 12 req/min × tool-циклы жжёт деньги.
Добавить per-user daily token/cost gate перед `agent_core`. [medium]

### 🔵 2.6 `llm_usage` наблюдается, но не на дашборде
`app/core/llm.py` стоимость на вызов с бюджетом — отлично; вывести в админ-дашборд как премиум-фичу
unit-economics, не только телеметрию. [quick]

---

## 3. ДАННЫЕ / ДОСТУП

### 🟠 3.1 Пул `_db` (см. 1.2) — бутылочное горло пропускной, влияет доступ
Дублируем фиксацию: глобальный синглтон-конна в `app/api/deps.py:19` — под нагрузкой сериализация.
[— дубликат 1.2 —]

### 🟠 3.2 Referral-циклы (см. 2.2) — пересечение данных
[— дубликат 2.2 —]

### 🟡 3.3 Память юзера — cross-user side-channel через промпт?
`app/core/memory.py` выделяет факты по `tg_id`; проверить, что `_context` берёт только
текущего `tg_id` (readings, diary, chat history), нет ли общей ключевой базы на недавние
записи без разграничения. Аудит scope всех `repo/*` по `id=? AND tg_id=?` — сейчас IDOR-прочно. [medium]

### 🟡 3.4 Аналитика и логи без отбора PII
`app/core/{log_stream,observability,sentry}.py`, `repo/analytics.py` — лог секретов/токенов/сырых
сообщений пользователей, данные хранятся без срока жизни, нет маскирования initData/token.
Добавить scrubbing перед логированием + retention lifecycle. [medium]

### 🔵 3.5 GDPR-анонимизация есть (сильно), проверить сторонние пути
`users.anonymize` с accounting-трейсом — отлично; распространить на palm-аватары/object-storage
retention (P2-005 в release-gates). [medium]

### 🔵 3.6 Клиент хранит секреты в localStorage/Telegram Storage
`miniapp/js/03-data.js` — проверить, что initData/токены не пишутся в localStorage без
необходимости; Telegram Storage предпочтителен. [quick]

---

## 4. ИНФРА / ДЕПЛОЙ

### 🟠 4.1 Валидация окружения не блокирует прогон тестов
`requirements.txt` пинит версии, но локальный env без них; нет Makefile-таргета, проверяющего
env-vs-requirements перед pytest — так 36 collection-errors прорвались незамеченными
(тест-сьют ПЕРЕЗАПУЩЕН и не мо 0 тестов). [medium]

### 🟠 4.2 Тест-сьют сломан в dev: `pyswisseph` не установлен
`app/core/vedic.py:12` импортирует `swisseph` на import-time; ~36 модулей зависят транзитивно.
Релейс-гейт "лок G27" сейчас невыполним локально. `pip install pyswisseph` или ленивый импорт. [quick]

### 🟠 4.3 `.env` содержит `PADDLE_WEBHOOK_SECRET=` пустым
`webhooks.py:150` `verify_paddle` + replay-аware `_parse_signature` верны, но при пустом
секрете поведение на старте должно быть fail-closed. Проверить, что пустой секрет не
no-ops-разрешает платёж (иначе forgeable до настройки). [quick]

### 🟡 4.4 Статичный `web/robots.txt` и `sitemap.xml` — битые мёртвые копии
Сервер генерирует оба динамически (`main.py:313-332`); статичные содержат заглушку
`https://oracle-bot.example` и отдаются по `/public/robots.txt`. Удалить файлы. [quick]

### 🟡 4.5 `/public/*` отдаёт сырые шаблоны с неподнятым плейсхолдером
`/public/landing.html` возвращает страницу с литеральным `__PUBLIC_BASE_URL__` в canonical/hreflang.
Монтировать только `landing.css`, не web целиком. [quick]

### 🟡 4.6 Метаграции на boot без атомарности
Alembic-миграции запускаются на старте без блокировки/проверки (upgrade head в Makefile).
Добавить idempotent-обёртку, запрет на root-контейнер, healthcheck. [medium]

### 🟡 4.7 HSTS без `preload`
Caddyfile `max-age=31536000; includeSubDomains` — добавить `preload` и отправку в preload-list
для премиум-домена. [quick]

### 🔵 4.8 Зависимости — проверить CVE-флаги
`requirements.txt` пинится точно (хорошо); прогнать OSV-скан на предмет известных уязвимостей
в текущих версиях. [quick]

### 🔵 4.9 Бэкап-стратегия упомянута в release-gates, но не в инфраструктуре
P0-004 «production backup/restore + rollback» — проверить, что реально настроены бэкапы Postgres
и восстановление, а не только таск в списке. [large]

### 🔵 4.10 `lilith-sil.png` 307КБ + img/ =8.3МБ (см. 5.x — переносим сюда перф-под)
WebP/AVIF: сократит ~10x и ускорит Mini App. [quick]

---

## 5. ТЕХНИКА / LLM-ДВИЖОК / ПРОИЗВОДИТЕЛЬНОСТЬ

### 🟠 5.1 `file_loader.load_profiles()` ре-читает YAML с диска на каждый запрос
`app/core/agents/file_loader.py:181-190` ходит по всем agent-дирам и парсит SKILL.md/front-matter
БЕЗ кэша, вызывается из `skill_context()`/`activate_skill` (каждый chat/report/tool-call).
При ~10k пользователей платим реюз ре-парс 4 профилей. Кэшировать по mtime файла. [quick]

### 🟠 5.2 Prompt-cache шлют весь system-блок на каждый запрос
`llm.py:436-437` один `cache_control` breakpoint на ВЕСЬ system, а system содержит per-user
volatile память/наталь/контекст → hits почти не бывает, платим полный ре-промпт за статичный
identity+protocol каждый раз. Сплит статичного префикса в кэшируемый block / второй breakpoint. [medium]

### 🟠 5.3 Ungrounded на платных отчётах: `build_report`/`daily_forecast` слабейшие гейты
`agent.py:772-783` `build_report` — только `validate_nonfatal_text`, без section-coverage/retry;
`daily_forecast` (`agent.py:212-215`) — только `if text.strip()`. Тогда как natal-гейт —
полный цикл retry с фидбеком (`agent.py:634-655`). Самые дорогие выходы (solar/monthly/returns)
защищены слабее всего. [large]

### 🟠 5.4 Chat-гейт одноразовый и поверхностный
`agents/runtime.py:174-183` `validate_nonfatal_text` + MIN_ANSWER_LEN=120, одна попытка, жёсткий
offline-fallback. Не использует богатые `validate_*_text` каналов; порог 120 откидывает
легитимно-краткие ответы в шаблон. [medium]

### 🟡 5.5 Контент-слой — некэшированные N+1 DB на запрос
`repo/content.py` `get_text/get_content/get_setting` — сырой SQL без кэша; один `system_for` =
6-8 запросов (agent, persona, billing×2, skills, context) до самого LLM. Админ-редактируемость
оправдывает короткий TTL-кэш, не per-request reads. [medium]

### 🟡 5.6 Память: полный O(n) скан на каждую запись
`memory.py:248-269` `_find_exact` грузит ВСЕ строки и ком	парит `dedup_key`; `_find_similar`
грузит все embedding с косин-сканированием без LIMIT; `_insert` эмбедит per row. Нет
CANDIDATE-окна в dedup (в recall есть`CANDIDATE_POOL=300`). [medium]

### 🟡 5.7 Unbounded in-memory кэши с декларированным, но не заданным кэпом
`memory.py:52` `RECALL_CACHE_MAX=512` не применяется — `_recall_cache` не прунится по TTL;
`agent.py:150` лимит 5000, но сами лимиты масштабируются ре-сканированием при росте.
Мелкие, но реальные утечки. [quick]

### 🟡 5.8 Двойная система свайпов в Mini App (мёртвый/конфликтующий код)
`miniapp/js/05-app.js:100-140` старая touch-система, `14-gestures.js:14-106` новая Pointer Events;
guard только у новой, обе висят на документе → двойные `cycleAgent`, разный порядок навигации
(старый home→hub→profile vs новый +payment). `initSwipe` из boot цепляет одну из двух — состояние
неоднозначно. Удалить одну. [medium]

### 🔵 5.9 Failover-latency: RETRIES=2 + фолбэк ≈ до 36с при деградации
`config.py:140-161` provider chain корректен (бюджет останавливает retry-жор), но офлайн-ответ
меняет качество на латентность сознательно. Задокументировать. [quick]

### 🔵 5.10 Дублирование нумерации файлов миниаппа
Два `13-*`, два `14-*`, два `16-*`, два `18-*` (css) — хрупкая сборка regex-конкатенацией
(`build_frontend.mjs`); любое `?v=` ломает discovery. [quick]

### 🔵 5.11 Ретейншн-цифры privacy без оговорки/юр. сверки (см. 4 линк)
Системная. [см. веб-секция]

---

## 6. ПУБЛИЧНЫЙ САЙТ (WEB)

### 🟡 6.1 Нет favicon на лендинге/legal
`web/*.html` нет `link rel=icon`; `/favicon.ico` →404 (`main.py:367` ищет в miniapp/, там только
`favicon.svg`). Голый таб. Готов `miniapp/img/favicon.svg` — 1 строка в head. [quick]

### 🟡 6.2 Нет `twitter:card`
X/Twitter previews без карточки; Telegram доволен og:. Добавить summary_large_image + методы. [quick]

### 🟡 6.3 Sitemap рекламирует `/` (Mini App shell) с priority 1.0
`main.py:320-332` кладёт `/` первым — краулер получает JS-заглушку с initData. Убрать `/` из
sitemap или redirect `/`→`/landing` для не-Telegram. [quick]

### 🟡 6.4 `og:image` — лого, не карточка
`landing.html:18` на `/static/img/oracle-mark.png` (34px), при готовой `miniapp/img/og-card.jpg`.
Нет og:image:width/height/alt. [quick]

### 🟡 6.5 RU/EN privacy расходятся по существу
RU §7 заявляет сроки 120/90/180/365; EN §7 — «must be confirmed before launch». Юр. версии
одного документа не совпадают. Привести к одному. [medium]

### 🟡 6.6 Cache-Control нет для `/public/landing.css`
`_cache_control` (main.py:212-226) знает `/static/`, `/admin/static/`, про `/public/` нет —
CSS лендинга перекачивается каждый визит. Добавить ветку `elif` с max-age. [quick]

### 🔵 6.7 404 публичного сайта — голый текст
`main.py:308` `HTMLResponse("Страница не найдена",404)` без стилей/бренда. Брендированная
страница-заглушка. [quick]

### 🔵 6.8 Legal-страницы без og/canonical; JSON-LD тонкий
privacy/terms шерится голо, RU/EN duplicate без canonical; SoftwareApplication price:0 без
author/url/rating. Шаблонизируемый head. [medium]

### 🔵 6.9 `t.me/oracle_ai_bot` захардкожен в 8 местах (2 лендинга × CTA+footer)
Смена юзернейма = правка 8 строк/4 языка. [quick]

### 🔵 6.10 404 публичного сайта см. 6.7; HSTS preload см. 4.7
—

---

## 7. МИНИАПП (UI) — постранично

### ПАКЕТСТЬ: 19 `<script>` без `type=module`, глобальный `app`, нумерация сломана
`index.html:48-66` конкатенация regex'ом; 3/4 кода пишет напрямую `app.me/app.view` в обход
"app.state". [см. 5.8/5.10]

### 🟠 7.1 Нет BackButton/popstate
`grep BackButton|history` — 0. Android hardware back закроет Mini App целиком из чата/модалки;
свайп есть, системной навигации нет. Внедрить `tg().BackButton.onClick`. [medium]

### 🟡 7.2 Мёртвый/конфликтующий двойной свайп (см. 5.8)
—

### 🟡 7.3 Нет loading/empty/error состояний на страницах
home/chat/tarot и др. — данные грузятся без скелетонов; сбой fetch → тихий пустой экран без
retry. Добавить состояния на каждую страницу. [medium]

### 🟡 7.4 XSS-поверхность `innerHTML` без `esc()` (см. 1.3) — особенно 07-chat dynamic
—

### 🟡 7.5 Платёжный флоу: нет явного статуса «платим/успех/ошибка», double-tap дублирует заказ
`17-payments.js` — заблокировать кнопку на время запроса, показать спиннер, обработать
already-paid payload без ошибки (см. S4 в боt). [medium]

### 🟡 7.6 Изображения без lazy-load и в не-современном формате
`lilith-sil.png` 307КБ eager на каждого экране; card-face/og-card крупные; img/ 8.3МБ.
WebP/AVIF + `loading=lazy` + `width/height` против CLS. [quick]

### ❓ 7.7 Остальные страницы: детали не извлечены (агент вернул частично)
Требуется live-проверка каждой вьюхи в браузере.

---

## 8. ТЕЛЕГРАМ-БОТ (UX)

### 🟠 8.1 Глобальный throttle ест сообщения И тапы без фидбека
`main.py:56-76` ThrottleMiddleware `interval=1.2s` по юзеру на ВСЕ типы событий, возвращает `None`
(дроп). Тап→ввод в 1.2с: текст молча выброшен, перепечатка снова в окне → выглядит сломанным.
Также режется `callback_query` — кнопка «Ask»+starter, double-tap расклада молчит без `answer()`/
toast. Окно охватывает типы (callback→text) — вопрос после открытия меню агента теряется. [medium]

### 🟠 8.2 Неизвестные `/commands` молча игнорируются
`chat.py:230` `any_text` исключает `startswith("/")`, нет fallback-хендлера. `/proma `/prediction`
→ бот молчит. Добавить catch-all «не знаю такую команду, вот меню». [quick]

### 🟠 8.3 Пречекаут «заказ уже оплачен» отклоняет легитимный повтор
`shop.py:269-271` если Telegram повторно доставляет оплаченный payload → `ok=False,
"Заказ уже оплачен"`. Реальному плательщику кнопка показывает ошибку. Идемпотентность только
downstream. Вернуть `ok=True` молча на already-paid. [quick]

### 🟡 8.4 Отсутствие индикатора прогресса/шагов в онбординге
`onboarding.py` 7 FSM-шагов; рискованнейший — free-text geocode города (опечатки/локаль), только
`back_menu`, нет «skip». [medium]

### 🟡 8.5 Утечка премиум-контента до пейволла
В flow `features/chat`: бесплатная порция премиум-ответа отдаётся клиенту и лишь потом режется пейволлом
(передать «бесплатную заставку → paywall» — не светить тело ответа). Проверить, что лимит чекается
ДО генерации, не после. [large]

### 🟡 8.6 Palm-loop на ретрае + unlocalized ошибки
`features.py` palm_photo ошибка держит `PalmUpload.photo`, `back_menu()` — ретрай злых фото
зацикливается; текст ошибки DUPLICATE ru для en (line27). Отделить попытку/локаль. [quick]

### 🔵 8.7 Непойманные исключения показываются сыро
`chat.py`/`features.py` — где LLM-сбой прокидывает stacktrace в ответ юзеру вместо дружеского
fallback. Ловить и показывать «попробуйте позже». [quick]

### 🔵 8.8 Рассылки/кроны без per-user флуд-контроля на уровне бота
[sм. 1.4] broadcast каждый tick 60с — дроссель общий, а не на канал. [medium]

---

## 9. ПРОЧЕЕ / GATED

### 🔴 9.1 Релейс-блокеры (external, фикс вне кода)
Из docs/RELEASE/CURRENT_STATUS.md: P0-001 staging initData, P0-002 PSP sandbox-сертификация
(refunds/chargebacks), P0-003 LLM latency p95, P0-004 backup/restore+rollback, P1-004 Swiss
Ephemeris-лицензия, P2-002 ручной accessibility/device review. Открыты: P1-002 stale-fact
memory-телеметрия, P2-005 avatar/object-storage retention.

### 🟡 9.2 Админ: создать/удалить последнего owner без self-lockout-guard
`admin.py:649-687` демот/удаление админа — нет инварианта «нельзя снять себя/последнего owner».
Добавить тест + guard. [medium]

---

## КРАТКИЙ ЧЕК-ЛИСТ БЫСТРЫХ ПОБЕД (quick, ~день работы)
1. Favicon + twitter:card (6.1, 6.2) — 3 строки meta/head
2. `/public` монтировать только css; удалить мёртвые robots/sitemap (4.4, 4.5)
3. og:image на og-card.jpg (6.4)
4. Catch-all `unknown command` в боте (8.2)
5. Пречекаут already-paid → ok=True (8.3)
6. Cache-Control `/public/` (6.6)
7. Lazy `swisseph`/py-импорт — починить тест-сьют (4.2)
8. `pyswisseph` в деп драйвере / verify env-vs-requirements (4.1)
9. LRU-эвикция вместо clear-all в лимитерах (1.4)
10. Fail-fast `settings.ready` (1.11)
11. Rate-limit: задать Redis обязательно в проде (1.5)
12. Кэш `file_loader.load_profiles()` по mtime (5.1) — чистая выгода хот-пути
13. Dневной spend-потолок на LLM (2.5)
14. Ключ unauthenticated rate-limit по IP, не tg_id=0 (см. deps.py:53-63)
