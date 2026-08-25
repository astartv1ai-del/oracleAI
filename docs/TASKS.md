# OracleAI — рабочий backlog

Дата baseline: **2026-08-25**. Документ обновляется синхронно с кодом и документацией.

## Статус фаз

| Фаза | Статус | Критерий перехода |
|---|---|---|
| 0. Аудит и документация | complete | Фактическая карта потоков, baseline-тесты и ADR зафиксированы |
| 1. Конкурентный benchmark | complete | Публичные наблюдения SteerCorp подтверждены ссылками |
| 2. Расчётный слой и wheel | complete | Canonical DTO, edge fixtures and SVG regressions are green |
| 3. LLM interpretation/chat | in progress | Strict JSON path, luminary coverage and grounding are green; live/API follow-up QA remains |
| 4. PDF | complete | RU/EN A4 PDFs, visual pages and text markers pass |
| 5. Routing и персоны | complete | 24-case matrix passes; specialist benchmarks and handoff UI pass |
| 6. Полный аудит и release gate | complete | 465 tests, selfcheck, routing, PDF, syntax and design gates are green |

## Фаза 0 — audit baseline

- [x] Клонировать `astartv1ai-del/oracleAI` и зафиксировать ветку/последний commit.
- [x] Определить стек: Python/FastAPI/aiogram, Vanilla JS Mini App, SQLite WAL, Kerykeion/Swiss Ephemeris, WeasyPrint.
- [x] Найти расчётный слой, API-контракт, interpretation pipeline, agent registry/runtime, PDF pipeline и frontend wheel.
- [x] Зафиксировать baseline `pytest -q`: проходит полный suite после установки pinned dependencies.
- [x] Зафиксировать baseline `python -m scripts.selfcheck`: завершён успешно; live LLM пропущен без `SELF_CHECK_LIVE=1`, переменные Telegram/WEBAPP не заданы в sandbox.
- [x] Создать/обновить живые документы `ARCHITECTURE.md`, `DECISIONS.md`, `CHANGELOG.md`, `AGENTS.md`, `TASKS.md`.
- [x] Добавить отдельный baseline-отчёт с командами, выводами и известными ограничениями.
- [x] Проверить production/CI-команды и воспроизводимость PDF/скриншотов.

## Фаза 1 — конкурентный аудит SteerCorp

- [x] Пассивно исследовать публичные страницы `steercorp.io` и доступный onboarding.
- [x] Сравнить wheel, глубину текста, onboarding, PDF/export, языки, дополнительные функции и premium brand.
- [x] Добавить в `DECISIONS.md` таблицу `Competitor Benchmark` с URL и confidence.
- [x] Сформировать список «повторить минимум» и «превзойти».

## Фаза 2 — расчёты и SVG wheel

- [x] Оформить versioned `CalculationConfig` и canonical `ChartModel`.
- [x] Явно вернуть conventions: Tropical, Placidus `P`, Apparent Geocentric, True Node, active points и aspect policy.
- [x] Подтвердить поведение Chiron, Lilith, Rahu/Ketu, unknown time, DST, IANA timezone, invalid coordinates и polar latitudes.
- [x] Сохранить exact values отдельно от UI-rounded values и добавить precision/source metadata.
- [x] Добавить golden fixtures и cross-engine regression checks.
- [x] Переписать/усилить SVG: collision avoidance, семантические стили аспектов, легенда, labels, responsive viewBox, reduced-motion.
- [x] Проверить минимум три плотности карты screenshot-регрессией.

## Фаза 3 — интерпретация и follow-up

- [x] Разделить deterministic context builder и LLM interpreter.
- [x] Сформировать strict JSON Schema с лимитами длины для всех обязательных разделов.
- [x] Добавить schema validation, retry, safe fallback и prompt-injection boundaries.
- [x] Покрыть Sun/Moon/ASC, Rahu/Ketu, strengths/weaknesses, purpose, relationships, career/money, aspects и доступные периоды.
- [ ] Не имитировать транзиты/периоды, если deterministic-функционал отсутствует; завести отдельную задачу.
- [x] Передавать canonical chart context в follow-up-вопросы и проверять отсутствие выдуманных placements.

## Фаза 4 — PDF

- [x] Зафиксировать ADR по WeasyPrint vs Puppeteer/headless Chromium vs react-pdf/pdfmake.
- [x] Переработать cover, full wheel+legend, тематические страницы и final CTA.
- [x] Синхронизировать все labels с i18n RU/EN и вынести проектный URL/branding в конфигурацию.
- [x] Добавить footer и page numbering без пустых страниц.
- [x] Проверить три профиля входных данных, длину текста, SVG, overflow и печатный контраст.

## Фаза 5 — routing, агенты и инструменты

- [x] Построить фактическую карту выбора агента: UI/FSM/API/agent registry/skill narrowing.
- [x] Проверить, есть ли центральный classifier; deterministic router добавлен с explicit-selection precedence.
- [x] Подготовить 20–30+ кейсов RU/EN/code-switching/границы/опечатки/off-topic.
- [x] Зафиксировать expected vs actual agent, результат и confidence.
- [x] Исправить найденные провалы без регрессии.
- [x] Описать persona/voice/rules/tools/limits всех агентов: Лилит, Урания, Мадам Ленорман, Мира и обнаруженных расширений.
- [x] Проверить различимость voice и правильность fallback.

## Фаза 6 — полный аудит UI и release gate

- [x] Инвентаризировать каждого агента, tool, ключевые экраны результата и состояния загрузки/ошибки через registry, runtime, Mini App and selfcheck.
- [x] Проверить raw Markdown, cards/loading/error/empty states, reduced motion and mobile overflow contracts.
- [x] Запустить unit/integration, routing matrix, PDF smoke, screenshot, design and JavaScript syntax checks.
- [x] Проверить source/artifacts на реальные secrets/PII; найдены только ожидаемые env-name references и документационные placeholders.
- [x] Обновить `AGENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `CHANGELOG.md` в том же изменении.
- [x] Подготовить финальный отчёт с тестами, benchmark и визуальными артефактами.

## Обнаруженные смежные задачи

- [x] Устранить рассинхронизацию документации о PDF: runtime/deployment smoke подтвердил WeasyPrint как текущий renderer; альтернативы оставлены ADR fallback.
- [x] Уточнить API-контракт: текущая карта versioned как `natal_schema_version: 2`, canonical calculation metadata выделен в `chart_contract.py`.
- [x] Проверить frontend comment B1: geometry scaling уменьшает риск обрезания, collision avoidance для планет реализован.
- [ ] Добавить safe live-LLM test через mock/provider fixture; sandbox selfcheck показал пустые ответы от configured proxy и корректно ушёл в offline fallback.
- [x] Отдельно проверить, не используется ли `True Node` как product convention без пользовательской настройки Mean/True Node; convention явно отражена в canonical contract и PDF.

## Фаза 7 — ToV, PDF density и renderer decision — 2026-08-25

- [x] Провести широкий RU/EN semantic audit user-facing surfaces, active prompts, file-backed skills, offline fallbacks, Mini App и PDF.
- [x] Переписать активные рационализирующие оговорки в уверенный evidence-first голос; сохранить safety/crisis/age/privacy, medical/legal/financial boundaries и запрет на выдуманные расчёты.
- [x] Упростить literal negative examples в specialist SYSTEM contracts; по narrow release pattern остаточные semantic matches ограничены `app/core/safety.py` и медицинскими границами Mira/Urania; технические термины и age/legal copy классифицированы отдельно.
- [x] Увеличить PDF typography: body `12.4pt`, line-height `1.56`, H2 `24pt`, H3 `17pt`; убрать лишнюю матрицу и собрать тематические главы в две колонки.
- [x] Провести deterministic QA на 3 неперсональных профилях × RU/EN: 6/6 документов собраны WeasyPrint, каждый 6 страниц, marker-free, без overflow по визуальной проверке.
- [x] Реально протестировать AstroChart 3.0.2 (MIT) и Kerykeion 5.12.9 classic/modern; сохранить SVG и metrics artifacts.
- [x] Принять production decision: оставить собственный canonical-data-driven SVG wheel; внешние renderer outputs использовать как reference, не добавляя второй runtime/adapter.
- [x] Обновить ADR, architecture/agent docs, changelog и финальный audit report.
- [x] Повторить release gate после последней правки prompt contracts: полный pytest, JS syntax, compileall, design contract, selfcheck, routing/renderer smokes и `git diff --check`.

### Принятые ограничения

Шесть страниц PDF приняты как плотный, но читаемый результат при сохранении body `12.4pt`, полной calculation reference, wheel/matrix anchors, пяти тематических блоков и closing. Сокращение до пяти страниц допустимо только структурной компоновкой без уменьшения основного текста.

Миграция уже сохранённых административных `content_items` не выполняет безусловную перезапись: новые defaults применяются для новых/пустых значений, а кастомный контент требует отдельного reviewed migration.


## Фаза 8 — zero-baseline, traceability и scheduler operations — 2026-08-25

- [x] Зафиксировать текущую ветку, commit, чистый baseline и полный локальный gate в `docs/audit/baseline_master_2026-08-25.txt`.
- [x] Создать `docs/PROJECT_MAP.md` и машинный `docs/FILE_AUDIT.csv` через повторяемый `scripts/generate_project_audit.py` (746 файлов исключая vendor/cache).
- [x] Создать `docs/TRACEABILITY_MATRIX.md` с evidence/status/owner для Gate 0–5 и Definition of Done.
- [x] Выполнить disposable plaintext/encrypted SQLite backup/restore drill; сохранить честный статус fixture-only.
- [x] Добавить `scheduler_leases` и атомарный single-owner lease с stale recovery, failure accounting и bounded operator status.
- [x] Расширить `scripts/ops_alerts.py` сигналами scheduler missing/stale/failed без вывода private content.
- [x] Добавить regression tests на двух соединениях SQLite, expired lease, failure accounting и ops parsing.
- [ ] Не закрывать внешние gates по наличию локального кода: live LLM/palm, real Telegram devices, legal/privacy, off-site backup, production alerts/on-call, payment sandbox, capacity и Dubai/UAE approvals остаются OPEN/BLOCKED.
