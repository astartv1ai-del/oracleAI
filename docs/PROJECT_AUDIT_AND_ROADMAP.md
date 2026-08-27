# OracleAI — независимый Technical & Product Due Diligence Audit и roadmap

**Дата аудита:** 27 августа 2026 года, GMT+3
**Репозиторий:** [`astartv1ai-del/oracleAI`](https://github.com/astartv1ai-del/oracleAI)
**Проверенный commit:** `4b0f8e2` (`fix: unify eligibility guard for queued chat`)
**Ветка:** `master`
**Автор:** Manus AI
**Статус документа:** audit snapshot for `4b0f8e2`; subsequent local UX/tooling fixes are recorded in the current working tree and revalidated before release.

> **Итоговый вердикт:** OracleAI уже является содержательным, тестируемым продуктовым ядром с реальными backend-операциями, четырьмя AI-проводниками, детерминированными расчётами, owner-scoped данными, платежной архитектурой и качественным локальным CI-baseline. Однако текущий commit не следует объявлять готовым к безусловному публичному запуску. Реальный Telegram `initData` и device QA, production deployment/rollback, live-провайдеры, payment settlement/refund, юридические placeholders, production backup/restore и несколько инженерных blockers остаются непроверенными или незакрытыми.

## 1. Executive Summary

OracleAI — это Telegram Bot + Mini App для ежедневного ритуала саморефлексии: персональная натальная карта, карта дня, лунный контекст, Tarot, Matrix, дневник, практики, совместимость и четыре специализированных проводника. Архитектура заметно зрелее простого прототипа: FastAPI и aiogram используют общие сервисы, расчёты отделены от интерпретации, платежи имеют idempotent-путь, история и память ограничены владельцем, а в репозитории есть unit/integration/security/domain/visual-quality инструменты. Это подтверждается текущим кодом, схемой данных и локальными проверками [1] [2].

По текущему commit локальные инженерные gates проходят: полный pytest завершился успешно с одним skip, Ruff, JavaScript syntax, self-check, release gate, hygiene, dependency audit, agent-context, domain evaluation, PDF golden cases и disposable backup/restore drill также прошли. Локальный seeded-browser прогон открыл Today, Dialogues и Profile, включая memory state и chat composer. Эти результаты доказывают работоспособность репозитория в изолированном synthetic/dev контуре, но не доказывают безопасность и устойчивость в production Telegram WebView. Действующие документы проекта сами корректно отделяют local pass от external launch gates [12] [15].

**Решение по запуску:** сейчас — **не public launch**, а controlled staging review. Controlled beta допустима только после закрытия P0, сохранения owner-approved risk acceptance для оставшихся P1 и появления внешних evidence artifacts. Для полноценного публичного запуска необходимы как минимум следующие семь пунктов:

| Приоритет | Критичная проблема | Почему это блокирует публичный запуск | Доказательство |
|---|---|---|---|
| 🔴 P0 | Не подтверждены реальный Telegram signed `initData`, `/start`, возрастной gate и device/WebView journey. | Без этого не доказаны identity, onboarding, 16+ boundary, клавиатура, safe area и реальные переходы. | `app/api/deps.py`, `app/api/routers/profile.py`, `docs/LEGAL_REVIEW.md`; local seeded browser — только synthetic evidence. |
| ✅ Closed | Queued-chat eligibility guard is unified across enqueue and worker execution. | The previously identified age-confirmation bypass is covered by queue regression tests; retain this contract in future changes. | `app/services/eligibility.py`, `app/api/routers/jobs.py`, `app/tasks/tasks.py`, `tests/test_jobs.py`. |
| 🔴 P0 | Live LLM p95 выше целевого порога: последний bounded report — `25.088 s` против цели ≤15 секунд. | Длинный ответ ухудшает first-value experience, удержание и стоимость retries; это явно обозначенный staging blocker. | `/tmp/oracleai-llm-live-report-all.json`, `docs/LLM_EVALUATION.md`, `docs/LLM_AGENT_TECHNICAL_AUDIT.md`. |
| 🔴 P0 | Не проведены payment sandbox, settlement/reconciliation/refund и entitlement E2E с provider credentials. | Наличие order/webhook-кода ещё не доказывает, что деньги, возвраты и доступ корректно проходят в реальном PSP. | `app/services/billing.py`, `app/api/routers/webhooks.py`, `docs/MONETIZATION_STRATEGY.md`. |
| 🔴 P0 | Публичные Privacy/Terms содержат незаполненные operator, contact и jurisdiction placeholders; legal/privacy review не выполнен. | Сервис собирает birth data, diary, chat context и может принимать платежи; коммерческий запуск без проверенных условий неприемлем. | `docs/LEGAL_REVIEW.md`, routes `/privacy`, `/terms`, `/privacy/en`, `/terms/en`. |
| 🔴 P0 | Production encrypted backup/restore, storage permissions и rollback rehearsal не подтверждены. | Локальный disposable drill не заменяет восстановление production snapshot с реальным key custody и операционной процедурой. | `scripts/check_backup_restore_drill.py`, `docs/BACKUP_RESTORE_DRILL.md`, `docs/ORACLEAI_CONTINUATION_REPORT.md`. |
| 🔴 P0 | Независимое сравнение астрологических расчётов, licensing confirmation для Swiss Ephemeris/Kerykeion и полная PDF/device review не завершены. | Это external correctness, IP и customer-facing artifact gates, которые нельзя закрыть одним наличием кода или тестовой фикстуры. | `docs/ASTRONOMY_REFERENCE_QA.md`, `docs/CHART_ENGINE_LICENSING.md`, `docs/LEGAL_REVIEW.md`. |

**Оценка готовности:** к следующему controlled staging review — **высокая локальная готовность**; к public launch — **не сертифицирована**. Процент строк или функций не использовался как ложная метрика покрытия: решение принято по critical path, внешним gates, наблюдаемым тестам и последствиям отказа.

## 2. Scope и методология

Аудит проведён против текущего `HEAD`, а не против старых отчётов. Документы `FULL_PRODUCT_SURFACE.md`, `TASKS.md`, `BASELINE.md` и continuation report ценны как traceability, но часть из них ссылается на предыдущий baseline commit; поэтому все существенные выводы сверялись с текущими маршрутами, сервисами, схемами и скриптами [2] [12]. Секреты, реальные Telegram ID и содержимое пользовательских данных в документ не включались.

Проверены следующие области: product surface и архитектура; функциональная полнота; critical path и вторичные сценарии; API/LLM/DB reliability; security, privacy и data ownership; performance и масштабирование; business readiness, payments, legal и SEO; AI agents, routing, memory, CV и safety; visual UX, accessibility, localization, documentation, tests и technical debt.

Локальная проверка выполнялась в изолированном Python 3.12 virtual environment, собранном из `requirements-dev.txt`. Native dependency `pyswisseph` потребовала compiler и Python headers; после установки системных build prerequisites зависимости установились. API запускался локально в `APP_ENV=dev`, `DEV_MODE=1` на disposable SQLite database с synthetic user `10001`. Live LLM, Telegram login, payment provider, production deploy и реальный storage намеренно не запускались.

## 3. Текущий продукт и архитектурная карта

| Слой | Фактически найдено в текущем commit | Статус |
|---|---|---|
| Client | Mobile-first Mini App в `miniapp/`, action delegation через `data-act`, локализованные RU/EN экраны, bottom navigation, chat composer, profile, Tarot, chart, compatibility и palm surfaces. | Работает локально; Telegram device QA открыт. |
| API | FastAPI routes для auth/profile/chat/jobs/today/diary/history/chart/placements/tarot/shop/share/admin/webhooks/SEO и legal pages. | Основной surface реализован; route-level production E2E открыт. |
| Bot | aiogram handlers для `/start`, onboarding, chat, profile, payments и notifications. | Код присутствует; реальный bot token и Telegram journey не проверены. |
| Domain core | Swiss Ephemeris/Kerykeion-backed chart, Tarot ledger, Matrix/practices, compatibility, reports, PDF, palm precheck и optional ONNX line evidence. | Реальные локальные расчёты; независимое oracle comparison и palm benchmark открыты. |
| AI layer | Lilith/oracle, Urania/astro, Madame Lenormand/tarot, Mira/chiromant; routing, skills, bounded tools, safety tail, offline fallback, usage/cost records. | Сильный offline baseline; live quality/latency staging gate открыт. |
| Data | SQLite/WAL schema with migrations, owner-scoped repositories, append-only report/history semantics, memories, diary, jobs, billing, analytics. PostgreSQL/Alembic path присутствует. | Beta-capable local path; production data plane, backup and scale decision require evidence. |
| Operations | Caddy/Docker/compose, Celery/Redis scaffolding, health/security middleware, release gate, CI and audits. | Reproducible local checks; real deployment, queue, alerts and rollback not run. |

## 4. Полная карта находок по восьми слоям

### Слой 1. Product surface, архитектура и соответствие замыслу

| Находка | Фактическое доказательство | Текущее состояние | Риск | Критичность | Сложность |
|---|---|---|---|---|---|
| Основной product concept действительно собран в одном приложении, а не только описан в README. | `app/api/routers/__init__.py`, `miniapp/index.html`, `app/core/agents/`, `app/data/schema.py`, `docs/FULL_PRODUCT_SURFACE.md`. | Реализовано и локально запускается. | Низкий для beta. | 🟢 Желательно | — |
| Архитектура разделяет deterministic evidence и LLM interpretation. | `app/core/agent.py`, `app/core/agents/base.py`, `app/services/chat.py`, `docs/LLM_AGENT_TECHNICAL_AUDIT.md`. | Реализовано с offline fallback и evidence contracts. | Regression при provider/model changes. | 🟡 Важно | Medium |
| SQLite, PostgreSQL migration и Celery/Redis coexist, но production decision не следует из наличия scaffolding. | `app/data/session.py`, `app/data/postgres.py`, `alembic/versions/`, `app/tasks/`, `docs/POSTGRES_MIGRATION.md`. | Beta route возможен; capacity/operational ceiling не доказаны. | Неверный выбор data plane под реальный трафик. | 🟡 Важно | Large |
| Older audit docs refer to previous commit, while current HEAD contains subsequent changes. | `docs/FULL_PRODUCT_SURFACE.md:4`, `docs/TASKS.md:4`, current `git log`. | Traceability есть, но документы нельзя считать current snapshot без сверки. | Команда может принять старый статус за текущий. | 🟡 Важно | Small |

Сильная сторона проекта — достаточно редкая для прототипов дисциплина границ: profile, memory, diary, billing и history не смешаны в одном клиентском состоянии; вычисления выполняются кодом, а модель получает bounded context. Основной архитектурный риск сейчас не в отсутствии модулей, а в том, что рядом существуют несколько execution paths с разной степенью доказанности: synchronous API, queued jobs, bot handlers, web checkout и Telegram Stars.

### Слой 2. Функциональная полнота и реализация пользовательских функций

| Находка | Фактическое доказательство | Текущее состояние | Риск | Критичность | Сложность |
|---|---|---|---|---|---|
| Today ritual, daily card, lunar context, diary, practice, agents и navigation реально отображаются. | Seeded browser; `miniapp/js/06-home.js`, `miniapp/js/15-actions.js`; `/api/today`, `/api/diary`, `/api/agents`. | Happy path работает на synthetic user. | Реальные empty/error states ещё не полностью пройдены вручную. | 🟡 Важно | Medium |
| Chat composer, agent tabs, suggestions, tools и multi-session controls присутствуют. | `miniapp/js/07-chat.js`, `miniapp/js/15-actions.js`, local browser. | Переход Today → Dialogues и suggestion-to-draft подтверждены. | Live response, streaming, cancellation и provider error не проверены в browser. | 🟡 Важно | Medium |
| Profile summary, chart/history/memory tabs, language/gender controls и referral copy доступны. | `miniapp/js/12-misc.js`, local browser; `/api/me`, `/api/history`, `/api/palm`. | Profile и memory enabled state подтверждены. | Account deletion не была найдена в inspected viewport; device-specific flow открыт. | 🟡 Важно | Medium |
| Palm surface хранит structured result/hash/metadata, а raw image не возвращается как retained artifact. | `app/core/palm.py`, `app/api/routers/placements.py`. | Реализовано с upload validation и owner scope. | Accuracy на consented real captures и device latency не подтверждены. | 🟡 Важно | Large |
| Некоторые surfaced controls являются informational или зависят от внешнего канала. | Bell/notification state в `miniapp/js/12-misc.js`; Telegram reminders в bot layer. | UX сообщает о reminders, но Mini App не является полным notification settings center. | Пользователь может ожидать toggle, которого нет. | 🟢 Желательно | Small |

Локально основной value path выглядит так: пользователь открывает Mini App, видит мягкую границу и daily ritual, получает карту дня, затем переходит в chat или другую domain surface. Это не выглядит как пустой mock. Блокером остаётся не отображение готового synthetic профиля, а доказательство того, что новый человек проходит тот же путь через Telegram `/start`, signed identity, age consent и заполнение profile.

### Слой 3. Надёжность, безопасность и данные

| Находка | Фактическое доказательство | Текущее состояние | Риск | Критичность | Сложность |
|---|---|---|---|---|---|
| Production startup fail-closes unsafe dev mode и отсутствие обязательных credentials; security headers/CSP/request IDs добавлены. | `app/api/main.py`, `app/config.py`, `scripts/release_gate.py`. | Local release gate PASS; real deploy не запускался. | Ошибка окружения/secret wiring может быть обнаружена только на staging. | 🔴 Блокер до public | Medium |
| Telegram identity и owner scope проверяются на сервере; `dev_user` ограничен dev mode. | `app/api/deps.py`, `app/api/security.py`, repositories/tests. | Кодовой baseline достаточно для review. | Signed initData и tampering на реальном Telegram не проверены. | 🔴 Блокер до public | Medium |
| Обычный chat API использует `confirmed_age_user`, но queued chat route использует только `current_user`. | `app/api/routers/chat.py`, `app/api/routers/jobs.py:23-35`. | Несогласованность dependencies. | Возможный bypass 16+ через `/api/jobs/chat/{agent}`; worker также не проверяет age перед `chat_service.ask` [5]. | 🔴 Блокер до public | Small |
| In-memory rate limit защищает один process, но не распределённый multi-instance deployment. | `app/api/deps.py:37-79`. | Приемлемо для одного VPS/controlled beta; Redis нужен для scale. | Обход лимита через несколько workers/instances, uneven abuse protection. | 🟡 Важно | Medium |
| Memory consent, deletion, owner isolation и raw-image non-retention имеют server-side controls. | `app/api/routers/profile.py`, `app/services/chat.py`, `app/core/palm.py`, security tests. | Сильный local baseline. | Production storage permissions, retention/legal wording и restore procedure не подтверждены. | 🔴 Блокер до public | Large |
| Webhook signature, timestamp, order binding и idempotent journal реализованы; при ошибке журнала код предпочитает возможную повторную обработку, а не потерю payment. | `app/api/routers/webhooks.py`, `app/services/billing.py`. | Кодовая защита есть; provider sandbox отсутствует. | Возможная double-grant trade-off требует monitoring/reconciliation и не закрывается unit test. | 🔴 Блокер до public | Large |
| Disposable backup/restore drill прошёл с owner isolation, но production key custody/encryption/storage/rollback не доказаны. | `scripts/check_backup_restore_drill.py`, `docs/BACKUP_RESTORE_DRILL.md`. | Local synthetic PASS. | Потеря или невозможность восстановления production данных. | 🔴 Блокер до public | Large |
| Error responses не отдают stack trace по common path; Pydantic ловит empty input и invalid language. | `app/api/main.py`, contracts, local `/api/profile` и empty chat checks. | Local checks PASS. | Полный matrix future dates, DST, upload, provider malformed response и client recovery требует staging/E2E. | 🟡 Важно | Medium |

Главная security находка — не отсутствие защиты вообще, а **разрыв между execution paths**. Исправление должно быть централизованным: общий `require_age_confirmed`/eligibility service должен применяться и на enqueue, и при worker execution, чтобы возраст, status, plan/allowance и safety не зависели от того, каким транспортом пришёл запрос.

### Слой 4. Производительность, UX ответа AI и масштабирование

| Находка | Фактическое доказательство | Текущее состояние | Риск | Критичность | Сложность |
|---|---|---|---|---|---|
| Детерминированные chart, Tarot и memory операции быстрые на synthetic workload. | `scripts/benchmark_product_performance.py`; chart p50 3.47 ms, Tarot p50 0.06 ms, memory p50 0 ms. | Directional local PASS. | Не учитывает contention и production data volume. | 🟢 Желательно | Medium |
| PDF HTML generation занимает около 1.4 s p50 и до 2.8 s max на двух runs. | Current benchmark. | Приемлемо для background/report flow. | Percentile на n=2 статистически слаб; PDF delivery path не полностью measured. | 🟡 Важно | Small |
| Palm-line fp16 segmentation заняла около 8.35 s p50/p95 на текущем sandbox CPU. | Current `benchmark_product_performance.py`; model `palm_line_student_fp16.onnx`. | Local pass по функциональности, но не по mobile SLO. | Слабое устройство может зависать или выглядеть сломанным; нужен int8/skip/queue strategy. | 🟡 Важно | Medium |
| Provider-side live LLM p95 документирован как 25.088 s против цели ≤15 s. | `/tmp/oracleai-llm-live-report-all.json`, `docs/LLM_EVALUATION.md`, `docs/LLM_AGENT_TECHNICAL_AUDIT.md`. | Explicit staging blocker. | Потеря first-value, retries и рост стоимости. | 🔴 Блокер до public | Large |
| Mini App chat endpoint возвращает complete answer; provider умеет собирать stream, но incremental stream до клиента не доказан. | `app/core/llm.py`, `app/services/chat.py`, `app/api/routers/chat.py`. | UX имеет loading/error controls, но streaming/cancellation не подтверждены. | При длинном ответе пользователь видит ожидание без частичной ценности. | 🟡 Важно | Medium |
| Rate limit и DB connection state in-process. | `app/api/deps.py`, `app/data/session.py`. | Один process/VPS acceptable для beta. | Multi-worker horizontal scale потребует shared limiter, pool и capacity test. | 🟡 Важно | Large |

Производительность не является проблемой domain calculations; узкие места — live LLM, Palm CV и неопределённость распределённого режима. Нельзя объявлять локальные p50 production SLO: benchmark синтетический, PDF sample мал, а provider latency зависит от модели, региона, очереди и retry policy.

### Слой 5. Business readiness, payments, legal и публичный web surface

| Находка | Фактическое доказательство | Текущее состояние | Риск | Критичность | Сложность |
|---|---|---|---|---|---|
| Технически существуют Telegram Stars, Paddle/web order, crystals, entitlements, products и refunds/status fields. | `app/services/billing.py`, `app/api/routers/shop.py`, schema, `docs/MONETIZATION_STRATEGY.md`. | Technical foundation implemented. | Settlement, taxes, refund/reconciliation и provider certification не доказаны. | 🔴 Блокер до public | Large |
| Current seed catalog не равен approved live pricing. | `docs/MONETIZATION_STRATEGY.md:1169-1170, 1212-1226`. | Pricing strategy explicitly marked recommendation. | Нельзя публиковать цены по аналитическому документу без owner approval/live export. | 🔴 Блокер до commercial launch | Medium |
| Product cost records include model/tokens/latency/estimated cost, но PDF/support/tax/settlement/CAC не образуют полный reviewed contribution ledger. | `app/core/product_cost.py`, `docs/MONETIZATION_STRATEGY.md`. | Cost instrumentation partial. | Неверные margin assumptions и uncontrolled deep actions. | 🟡 Важно | Medium |
| `/landing`, `/landing/en`, privacy, terms, robots and sitemap отвечают 200 локально; title/description/canonical присутствуют на landing. | Local API route checks, templates/static landing code. | Public web basics implemented. | Canonical на local host must be replaced/verified in production; OG/structured data and full SEO semantics need review. | 🟡 Важно | Small |
| Privacy/Terms intentionally leave legal entity, address, contact, jurisdiction and policy placeholders. | `docs/LEGAL_REVIEW.md`, `/privacy`, `/terms`. | Texts are present but not launch-approved. | Legal non-compliance and unclear data-subprocessor/retention/refund commitments. | 🔴 Блокер до public | Medium |
| Analytics includes events for questions, opens, product/cost and operational categories without raw user text in the intended contract. | `app/repo/analytics.py`, `docs/ANALYTICS_EVENT_DICTIONARY.md`. | Code/dictionary present. | Production sink, dashboard, alert routing and data-retention verification not run. | 🟡 Важно | Medium |

В business readiness следует разделять **“можно создать order”** и **“можно принимать деньги публично”**. Второе требует sandbox evidence, server-side binding, duplicate/refund/reconciliation scenarios, published terms, support path и владельца, который утвердил актуальный live catalog.

### Слой 6. AI agents, routing, memory, CV и safety

| Находка | Фактическое доказательство | Текущее состояние | Риск | Критичность | Сложность |
|---|---|---|---|---|---|
| Четыре agent profile имеют bounded skills/tools, domain rules и safety boundaries. | `app/core/agents/`, `docs/AGENT_ARCHITECTURE.md`, `docs/LLM_AGENT_TECHNICAL_AUDIT.md`. | Реализовано; context-contract check PASS. | Provider/model change может изменить поведение. | 🟡 Важно | Medium |
| Prompt context маркирует chart/Matrix как deterministic evidence, а memory/diary/profile/history как untrusted data. | `app/core/agents/base.py`, `app/core/agents/runtime.py`, memory wrappers. | Offline context tests PASS. | Human review и live prompt-injection evaluation остаются внешними. | 🟡 Важно | Medium |
| Safety crisis path отвечает кодом до LLM и не списывает платный вопрос; soft-risk path records incident. | `app/services/chat.py`, `app/core/safety.py`, tests. | Local safety baseline PASS. | Локальные emergency resources и production monitoring need owner/legal review. | 🔴 Блокер до public | Medium |
| Aggregate agent quality/domain evaluation проходит: 54 cases; routing accuracy 1.0; Vedic top-1 1.0. | `scripts/check_agent_quality.py`, `scripts/check_domain_evals.py`. | Strong local baseline. | Metric is synthetic/offline. | 🟡 Важно | Medium |
| Mira/Lenormand specialized benchmark проходит top-3 20/20, но top-1 только 14/20 = 70%. | `scripts/benchmark_mira_lenormand.py` executed as module. | Acceptable recall, weak precision. | Wrong first skill can shape prompt and output, especially in palm/Tarot boundary cases. | 🟡 Важно | Medium |
| Palm CV returns bounded summaries and never raw mask; model integrity hash is checked. | `app/core/palm_lines.py`, `app/core/palm.py`, `models/THIRD_PARTY_NOTICES.md`. | Good defense-in-depth. | Model generalization, device inference and real capture benchmark open. | 🟡 Важно | Large |
| Direct script invocation previously depended on caller-provided `PYTHONPATH`. | Root bootstrap was added to the four affected scripts and direct invocations pass in the current working tree. | Reproducibility gap is closed locally; retain direct invocation checks in CI. | Operators no longer receive a false import failure from documented-looking commands. | ✅ Closed | Small |

AI layer is one of the strongest parts of the repository, but the project must not convert offline evaluator green into a production safety claim. A minimum staging matrix should include language switching, empty/partial chart, unknown birth time, conflicting memory, prompt injection, crisis/soft-risk, Tarot ledger mismatch, palm poor capture, provider timeout, duplicate retry and cancellation.

### Слой 7. Visual UX, accessibility, localization и responsive behavior

| Находка | Фактическое доказательство | Текущее состояние | Риск | Критичность | Сложность |
|---|---|---|---|---|---|
| Dark/night visual language, token cascade, ritual redesign and reduced-motion CSS are coherent. | `miniapp/css/00-tokens.css`, `miniapp/styles.css`, `miniapp/css/15-ritual-redesign.css`, `docs/DESIGN_SYSTEM.md`. | Design contract PASS. | Manual contrast and interaction review still open. | 🟢 Желательно | Medium |
| Seeded local browser rendered Today, Dialogues and Profile at a narrow mobile viewport. | Local browser inspection against `/?dev_user=10001`; screenshots kept outside source tree. | Observed local pass. | Not Telegram iOS/Android/Desktop evidence; only seeded account. | 🟡 Важно | Medium |
| Chat suggestion correctly fills textarea without sending; agent onboarding dismisses; Profile memory card shows one record. | Local browser interaction. | Observed local pass. | Live send/error/slow-network and deletion visual state not fully checked. | 🟡 Важно | Small |
| Deterministic Playwright baseline is documented as 6 viewports × 9 states with no horizontal overflow, unnamed focusables or missing image alt. | `docs/LOCAL_BROWSER_BASELINE.md`, `scripts/capture_visual_baseline.py`. | Automated baseline claimed and current repo checks pass. | Desktop, manual keyboard/screen reader/contrast, loading/error states open. | 🟡 Важно | Medium |
| RU/EN are separate locale surfaces and English fallback regression exists. | `miniapp/js/01-utils.js`, `miniapp/js/06-home.js`, localization tests/glossary. | Main known leakage fixed. | Long labels, pluralization, all PDF locale variants and Telegram UI widths open. | 🟢 Желательно | Medium |
| Focus-visible, tap targets and data-act delegation are present. | `miniapp/js/15-actions.js`, CSS, `tests/test_miniapp_actions.py`. | Static contract PASS. | Real keyboard/assistive-tech behavior not observed. | 🟡 Важно | Medium |

Локальный визуальный результат соответствует заявленной формуле «мистичность задаёт настроение; интерфейс остаётся предсказуемым», но этот вывод ограничен synthetic browser. До запуска следует пройти reference matrix в Telegram WebView и вручную проверить 360–430 px, dynamic viewport, keyboard-open, reduced motion, long names, RU/EN, empty/error/loading и age-gate states.

### Слой 8. Documentation, tests, CI и technical debt

| Находка | Фактическое доказательство | Текущее состояние | Риск | Критичность | Сложность |
|---|---|---|---|---|---|
| CI workflow включает dependencies, Ruff, compileall, JS syntax, hygiene, cache busting, design contract, LLM evaluator, migrations, full tests, pip-audit, selfcheck и release gate. | `.github/workflows/ci.yml`. | Хорошая automated quality base. | CI не заменяет external Telegram/payment/deploy gates. | 🟢 Желательно | — |
| Full pytest, Ruff, Node checks, selfcheck, release gate, pip-audit и hygiene прошли в текущем sandbox. | Local run evidence, commands in section 5. | Local PASS. | One skip and expected credential/live skips must remain visible. | 🟡 Важно | — |
| Test suite is broad: security, API resilience, migrations, billing, jobs, agent context, Tarot, PDF, palm, history and Mini App actions. | `tests/` inventory, `docs/TESTING.md`. | Good coverage of code contracts. | True Telegram device, payment settlement, production DB and provider behavior open. | 🟡 Важно | Medium |
| Standalone quality scripts previously worked reliably only as `python -m scripts.name`. | `scripts/validate_skill_library.py`, `scripts/check_agent_stability.py`, `scripts/benchmark_vedic_routing.py` and `scripts/benchmark_mira_lenormand.py` now bootstrap repository root; direct commands pass. | Keep this as a CI regression contract. | ✅ Closed | Small |
| Benchmark methodology is partly weak for small samples. | PDF benchmark n=2 produced p50 1409.51 ms and p95 10.3 ms; p95 cannot be treated as a stable SLO. | Evidence should be relabeled directional. | False performance confidence. | 🟡 Важно | Small |
| Generated visual captures under `artifacts/visual-baseline/` are untracked audit outputs, not product source. | `git status --short` after visual baseline run. | Keep outside release commits or remove before handoff; do not silently ship large generated artifacts. | 🟢 Желательно | Small |

Documentation quality is unusually high and honest about limitations. The remaining documentation debt is synchronization: historical reports and benchmark snapshots must continue to be refreshed after each release. The direct-invocation script defect identified during the audit is closed locally and is now a CI regression contract. The audit document intentionally retains historical evidence labels instead of rewriting previous reports.

## 5. Post-audit local fixes

The following findings were fixed after the initial audit and are covered by the current working tree QA: the Mini App now renders an explicit authenticated recovery state instead of silently continuing to the home shell after `/api/me` failure; account deletion is discoverable from Profile Summary, confirm-gated, calls the existing idempotent endpoint and renders a terminal success state; six operator-facing scripts bootstrap the repository root for direct invocation; CI runs the quality-script subset as a regression check; and the Mini App asset version was raised from 95 to 96 so the fixes are not hidden by stale client caches. These changes do not close the external Telegram, payment, legal, live-provider, monitoring or production restore gates.

## 6. Critical path walkthrough

| Шаг | Ожидаемый пользовательский путь | Что реально подтверждено | Вывод |
|---|---|---|---|
| 1 | Открыть публичный landing, legal pages и Mini App entry. | Local `GET /landing`, `/landing/en`, `/privacy`, `/terms`, `robots.txt`, `sitemap.xml` returned 200; landing includes title/description/canonical. | Public web shell works locally; production domain/OG/canonical must be verified. |
| 2 | В Telegram нажать `/start`, пройти signed identity и создать user. | Clean unseeded API returned 404 “open the bot and press /start”; synthetic seeding bypassed this path. | **Не доказано внешне; P0 gate.** |
| 3 | Пройти age 16+ self-confirmation, затем profile/birth input. | `confirmed_age_user` exists; invalid profile language returned 400; synthetic profile had exact chart. | Server model exists; real first-run and device flow not proven. |
| 4 | Получить first value: Today ritual, lunar context, daily card. | Seeded `/api/today` returned forecast/card/moon; browser showed Today ritual, daily card and CTA. | Local happy path works. |
| 5 | Перейти к AI agent and ask first question. | Browser opened Dialogues, agent tabs, composer, tools and suggestion chips; suggestion filled draft. | Entry UX works; no live answer was sent in audit. |
| 6 | Receive answer, preserve history, retry/error safely. | Offline/selfcheck and chat code cover save/refund/fallback; live provider response/stream/cancel and browser error recovery not exercised. | **Staging gate.** |
| 7 | Use Tarot/chart/compatibility/palm secondary paths. | `/api/tarot/spreads`, `/api/placements`, `/api/palm`, expanded chart and PDF golden cases passed locally; palm raw retention is bounded. | Code surface exists; real upload/device and full visual matrix open. |
| 8 | Reach paywall, pay, receive entitlement and recover/refund. | Order/webhook/idempotency code exists; no provider sandbox/settlement/refund run. | **P0 commercial gate.** |
| 9 | Return later, see history/memory, change settings. | Browser Profile and Memory enabled state rendered; API history owner scope returned Tarot/diary records; language/gender controls visible. | Local seeded path works; memory-off and deletion visual states need dedicated QA. |
| 10 | Delete account, restore service after incident. | Confirm-gated deletion/anonymization and disposable backup/restore drill passed. | Production legal retention, encrypted backup, restore and rollback open. |

## 7. Проверки и их результаты

| Проверка | Команда/метод | Результат | Ограничение |
|---|---|---|---|
| Unit/integration suite | `/tmp/oracleai-venv/bin/python -m pytest -q` | **PASS**, 100%, один skipped test | Sandbox dependencies installed separately; no production services. |
| Python quality | `/tmp/oracleai-venv/bin/ruff check app scripts tests` | **PASS** | Static only. |
| Python/JS syntax | compile/selfcheck and `node --check` for all `miniapp/js/*.js` + `admin/admin.js` | **PASS** | Does not prove browser/device behavior. |
| Self-check | `/tmp/oracleai-venv/bin/python -m scripts.selfcheck` | **PASS**; live LLM skipped, production credentials absent | Expected local skips: `BOT_TOKEN`, `ADMIN_ID`, `WEBAPP_URL`, live provider. |
| Release gate/hygiene | `scripts.release_gate.py`, `scripts/check_repository_hygiene.py` | **PASS** | Static gate only. |
| Security/dependency | `pip-audit -r requirements.txt` | **No known vulnerabilities** | Known-vulnerability database is not a complete security audit. |
| Agent context/domain | `check_agent_context_contracts.py`, `check_domain_evals.py`, `check_agent_quality.py` | **PASS**, 54 domain cases; routing top-1 1.0; Mira/Lenormand top-1 0.70 but top-3 1.0 | Synthetic/offline evidence. |
| Chart/PDF/backup | expanded chart, PDF golden cases, disposable backup/restore | **PASS** | Independent calculator, production restore and full visual review open. |
| Local API smoke | Public/legal/SEO routes, seeded authenticated routes, invalid language, empty chat | **PASS** for expected statuses | Dev mode + synthetic user, not signed Telegram. |
| Browser smoke | Seeded Today → Dialogues → composer → Profile → Memory | **PASS** for observed local states | Narrow sandbox viewport; no Telegram device or assistive-tech claim. |
| Direct script reproducibility | `python scripts/validate_skill_library.py`, `python scripts/check_agent_stability.py`, `python scripts/benchmark_vedic_routing.py`, `python scripts/benchmark_mira_lenormand.py` | **PASS** after repository-root bootstrap; direct invocations are now run in CI | Keep as a regression contract. |

## 8. Roadmap

### Phase A — Must Fix Before Launch

| ID | Работа | Причина | Acceptance criteria | Зависимости | Оценка |
|---|---|---|---|---|---|
| A-01 | ✅ Закрыто в `4b0f8e2`: унифицирован eligibility/age guard для synchronous chat, queued enqueue и worker execution. | Сохранить защиту от обхода 16+ при дальнейших изменениях transports. | Неподтверждённый age получает 403, worker повторно отбрасывает job; enqueue/worker regression tests проходят. | None. | Closed |
| A-02 | Провести controlled staging с реальным Telegram bot/Mini App. | Доказать signed `initData`, `/start`, age gate, onboarding, profile, keyboard, safe area и logout/reopen. | Сохранены synthetic-safe screenshots/logs, invalid/expired/tampered signature checks, 360–430 px RU/EN device matrix, no PII in artifacts. | Owner Telegram credentials and staging domain. | Large |
| A-03 | Снизить live LLM p95 до ≤15 s или formally revise SLO before beta. | Latest bounded report is 25.088 s and blocks first-value quality. | Repeatable 30–50 case staging run, p50/p95/p99, timeout/retry/cost attribution, error/fallback rate and approved SLO. | A-02, provider/model access. | Large |
| A-04 | Выполнить payment sandbox E2E: order, successful payment, duplicate webhook, wrong price/order binding, refund, cancellation and entitlement expiry. | Кодовая idempotency не заменяет provider settlement evidence. | Provider-signed fixtures and sandbox receipts; no duplicate grant; refund/reconciliation report; support path and terms linked. | PSP/Paddle/Telegram sandbox credentials. | Large |
| A-05 | Заполнить legal placeholders and approve Privacy/Terms/16+/refund/support/subprocessor wording. | Current pages are not launch-ready legal documents. | Named operator/contact/jurisdiction, retention/deletion/export, LLM subprocessors, payment/refund/tax wording, local emergency resources, legal sign-off. | Product owner + qualified counsel. | Medium–Large |
| A-06 | Execute encrypted production-like backup/restore and rollback rehearsal. | Disposable local drill is insufficient. | Fail-closed key handling, encrypted off-site snapshot, checksum, restore into isolated target, owner isolation check, RTO/RPO record, rollback runbook and alert. | Production-like storage/host key. | Large |
| A-07 | Close correctness/licensing gate for astrology, Tarot and PDF. | Independent calculation comparison and licensing are external obligations. | Versioned exact/date-only/DST/high-latitude comparison against approved reference; Swiss Ephemeris/Kerykeion notices confirmed; full RU/EN PDF matrix manually reviewed. | Independent reviewer and legal/licensing owner. | Medium–Large |

### Phase B — Should Fix Soon

| ID | Работа | Причина | Acceptance criteria | Оценка |
|---|---|---|---|---|
| B-01 | Add a shared distributed limiter and production DB/connection strategy. | In-memory limiter/connection state is single-process. | Redis-backed identity/bucket limits, DB pool/capacity test, 5xx/error budget under representative load. | Medium–Large |
| B-02 | Decide whether to expose incremental AI streaming and cancellation. | Current path likely waits for complete answer despite provider-side stream collection. | UX evidence for sending/loading/cancel/error/cancel; measurable time-to-first-token and safe refund semantics. | Medium |
| B-03 | Improve Mira/Lenormand top-1 routing from 70% while retaining top-3 recall. | Wrong first skill can bias the prompt. | Specialized benchmark target agreed, ideally ≥90% top-1 on expanded cases; regressions added to CI. | Medium |
| B-04 | ✅ Закрыто локально: bootstrap repository root в directly executable scripts и CI smoke. | Устранён misleading import failure при operator invocation. | `python scripts/name.py` и `python -m scripts.name` проходят для quality scripts; direct commands закреплены в CI. | Closed |
| B-05 | Correct benchmark methodology for small samples and separate CV engines by device budget. | Current PDF p95 with n=2 is directional; latest palm fp16 sample is ~8.35 s on sandbox CPU and still lacks real-device evidence. | Minimum sample size, documented percentile method, int8/fp16/skip decision from real capture benchmark, user-visible progress/timeout. | Small–Medium |
| B-06 | Finish manual accessibility/responsive matrix and visual lifecycle review. | Automated DOM checks do not prove screen reader, contrast, keyboard, memory-off, deletion confirmation or error UX in real Telegram WebView. | Manual keyboard/screen-reader/contrast review; 360/390/430 px RU/EN; loading/error/empty/slow/offline; deletion confirmation/success and memory-off screenshots. Account deletion UI is now implemented locally. | Medium |
| B-07 | Verify production analytics sink, alerts and cost ledger by product/channel. | Events exist but operational dashboards and full variable-cost view are not proven. | Dashboard for activation, first value, LLM p95/fallback, paywall, purchase, refund, retention and channel cost; no raw personal text. | Medium |
| B-08 | Review web SEO metadata on production domain. | Local canonical and sitemap use local host in smoke environment. | Production canonical/OG/robots/sitemap, structured data, legal links and crawl check. | Small–Medium |

### Phase C — Nice to Have

| ID | Работа | Пользовательская ценность | Оценка |
|---|---|---|---|
| C-01 | Полный notification center/toggle inside Mini App. | Уменьшить расхождение между informational bell и Telegram bot settings. | Small–Medium |
| C-02 | Desktop visual polish, broader PDF template gallery and additional chart products. | Улучшить premium perception after core gates. | Medium |
| C-03 | Richer report export/history for palm and future products. | Продолжить unified archive beyond current intentional palm boundary. | Medium–Large |
| C-04 | Experimentation and public SEO/content growth layer. | Acquisition and retention learning after trustworthy launch. | Medium |
| C-05 | Additional model/device optimization and broader independent domain evaluation. | Lower cost and increase confidence after staging data. | Medium–Large |

## 9. Открытые вопросы владельца проекта

| Вопрос | Какое решение меняет |
|---|---|
| Какой юридический оператор, jurisdiction, support contact и retention policy будут указаны на public launch? | Privacy/Terms, deletion/export, incident response и release date. |
| Какой канал является primary для коммерции: Telegram Stars, Paddle web или оба? | Catalog, pricing, tax/refund, reconciliation, analytics channel и support. |
| Будет ли launch controlled beta на одном VPS/SQLite или public-scale deployment на PostgreSQL + Redis + Celery? | Rate limiting, connection pooling, backup, worker topology, capacity test и rollback. |
| Сохраняется ли target live LLM p95 ≤15 s? | Модель, streaming, timeout, concurrency, prompt budget и launch SLO. |
| Какой уровень 16+ self-confirmation юридически достаточен для стран присутствия? | Copy, geography, access policy и legal sign-off. |
| Является ли пальмовая CV-оценка launch feature или auxiliary beta experiment? | Device model, int8/fp16 budget, upload retention, consent benchmark и UX expectation. |
| Что именно считается платным результатом и какая цена утверждена? | Live catalog, entitlement semantics, credits, refunds и unit economics. |
| Нужен ли self-service data export наряду с deletion? | API scope, legal copy, support process и privacy implementation. |
| Какой минимальный evidence threshold требуется для live AI safety approval? | Golden cases, human adjudication, provider/model lock и incident response. |

## 10. Рекомендация: с чего начинать после утверждения

Начинать следует не с новых функций и не с маркетингового трафика, а с **P0 Staging Closure Pack** из трёх связанных потоков.

Первый поток — создать изолированный staging и выполнить реальный signed Telegram flow на iOS, Android и Desktop. Предыдущий queued-chat eligibility mismatch уже закрыт в `4b0f8e2` и покрыт worker/enqueue regression tests; теперь его нужно только сохранить при внешнем E2E.

Затем следует провести live LLM latency/safety run на том же controlled staging environment и закрыть payment/legal/backup/monitoring evidence. Эти проверки дадут владельцу реальную информацию о first-value path и response budget. Только после этого имеет смысл принимать окончательное решение о SQLite/VPS против PostgreSQL/Redis/Celery scale.

Параллельно владелец должен назначить ответственных за A-04, A-05 и A-06. Без payment/legal/backup owners техническая готовность repository не превращается в право принимать реальные деньги и персональные данные. До появления этих evidence artifacts рекомендованный режим — staging или ограниченная beta с явным risk acceptance, а не публичный launch.

## 11. References

[1]: [README.md](../README.md) — продукт, запуск и общая архитектура OracleAI.
[2]: [FULL_PRODUCT_SURFACE.md](FULL_PRODUCT_SURFACE.md) — surface inventory и предыдущий baseline; использовать с учётом commit drift.
[3]: [app/api/main.py](../app/api/main.py) и [app/config.py](../app/config.py) — startup, middleware, security headers, CSP и environment guards.
[4]: [app/api/deps.py](../app/api/deps.py) и [app/api/security.py](../app/api/security.py) — Telegram identity, dev mode, age dependency и rate limits.
[5]: [app/api/routers/jobs.py](../app/api/routers/jobs.py) и [app/tasks/tasks.py](../app/tasks/tasks.py) — queued chat route и worker execution path.
[6]: [app/api/routers/chat.py](../app/api/routers/chat.py) и [app/services/chat.py](../app/services/chat.py) — synchronous chat, limits, safety, persistence и refund path.
[7]: [app/core/llm.py](../app/core/llm.py) — provider chain, retries, budgets, streaming collection и cost ledger.
[8]: [app/core/palm.py](../app/core/palm.py), [app/core/palm_lines.py](../app/core/palm_lines.py) — upload validation, raw-image boundary и auxiliary CV evidence.
[9]: [app/services/billing.py](../app/services/billing.py), [app/core/product_cost.py](../app/core/product_cost.py) — orders, grants, crystals, entitlements и cost attribution.
[10]: [app/api/routers/webhooks.py](../app/api/routers/webhooks.py) — signed webhook, timestamp, order binding и duplicate handling.
[11]: [LEGAL_REVIEW.md](LEGAL_REVIEW.md) — legal/privacy/terms launch gate.
[12]: [ORACLEAI_CONTINUATION_REPORT.md](ORACLEAI_CONTINUATION_REPORT.md) — последний локальный implementation report и explicit external blockers.
[13]: [LLM_AGENT_TECHNICAL_AUDIT.md](LLM_AGENT_TECHNICAL_AUDIT.md) — agent context, safety, quality and live latency evidence.
[14]: [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) и [LOCAL_BROWSER_BASELINE.md](LOCAL_BROWSER_BASELINE.md) — design tokens, responsive/accessibility contract и browser baseline.
[15]: [TESTING.md](TESTING.md) — testing contract, local commands и разделение local/external evidence.
[16]: [ci.yml](../.github/workflows/ci.yml) — automated CI quality gates.
[17]: [MONETIZATION_STRATEGY.md](MONETIZATION_STRATEGY.md) — pricing/payment strategy; explicitly not approved live catalog.
[18]: [scripts/benchmark_product_performance.py](../scripts/benchmark_product_performance.py), [scripts/check_agent_quality.py](../scripts/check_agent_quality.py), [scripts/check_domain_evals.py](../scripts/check_domain_evals.py) — local synthetic performance and quality checks.
[19]: [scripts/validate_skill_library.py](../scripts/validate_skill_library.py) и [scripts/benchmark_mira_lenormand.py](../scripts/benchmark_mira_lenormand.py) — direct-execution reproducibility and routing precision evidence.
[20]: [scripts/check_backup_restore_drill.py](../scripts/check_backup_restore_drill.py), [docs/BACKUP_RESTORE_DRILL.md](BACKUP_RESTORE_DRILL.md) — disposable local backup/restore evidence, not production sign-off.

> **Audit evidence note:** local API/browser artifacts and terminal outputs were kept outside the repository and used only as diagnostic evidence. They contain synthetic data only; they are not a substitute for signed Telegram, live provider, payment sandbox, production restore or legal sign-off.
