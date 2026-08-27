# OracleAI — список улучшений и статус внедрения

Дата: **2026-08-27**
Область: Mini App, Telegram-like WebView, API/agents, palm CV и QA tooling.

## Приоритетный список

| Приоритет | Улучшение | Статус | Измеримый результат |
|---|---|---|---|
| P0 | Добавить открытый `/health` probe с DB readiness state | Внедрено | Load balancer и smoke tests получают структурированный 200/500 вместо 404 |
| P0 | Сделать synthetic load dataset воспроизводимым | Внедрено | `seed_load.py` поддерживает `--age-confirmed`, `--active-subscription`, `--onboarded`; production DB защищена `--force` guard |
| P0 | Зафиксировать API/agent load profile как committed CLI | Внедрено | `scripts/load_test_api.py` поддерживает URL, users, concurrency, agent POST и JSON output |
| P0 | Зафиксировать WebView safe-area/keyboard probe как committed CLI | Внедрено | `scripts/telegram_webview_qa.py` проверяет `visualViewport`, `env(safe-area-inset-*)`, `100dvh`, overflow и composer restore |
| P1 | Ввести palm quality summary с ground-truth gate | Внедрено | `scripts/summarize_palm_quality.py` не выдаёт precision/recall/F1/IoU без annotated labels |
| P1 | Сохранить raw-data privacy boundary в QA outputs | Внедрено | Reports содержат только aggregate metrics; raw photos, masks и provider responses не включаются |
| P1 | Усилить quality gates для UI и API tooling | Внедрено | CLI argument validation, deterministic output, explicit synthetic/offline labeling |
| P1 | Реальный Telegram device matrix | Требует внешнего запуска | iOS/Android Telegram WebView, native safe-area inset, physical IME, keyboard animation |
| P1 | Provider-on load/soak test | Требует staging | Real LLM latency, retries, rate limits, cost, timeout and fallback behavior |
| P2 | Размеченный palm semantic benchmark | Требует данных | Per-line precision/recall/F1/IoU, calibration and confusion matrix |
| P2 | Specialized multi-class palm model | После dataset | Semantic segmentation/keypoints for named lines, mounts, markings and folded-edge zones |
| P2 | Distributed load profile | После staging | Multi-process/Redis rate-limit, DB pool, queue workers and sustained throughput |

## Внедрённые изменения

### Root health contract

`GET /health` теперь является unauthenticated process/database readiness probe. Ответ содержит только aggregate state:

```json
{"ok": true, "database": {"ok": true, "schema_tables": 49, "journal_mode": "wal"}}
```

Внутренние тексты, пользовательские данные и секреты в ответ не попадают. Существующий `/api/health` остаётся совместимым для Mini App/admin consumers.

### Воспроизводимый load test

`seed_load.py` теперь позволяет явно подготовить access state для нагрузки: подтверждение возраста, onboarding и future VIP entitlement включаются только флагами. Это устраняет ложные 403/402 при тестировании protected routes и не меняет default synthetic population.

`scripts/load_test_api.py` покрывает read API (`me`, `agents`, `today`, moon, sky, horoscope), GET history всех четырёх агентов и опциональные POST probes. Он работает только с переданным base URL и возвращает route-level p50/p95/p99, max, status distribution, throughput и success rate.

### WebView QA

`scripts/telegram_webview_qa.py` принимает base URL, viewport, DPR, QA state и output path. Он проверяет CSS capability и geometry contract, затем симулирует уменьшение `visualViewport` на 320px и убеждается, что composer получает inset и восстанавливается после resize.

Chromium не эмулирует фактический native Telegram safe-area inset, поэтому script намеренно помечает physical Telegram device QA как отдельный обязательный этап, а не выдаёт ложный PASS.

### Palm quality summary

`scripts/summarize_palm_quality.py` агрегирует benchmark JSON и optional user-series aggregate. Он отдельно сообщает hand detection, full-scope evidence, view types, ONNX ensemble status/agreement и major-line evidence. Semantic metrics остаются `null`, если ground truth не предоставлен.

## Правила запуска

Для локального API baseline сначала создайте отдельную базу и явно включите synthetic access profile:

```bash
PYTHONPATH=. python3 -m scripts.seed_load \
  --count 300 --db /tmp/oracleai-load.db --force \
  --all-active --age-confirmed --active-subscription --onboarded
```

Затем запускайте API в dev-only окружении с `LLM_PROVIDER=off`, а load script направляйте на isolated port:

```bash
APP_ENV=dev DEV_MODE=1 DB_PATH=/tmp/oracleai-load.db LLM_PROVIDER=off \
  PYTHONPATH=. uvicorn app.api.main:app --host 127.0.0.1 --port 8002

python scripts/load_test_api.py --base-url http://127.0.0.1:8002 \
  --users 300 --concurrency 32 --output /tmp/oracleai-load.json
```

Для WebView probe нужен Chromium/Playwright и dev preview:

```bash
python scripts/telegram_webview_qa.py \
  --base-url http://127.0.0.1:8000 \
  --width 390 --height 844 --dpr 3 \
  --output /tmp/oracleai-webview.json
```

Для palm metrics используйте только benchmark aggregates:

```bash
python scripts/summarize_palm_quality.py \
  --input /path/to/palm_benchmark.json \
  --output /tmp/oracleai-palm-quality.json
```

## Фактическая проверка этого change set

- Full `pytest`: **pass**, 1 pre-existing skip.
- Isolated API/agent smoke: **220/220 2xx**, success rate **100%**, **233.1 req/s**, 20 synthetic users, concurrency 8, `LLM_PROVIDER=off`. Это baseline API/auth/persistence/offline fallback, а не provider-on capacity claim.
- Root health: **200**, `ok=true`, database integrity `ok`, WAL, 49 schema tables.
- Telegram-like WebView probe: **pass** на Chromium profile 390×844, DPR 3, touch; safe-area и `100dvh` поддержаны, overflow отсутствует, composer padding восстановлен с 328px до 12px. Native Telegram iOS/Android и physical IME остаются external/manual gate.
- Palm summary: repository benchmark **15 fixtures**, full-scope evidence **15/15**, hand geometry **5/15**, ONNX ensemble detected **10/15**, agreement **13/15**; user-series aggregate **12 files**, raw flags clear; semantic precision/recall/F1/IoU — **null** без annotated ground truth.

## Рекомендуемый следующий этап

Следующим технически наиболее полезным шагом является **consented annotated palm dataset**. Для каждого кадра нужны view type, visibility labels, line polylines/masks, anatomical zones, mounts, fingers, markings и human adjudication. Только после этого можно обучать semantic model и измерять реальное улучшение, а не только увеличение candidate coverage.
