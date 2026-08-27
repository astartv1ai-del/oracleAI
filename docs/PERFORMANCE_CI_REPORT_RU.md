# Performance и CI/CD: итог оптимизации OracleAI

**Дата измерения:** 27 августа 2026 года
**Репозиторий:** `astartv1ai-del/oracleAI`
**Режим измерения:** локальный FastAPI QA-сервер, Chromium headless, viewport 1440×900, synthetic user `10001`, `reducedMotion=reduce`, production bundle включён через `BUNDLE_ASSETS=1`.

## Резюме

Выполнена безопасная Performance-фаза для Telegram Mini App без изменения бизнес-логики. Девятнадцать JavaScript-модулей и девятнадцать CSS-модулей теперь собираются в два content-hashed production-файла. HTML в production отдаёт только эти два bundle-запроса вместо 38 отдельных запросов исходных CSS/JS-модулей. Для разработки сохранён source-mode; production bundle можно воспроизводимо проверять в локальном QA через явный `BUNDLE_ASSETS=1`.

Параллельно сокращён статический payload: шесть неиспользуемых тяжёлых design masters вынесены из `miniapp/img` в `design/sources`, а runtime fallback `oracle-mark.png` пересохранён в 256×256. Добавлены проверки manifest, покрытия исходных модулей, статических ссылок и API-контракта index/cache. Полная SPA-матрица из десяти состояний после исправления семантики ask-chip дала **0 axe violations во всех состояниях**, а Lighthouse дал **Accessibility 100, Best Practices 100 и SEO 100 во всех состояниях**. Performance в локальном CPU/HTTP-окружении колебался от 31 до 94, поэтому этот результат нельзя интерпретировать как гарантированный production Performance score: он измеряется отдельно и чувствителен к локальной нагрузке, API-ответам и отсутствию HTTPS/staging-контекста.

## Что было изменено

| Область | Реализация | Контрольный эффект |
|---|---|---|
| Production frontend | `scripts/build_frontend.mjs` объединяет текущий порядок 19 JS и 19 CSS модулей, минифицирует их через pinned `esbuild` и создаёт 12-символьные content hashes | 38 запросов CSS/JS превращены в 2 bundle-запроса |
| HTML serving | `app/api/main.py` использует `dist/manifest.json` только для production или явного `BUNDLE_ASSETS=1`; обычный `DEV_MODE` оставляет исходные файлы | Source QA и разработка не зависят от stale bundle |
| Cache policy | `app.<12hex>.min.js/css` получают `public, max-age=31536000, immutable`; исходные static assets остаются с TTL 1 час; HTML/API — `no-cache` | Безопасный долгий cache для неизменяемых bundle-имен |
| Docker build | `infra/Dockerfile` добавляет Node 22.13 multi-stage builder и копирует только `miniapp/dist` в Python image | Production image собирает bundle из исходников, а не из локального состояния |
| Static payload | masters перемещены в `design/sources/`, исключены из `.dockerignore`; runtime mark уменьшен с 1254×1254 до 256×256 | `oracle-mark.png`: 1,502,xxx байт → 91,482 байта; design masters больше не раздаются `/static` |
| Layout stability | Добавлены intrinsic `width`/`height`, `decoding="async"` для runtime avatar images; первый eager portrait получил `fetchpriority="high"` | Меньше неопределённости размеров и лишнего layout shift |
| Accessibility | `.agent-ask-chips` получил реальные `<button>` вместо кликабельных `<span>` | Исправлена axe-ошибка `scrollable-region-focusable` в Guides |
| Static references | `scripts/check_static_asset_references.py` проверяет literal `/static`, `/public`, `/admin/static`, CSS `url()` и `@import`; динамические template paths пропускаются осознанно | Broken asset path становится CI failure |

> Важное различие: прежнее значение **96** относилось к Lighthouse **Best Practices**, а не к подтверждённому Performance score. В свежем bundled-прогоне Best Practices уже равен 100 во всех десяти состояниях. Это не означает, что локальный Performance score должен быть 100.

## Размеры и запросы

| Метрика | До оптимизации | После оптимизации | Изменение |
|---|---:|---:|---:|
| Отдельные CSS/JS запросы для 19+19 модулей | 38 | 2 | −94,7% |
| Исходный JS-массив модулей | 338 231 байт | — | — |
| Исходный CSS-массив модулей | 295 746 байт | — | — |
| Production JS bundle | — | 386 973 байта | — |
| Production CSS bundle | — | 224 230 байт | — |
| Суммарный source JS+CSS | 633 977 байт | — | — |
| Суммарный raw bundle JS+CSS | — | 611 203 байта | −3,6% до HTTP-сжатия |
| Runtime `oracle-mark.png` | 1254×1254, около 1,5 МБ | 256×256, 91 482 байта | −93,9% |
| Design masters в `miniapp/img` | 6 тяжёлых файлов | 0 | вынесены из static tree |

Снижение количества запросов является основным выигрышем этой фазы. Дополнительное HTTP-сжатие должен выполнять production reverse proxy; в текущем `infra/Caddyfile` отдельная директива compression не добавлялась, поэтому в отчёте не заявляется Brotli. Повторное добавление gzip/Brotli на уровне FastAPI без проверки Caddy могло бы дать дублирование или неверные заголовки.

## Bundled Lighthouse matrix

Матрица содержит десять SPA-состояний: home, guides, четыре chat-состояния и четыре profile tabs. Значения ниже — один воспроизводимый локальный запуск, а не обещание постоянного production score.

| Состояние | Performance | Accessibility | Best Practices | SEO | Axe violations |
|---|---:|---:|---:|---:|---:|
| Home | 33 | 100 | 100 | 100 | 0 |
| Guides | 63 | 100 | 100 | 100 | 0 |
| Chat · Oracle | 63 | 100 | 100 | 100 | 0 |
| Chat · Astro | 61 | 100 | 100 | 100 | 0 |
| Chat · Tarot | 61 | 100 | 100 | 100 | 0 |
| Chat · Chiromant | 61 | 100 | 100 | 100 | 0 |
| Profile · Summary | 58 | 100 | 100 | 100 | 0 |
| Profile · Chart | 89 | 100 | 100 | 100 | 0 |
| Profile · History | 90 | 100 | 100 | 100 | 0 |
| Profile · Memory | 62 | 100 | 100 | 100 | 0 |

В каждом состоянии axe сообщил один `incomplete` по `color-contrast`. Это не violation и соответствует ранее зафиксированной зоне manual review для декоративных artwork/pseudo-element gradients. Автоматический gate блокирует только реальные violations; Accessibility Lighthouse блокируется при результате ниже 100.

## Точный CI/CD pipeline после изменений

В workflow добавлен отдельный job `frontend-quality`; существующий Python job сохранён. Поэтому после каждого `push` и `pull_request` выполняются следующие группы проверок.

| Job | Проверки |
|---|---|
| `quality` | Python 3.12 setup, pinned Python dependencies, Ruff, `compileall`, syntax-check всех JS, repository hygiene, skill/agent stability scripts, Vedic/Mira benchmarks, cache-busting policy, design contract, LLM golden-set evaluator, migration-focused pytest, полный `pytest tests/`, `pip_audit`, selfcheck и production-readiness `release_gate` |
| `frontend-quality` | Node 22.13 setup, Python QA dependencies, Chromium/system libraries, `npm ci --ignore-scripts`, `npm run build:frontend`, `check_frontend_build.py`, `check_static_asset_references.py`, JS syntax включая scripts, synthetic QA user seed, FastAPI health wait, полный `npm run test:axe`, полный `npm run test:lighthouse` с `performance,accessibility,best-practices,seo` |
| Evidence | Python job uploads LLM report; frontend job uploads десять axe JSON, десять Lighthouse JSON, `summary.json` и API log через `actions/upload-artifact@v4` |

Browser gate намеренно **не блокирует merge по Performance score**: текущий локальный запуск показал сильную вариативность 31–94, а deterministic threshold требует HTTP(S) staging/production, стабильной базы/API и согласованной throttling-политики. При этом Lighthouse Performance продолжает измеряться и сохраняться как evidence, а реальные accessibility regressions блокируют job.

## Воспроизводимые команды

```bash
npm ci --ignore-scripts
npm run build:frontend
python3 scripts/check_frontend_build.py
python3 scripts/check_static_asset_references.py
python3 scripts/check_cache_busting.py
python3 scripts/check_design_contract.py
python3 -m pytest tests/test_api.py -q -p no:cacheprovider --timeout=120
```

Для полного локального bundled-аудита необходим QA-сервер с seeded user `10001`:

```bash
python3 scripts/seed_visual_user.py --db data/oracle.db
APP_ENV=dev DEV_MODE=1 BUNDLE_ASSETS=1 DB_PATH=$PWD/data/oracle.db \
  python3 -m uvicorn app.api.main:app --host 127.0.0.1 --port 8080

QA_OUT_DIR=bundled-axe-fixed npm run test:axe
QA_OUT_DIR=bundled-lighthouse-fixed \
  LH_CATEGORIES=performance,accessibility,best-practices,seo \
  npm run test:lighthouse
```

## Ограничения проверки

Docker smoke test в текущем sandbox не был выполнен: бинарник `docker` отсутствует. Сам Dockerfile и multi-stage syntax были проверены чтением конфигурации и локальными frontend/Python smoke checks, но окончательная проверка `docker build` должна выполняться на runner или машине с Docker daemon. Также локальный аудит использует HTTP loopback и synthetic QA user; production score следует снимать на опубликованном HTTPS staging URL с фиксированной сетевой эмуляцией.

### References

[1]: https://developer.chrome.com/docs/lighthouse/overview "Chrome Lighthouse documentation"
[2]: https://www.deque.com/axe/core-documentation/ "Deque axe-core documentation"
