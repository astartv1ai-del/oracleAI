# OracleAI — WebView, Load и Palm Quality Report

Дата запуска: **2026-08-27**  
Окружение: локальный FastAPI preview, isolated SQLite load DB, Chromium headless для WebView emulation.  
Автор: **Manus AI**

## Executive summary

Проверка локального Telegram-like WebView прошла: CSS поддерживает `safe-area-inset-*` и `100dvh`, приложение не создаёт горизонтального overflow, keyboard-resize обработчик реагирует на уменьшение `visualViewport` на 320px, а composer возвращается к исходному inset после восстановления viewport. Это доказывает корректность web implementation contract, но не заменяет ручную проверку внутри настоящего Telegram WebView на iOS и Android.

Изолированный HTTP load test охватил 300 synthetic users, 32 concurrent workers, 3,300 запросов к read API и четырём агентским маршрутам. После подготовки consented/entitled synthetic dataset получено **3,300/3,300 ответов 2xx**, throughput **786.42 requests/s**, без 5xx, traceback или slow/error events в логах. Agent POST routes тестировались с `LLM_PROVIDER=off`, поэтому это нагрузка на API, auth, rate-limit, persistence и offline fallback, а не тест внешнего LLM provider capacity.

Palm benchmark разделён на operational evidence и semantic accuracy. На 15 repository/public fixtures full-scope evidence был получен в 15/15, ensemble agreement — 13/15, но hand geometry обнаружила руку только в 5/15 из-за неоднородности fixtures. На пользовательской серии из 12 новых кадров ensemble agreement составил 12/12; 5 кадров получили major-line evidence, 7 — conservative `no_lines`. **Semantic precision/recall не вычислялись**, потому что в доступном наборе нет ground-truth масок, полилиний и adjudicated labels.

## 1. Telegram-like WebView: safe-area и keyboard

### Test profile

Использован iPhone-like browser profile: viewport 390×844 CSS px, device scale factor 3, touch enabled, mobile user agent и locale `ru-RU`. Страница открывалась в chat state через dev user на локальном FastAPI preview. Исходные пользовательские данные и изображения в этот тест не включались.

| Проверка | Результат |
|---|---:|
| `visualViewport` available | PASS |
| Initial viewport | 390×844 |
| `document.body.scrollWidth` | 390px |
| Horizontal overflow | **0px** |
| CSS `env(safe-area-inset-top/bottom)` support | PASS |
| CSS `100dvh` support | PASS |
| Page errors | **0** |
| Chat composer initial bottom padding | 12px in Chromium, where native inset resolves to 0 |
| Simulated keyboard delta | 320px |
| Composer padding while keyboard is open | 328px |
| Composer padding after viewport restore | 12px |
| WebView QA verdict | **PASS** |

В production CSS safe-area используется в header, screen bottom padding, composer, bottom navigation, sheets, modals и toast. Chromium не эмулирует native Telegram inset и поэтому возвращает 0 для фактической safe-area величины; тест подтвердил поддержку CSS и отсутствие collapse, но физический inset нужно проверить на реальном устройстве.

Keyboard test dispatches a controlled `visualViewport.resize` event after reducing viewport height by 320px. Это подтверждает используемый application handler и восстановление состояния. Реальная IME-анимация, selection behavior и Telegram-specific viewport quirks требуют manual iOS/Android WebView pass.

## 2. HTTP load test: API и агенты

### Workload

Нагрузка выполнялась на отдельном `/tmp/oracleai-load.db` с 300 пользователями. Перед основным прогоном каждому synthetic user были выставлены `age_confirmed=1`, `onboarded=1`, `status='active'` и future VIP entitlement, чтобы 403/402 от access guard не маскировали capacity API. `LLM_PROVIDER=off` исключил внешние вызовы и стоимость provider requests.

В workload вошли `/api/me`, `/api/agents`, `/api/today`, `/api/moon/week`, `/api/sky`, `/api/horoscope/all`, GET history для `oracle`, `astro`, `tarot`, `chiromant`, а также POST agent route для каждого из четырёх агентов.

| Metric | Result |
|---|---:|
| Synthetic users | 300 |
| Concurrent workers | 32 |
| Total requests | 3,300 |
| 2xx responses | 3,300 |
| Success rate | **100%** |
| Wall time | 4,196.21ms |
| Throughput | **786.42 req/s** |
| 5xx responses | 0 |
| Tracebacks in log | 0 |
| Slow/error log events | 0 |
| Prometheus clean-run counters | GET 3,001 × 200; POST 300 × 200 |

| Route group | Requests | p50 | p95 | p99 | Status |
|---|---:|---:|---:|---:|---|
| `GET /api/me` | 300 | 45.18ms | 57.32ms | 688.95ms | 200 × 300 |
| `GET /api/today` | 300 | 36.21ms | 46.76ms | 669.06ms | 200 × 300 |
| `GET /api/agents` | 300 | 8.52ms | 11.81ms | 666.99ms | 200 × 300 |
| `GET /api/chat/{agent}` | 1,200 | 34.09–35.70ms | 43.21–45.66ms | 125.73–134.10ms | 200 × all |
| `POST /api/chat/{agent}` | 300 | 206.66–207.80ms | 286.93–303.85ms | 340.03–520.55ms | 200 × all |
| `GET /api/moon/week` | 300 | 1.79ms | 3.08ms | 15.38ms | 200 × 300 |
| `GET /api/sky` | 300 | 1.80ms | 3.02ms | 647.68ms | 200 × 300 |
| `GET /api/horoscope/all` | 300 | 2.62ms | 4.17ms | 18.11ms | 200 × 300 |

The aggregate p99 tail is materially higher than p50 because SQLite/WAL contention and concurrent Python scheduling create occasional outliers. This run is a local directional baseline, not a production capacity SLO. A production capacity claim requires staging hardware, realistic network, provider-on load, longer duration, ramp-up, steady-state and soak phases.

## 3. Palm-line recognition quality

### 3.1 Repository/public fixture benchmark

The reproducible benchmark contained 15 fixtures. Its metrics measure capture quality, hand geometry, candidate evidence and ONNX model behavior; they do not measure semantic palmistry correctness.

| Metric | Result |
|---|---:|
| Fixtures | 15 |
| Mean precheck score | 0.5423 |
| Precheck score p50 | 0.5450 |
| Full-scope candidate evidence | 15/15 (100%) |
| Full-scope status | `candidate_evidence` in 15/15 |
| Hand geometry detected hand | 5/15 (33.3%) |
| ONNX ensemble `detected` | 10/15 |
| ONNX ensemble `no_lines` | 3/15 |
| ONNX ensemble `needs_vision_review` | 2/15 |
| fp16/int8 agreement | 13/15 (86.7%) |
| Major heart-line evidence | 9/15 |
| Major head-line evidence | 9/15 |
| Major life-line evidence | 12/15 |
| Raw masks/edge maps retained | 0 |

The low hand-detection rate is a property of the heterogeneous fixture set and capture quality, not a semantic accuracy score. Full-scope CV intentionally continues to provide bounded candidate evidence even when hand geometry is unavailable, while the semantic layer must abstain when anatomy or visual evidence is insufficient.

### 3.2 User photo series

The uploaded series was evaluated without persisting the original images, masks or edge maps. The separate 13-frame capture aggregate contained 11 folded-edge frames and 2 open-palm frames; hand geometry and full-scope evidence were available in 13/13. The 11 folded-edge frames exposed relationship/children/travel edge-search regions. In the 12-frame view-aware ONNX series, 5/12 received major-line `detected`, 7/12 received conservative `no_lines`, model agreement was 12/12, and raw-storage flags were clear in 12/12.

`detected` and `no_lines` here describe the auxiliary three-class ONNX evidence model and its view-aware abstention rules. They do **not** assert that a named palmistry line is semantically present or absent. Relationship, children and travel lines remain vision-adjudication zones that require visible edge anatomy and a valid vision provider response.

### 3.3 Semantic accuracy boundary

No precision, recall, F1, IoU or per-line confusion matrix is reported. The test set does not contain ground-truth masks/polylines for life, head, heart, fate, sun, mercury, relationship, children, travel, mounts or markings, nor an adjudicated label for each candidate segment. Reporting a semantic accuracy percentage from these fixtures would be fabricated.

To calculate real semantic quality, the next dataset should contain consented multi-view images, hand/view metadata, line polylines or masks, visibility labels, folded-edge region labels, mount/finger/marking annotations and a second human adjudication pass. The benchmark should then report per-zone precision/recall/F1, segmentation IoU, abstention rate and calibration of confidence thresholds separately for open-palm and folded-edge views.

## 4. Final verdict

| Area | Verdict |
|---|---|
| Telegram-like safe-area CSS contract | **PASS** |
| Keyboard visualViewport handler simulation | **PASS** |
| Real physical Telegram WebView device validation | **NOT RUN** |
| Local API/agent load baseline | **PASS: 3,300/3,300 2xx** |
| Provider-on agent capacity | **NOT RUN**; intentionally isolated with LLM off |
| Palm CV operational evidence | **PASS within declared contract** |
| Palm semantic accuracy | **NOT CLAIMED**; ground truth unavailable |

The artifacts attached to this report contain only aggregate metrics and structured QA output. No raw user photo, raw segmentation mask or raw provider response is included.
