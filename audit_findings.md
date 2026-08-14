# Рабочий журнал аудита oracleAI

## Baseline

- Репозиторий: `astartv1ai-del/oracleAI`.
- Ветка: `master`.
- Commit: `284acc0785ecf80f6b09d24ea276116d9c51e915`.
- Рабочее дерево на момент клонирования чистое; локально созданы только audit-файлы.
- Архитектура: Python/FastAPI/aiogram, Telegram Mini App без сборщика, SQLite WAL, provider chain custom/Anthropic/OpenAI/offline.
- Заявленный продукт: Telegram-бот + Mini App для бережного самопознания, ежедневных ритуалов, Таро, астрологии, дневника и AI-проводников; аудитория 16+.

## Подтверждённые автоматические результаты

- После установки `requirements.txt` и `requirements-dev.txt`: полный pytest завершился успешно; точное число тестов нужно извлечь из полного отчёта/повторного запуска с summary.
- `ruff check app scripts tests`: PASS.
- `pip-audit -r requirements.txt`: `No known vulnerabilities found`.
- `scripts.selfcheck`: PASS; сообщает 147 Python-файлов разобраны, 34 модулей импортируются, core, practices, memory, PDF, database, billing, limits, webhook и horoscope smoke-проверки проходят.
- `node --check` для JS-файлов Mini App: PASS.
- `scripts/check_design_contract.py`: PASS.
- `scripts/release_gate.py`: PASS после установки зависимостей.
- Live LLM self-check не выполнялся: проект сообщает `SELF_CHECK_LIVE=1` требуется для staging; локальные вызовы через доступный proxy дали HTTP 200, но пустой ответ модели и ушли в offline. Это отдельный production-risk, требующий provider-specific проверки.
- Во время selfcheck embeddings endpoint вернул 404, после чего память перешла на keyword fallback; это не падение, но требует проверки production embedding provider.
- Конфигурация без env в локальном окружении предупреждает: BOT_TOKEN/ADMIN_ID/WEBAPP_URL не заданы. Это ожидаемо для audit-среды, но означает, что end-to-end Telegram/deploy-flow не подтверждён.

## Подтверждённые архитектурные сигналы

- Большие и потенциально перегруженные модули: `app/core/skills.py` 72.7 KB, `app/core/agent.py` 49.4 KB, `app/core/llm.py` 36.1 KB, `app/core/astro.py` 31.3 KB, `app/core/practices.py` 38.8 KB, `app/services/scheduler.py` 27.7 KB, `app/api/routers/admin.py` 22.8 KB.
- Frontend состоит из 17 JS-модулей и большого каскада CSS; порядок файлов является архитектурным контрактом. Нужно отдельно оценить runtime coupling и доступность, а не считать успешный syntax/design check доказательством UX-готовности.
- В документации подробно заявлены privacy guards, evidence-first интерпретации, age gate, payment idempotency, analytics redaction и backup/restore; каждое такое обещание следует сопоставить с реализацией и тестом.
- В документации заявлены агенты Лилит, Урания, Мадам Ленорман и Мира; runtime/specs/base/context/interpretation нужно разобрать по контрактам, tool permissions, state, prompt/versioning и fallback.

## Ограничения аудита

- GitHub issue/PR listing через CLI отработал нестабильно из-за несовместимого JSON field и terminal control sequence; повторить отдельными командами через GitHub API/CLI и зафиксировать результат.
- Локально отсутствовали системные compiler/Python headers и dev-пакеты; после их установки baseline стал воспроизводимым. Это указывает, что setup-документация должна явно покрывать системные зависимости или Docker должен быть основным путём.
- Не выполнять изменения продуктового кода до завершения read-only аудита; audit-файлы не являются продуктовой правкой.

## Launch-gates и расхождения

Документ `docs/PRODUCTION_READINESS_EVIDENCE.md` прямо различает code/CI readiness и public-launch approval. Он перечисляет незакрытые внешние блокеры: legal/privacy review; real-device Telegram QA; live LLM/vision provider benchmark; staging, production secrets, HTTPS, encrypted off-site backup и restore drill; Paddle sandbox certification; named operations/support/on-call owners; beta cohort evidence.

Актуальный CI содержит quality checks, 381 собранный тест, dependency audit, selfcheck и static release gate, но отдельного deployment workflow нет. Docker Compose рассчитан на ручной запуск; API жёстко запускается с одним worker из-за in-process rate limiter. Это разумно для controlled beta, но не доказательство capacity для публичного трафика.

Dockerfile включает системные библиотеки для WeasyPrint/Pillow, поэтому чистый install проекта требует не только Python packages. В sandbox до установки build-essential/python3.12-dev requirements.txt не устанавливался из-за pyswisseph; setup-документация должна либо явно описывать системные зависимости, либо направлять разработчика в Docker.

В CI есть только deterministic/sample LLM evaluator; live provider quality и реальный Telegram/device/payment flow не проверяются. Selfcheck корректно пропускает live LLM и production env. В локальном запуске OpenAI-compatible proxy отвечал HTTP 200, но content был пустым, после чего код делал retries и переходил в offline. Embeddings endpoint дал 404 и память перешла на keyword fallback.

Собственная launch-документация требует self-service export/deletion, retention schedule, legal review, support flow, provider benchmark, queue/status UX для долгих vision/LLM jobs и controlled beta waves. Эти элементы следует считать продуктовым backlog, даже если статические gates зелёные.

## UX, Palm и data-plane

Mini App имеет явный age-gate, intro, chat guide, навигацию, sessions, pending widgets, recovery states и reduced-motion/design-contract checks. При этом `05-app.js` проглатывает ошибку `/api/me` и продолжает bootstrap; `loadAgents`/`loadToday` при ошибках тихо переходят к пустым данным. Для production нужен единый auth/bootstrap error state, различение offline/unauthorized/server error и наблюдаемая загрузка основных поверхностей.

`07-chat.js` сохраняет draft только в mutable runtime во время текущего DOM-сеанса; при reload/navigation before submit draft может быть потерян. Ошибка ответа показывает повторную отправку, но не использует server error code для разных сценариев 401/403/409/429/5xx и не имеет устойчивого idempotency key. Это следует проверить и доработать для платных/долгих действий.

Palm API `POST /api/palm` принимает image body и синхронно ждёт `analyze_and_save` до ответа. В БД есть `palm_readings` со status, но нет отдельной jobs/queue сущности или job/status endpoint. Это расходится с launch plan, где для public-scale требуется асинхронная vision job, progress, retry и безопасный polling.

Self-service export не обнаружен. Удаление реализовано как owner-only admin `/api/admin/users/{tg_id}/anonymize`; backend удаляет/анонимизирует связанные записи, но пользовательница не может сама инициировать flow через Mini App/бот. Это privacy/UX gap до public launch, хотя ручной support-control существует.

Схема содержит 41 таблицу/служебные структуры, audit, flags, billing, events, llm_usage и palm_readings, но не содержит отдельной jobs/queue таблицы. SQLite WAL и in-process rate limiter связывают runtime с одним API worker; это controlled-beta решение, не доказанный public-scale контур.

## Agents и LLM

В проекте четыре AgentSpec: Oracle/Лилит, Astro/Урания, Tarot/Мадам Ленорман и Chiromant/Мира. Сильные стороны — явный allow-list skills, разные роли, safety rules, bounded history, privacy-aware context и deterministic evidence-first tools. `runtime.answer` ограничивает бесплатный agent loop шестью итерациями по умолчанию, premium может получить до десяти; tools исполняются параллельно с timeout 15 секунд и output cap 12k.

Основной architectural debt — `app/core/skills.py` около 72.7 KB содержит registry и исполнение разнородных доменов: Tarot, Astro, Matrix, compatibility, practices, memory и Palm. `app/core/agent.py`, `app/core/llm.py` и `app/core/agents/specs.py` также крупные. Это пока работоспособно, но повышает blast radius изменений, усложняет ownership и требует выделения доменных tool-packages и contract tests.

Tool schemas передаются модели, но `skills.execute` не выполняет отдельную Pydantic/JSON Schema validation аргументов перед вызовом handler; неизвестный tool возвращает строку. Для model-generated вызовов это не мгновенный exploit, но это слабее требуемого контракта: schema validation, enum validation, size limits и deterministic rejection должны быть на сервере перед каждым side effect.

LLM gateway имеет provider chain, retries, concurrency/rate limit, fallback и usage logging. Однако в коде не обнаружена полноценная версия prompt/model contract, structured response contract для обычных agent answers, per-user/token budget, provider circuit breaker/health state или отдельный retry budget для всей логической задачи. `max_tokens` задаётся на итерацию, поэтому несколько tool iterations могут увеличить фактический расход сверх ожидаемой «стоимости ответа».

`PRICING` в `app/core/llm.py` — hardcoded approximate map; unknown model cost оценивается как 0.0. Это может скрыть реальную себестоимость при смене модели/провайдера. Embeddings вызываются напрямую через OpenAI-compatible client из `memory.py`, вне общего `_llm_slot`, provider-chain и `llm_usage`; fallback на keyword search полезен для доступности, но cost/latency/usage visibility неполны.

Anthropic vision path получает image и prompt, но строгий `response_format` применяется только в OpenAI-like ветке; общая защита строится на последующем parse/sanitize в palm module. Для каждого production provider нужен явный contract test: schema success, invalid JSON, timeout, provider fallback, image prompt injection и latency.

Системный prompt содержит safety и tool rules, но это всё ещё prompt-layer governance. Нужны deterministic post-generation validators для safety/grounding, versioned prompt registry, audit trail версии модели/prompt/schema и red-team regression cases. Текущий deterministic evaluator на 140 synthetic cases подтверждает harness, но не качество live provider.

## Security, operations и экономика

Подтверждены сильные контроли: production startup fail-closed для BOT_TOKEN/ADMIN_ID/WEBAPP_URL, запрет DEV_MODE вне dev, Telegram initData validation, CSP/security headers, Pydantic validation, ownership checks, rate limits, admin audit, signed Paddle webhook principles, encrypted backup scripts и redacted operational logging. `bash -n` для backup/restore проходит; `ops_alerts.py` поддерживает 5xx, webhook failures, fallback rate и backup age thresholds.

Ограничения: в audit sandbox отсутствует Docker, поэтому Compose config и реальный container build не подтверждены; real backup/restore drill, off-site upload, production secrets, HTTPS certificate, Sentry routing и alert delivery не подтверждены. CI запускает checks, но не deploy/staging rehearsal.

Retention cleanup для events/llm_usage заявлен в analytics service и документации, однако legal retention schedule для категорий данных ещё external gate. Product docs требуют deletion/export; код предоставляет `/delete_me` bot messaging/support wording и admin anonymize, но пользовательский export/self-service deletion/SLA не подтверждены.

GitHub repository public, без license metadata, без open issues, одна закрытая PR; release activity свежая, но governance/ownership cannot be inferred from repository metadata. Нужны explicit license decision, CODEOWNERS/release owner/support owner и security disclosure path до публичного запуска.

Монетизация документирована как scenario model с TBD settlement/tax/refund inputs. Предлагаемые цены и payer-count calculations — гипотезы, не observed economics; до paid launch нужна Paddle/Telegram sandbox certification, settlement reconciliation, refund/support workflow и cost-per-successful-outcome dashboard.
