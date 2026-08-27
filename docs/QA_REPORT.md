# OracleAI — QA report

Дата: **2026-08-27**. Проверка выполнена после внедрения `prompt-contract-v2`, `shared-context-v1`, `natal-json-v1`, hybrid palm CV и versioned Tarot knowledge artifact.

## Итог

Полный набор тестов проекта завершился успешно: **100% passed, 1 skipped**. Дополнительно выполнены компиляция всех Python-модулей и отдельный локальный benchmark CV на 15 реальных изображениях из repository/public fixtures.

| Область | Проверка | Результат |
|---|---|---|
| Agent context | `test_agent_context.py`, `test_agent_context_integrity.py`, `test_agent_file_harness.py` | Passed |
| Shared Context | 4 новых regression tests | Passed |
| Privacy | memory-off, self-delete/anonymization, tool restrictions | Passed |
| Palm API | JPEG/PNG/WebP upload, strict JSON, retry, no raw image persistence | Passed |
| Palm prompt | Mira receives `[SHARED_CONTEXT]` and `[NATAL_CONTEXT_JSON]` | Passed |
| Tarot | deterministic draw/ledger/contract and 78-card artifact | Passed; JSON contains 78 cards and 10 spreads |
| Full repository | `pytest -q` | Passed; 1 skipped |
| Syntax | `python3 -m compileall -q app scripts/...` | Passed |

## Shared Context acceptance checks

`shared_context.record_recommendation()` сохраняет только bounded recommendation при `memory_enabled=1`, связывает её с agent/source reference и ограничивает окно 30 днями. `prompt_block()` передаёт последние 8 событий, текущий вопрос и единый transit snapshot; все текстовые события маркируются как untrusted data. При отключённой памяти сохранённые рекомендации не возвращаются. `users.anonymize()` удаляет и events, и transit snapshots вместе с остальным личным контентом.

`shared_context._transit_snapshot()` строит активное небо через `chart_products.build_transit_contract`, кэширует его по пользователю и дате, а после истечения TTL обновляет через portable `ON CONFLICT DO UPDATE`. Это предотвращает раздельный и несовместимый пересчёт транзитов у разных агентов.

## Palm CV benchmark

Скрипт `scripts/benchmark_palm_cv.py` запускает на одном и том же наборе 15 фото: capture precheck, MediaPipe Hand Landmarker, ONNX fp16 и ONNX int8 line segmentation. Official MediaPipe model asset находится в `models/hand_landmarker.task`; ONNX models имеют checksum allow-list.

| Метрика | Результат |
|---|---:|
| Фото | 15 |
| `palm_vision` classified `usable` | 4 |
| MediaPipe `hand detected` | 13 |
| ONNX fp16 `detected` | 12 |
| ONNX int8 `detected` | 12 |
| fp16/int8 status agreement | 15/15 |

Это **не accuracy study**: для fixtures нет human-annotated ground truth. Результат подтверждает только запускаемость, bounded output and conservative gating. Перед public launch нужен consented dataset 15–20+ images with ground-truth labels, left/right and folded-edge metadata.

## Mira skill and tool-routing verification

Мира обнаруживает **34 file-backed skills**. В initial system prompt не попадают полные тела всех skills: `skill_context()` выдаёт компактный `[SKILL_INDEX]`, короткие description/version/tool/dependency cards, routed hints и сокращённый handbook synopsis. Полное тело появляется только после явного tool call `activate_palm_skill` с именем из индекса. Dependency resolution сохраняет обязательные зависимости, например `heart-line-depth` активирует `anti-barnum-protocol` перед собственным workflow.

Целевой regression subset после подключения lazy activation: **37 passed**. Проверены file-profile discovery, routing top-3, компактность prompt, отсутствие `ACTIVE_SKILL` bodies в initial prompt, реальный executor activation, Mira allow-list из `activate_palm_skill`, `palm_scanner`, `palm_photo_guide`, `palm_history`, strict palm integration и placement/safety cases. Initial Mira skill index был 8,426 символов на вопросе «фото ладони и линия сердца», что ниже прежней полной body-injection модели; `activate_palm_skill` возвращает только запрошенный skill и его зависимости.

## Known limitations and release gates

Мира не получает raw mask и не делает palmistry claims из segmentation confidence. ONNX covers heart/head/life only; relationship, children and travel lines require folded-edge capture and remain vision evidence only. MediaPipe detects geometry but does not interpret palmistry. No end-to-end third-party palmistry engine was accepted as a production dependency.

Не выполнены и намеренно не объявлены закрытыми следующие внешние gates: live provider quality evaluation, mobile-device QA, production Docker/deployment, legal/privacy review for uploaded palm photos, and licensing review for every redistributable model. Existing `PALM_SYSTEM` fallback remains available when optional CV dependencies fail.
