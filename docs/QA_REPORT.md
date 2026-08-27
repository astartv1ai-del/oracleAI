# OracleAI — QA report

Дата: **2026-08-27**. Проверка выполнена после внедрения `prompt-contract-v2`, `shared-context-v1`, `natal-json-v1`, hybrid palm CV, semantic evidence views, fp16/int8 ensemble и versioned Tarot knowledge artifact.

## Итог

Полный набор тестов проекта завершился успешно: **100% passed, 1 skipped**. Дополнительно выполнены компиляция всех Python-модулей и отдельный локальный benchmark CV на 15 реальных изображениях из repository/public fixtures.

| Область | Проверка | Результат |
|---|---|---|
| Agent context | `test_agent_context.py`, `test_agent_context_integrity.py`, `test_agent_file_harness.py` | Passed |
| Shared Context | 4 новых regression tests | Passed |
| Privacy | memory-off, self-delete/anonymization, tool restrictions | Passed |
| Palm API | JPEG/PNG/WebP upload, strict JSON, retry, enhanced focus views, no raw image persistence | Passed |
| Palm prompt | Mira receives `[SHARED_CONTEXT]` and `[NATAL_CONTEXT_JSON]` | Passed |
| Tarot | deterministic draw/ledger/contract and 78-card artifact | Passed; JSON contains 78 cards and 10 spreads |
| Full repository | `pytest -q` | Passed; 1 skipped |
| Syntax | `python3 -m compileall -q app scripts/...` | Passed |

## Shared Context acceptance checks

`shared_context.record_recommendation()` сохраняет только bounded recommendation при `memory_enabled=1`, связывает её с agent/source reference и ограничивает окно 30 днями. `prompt_block()` передаёт последние 8 событий, текущий вопрос и единый transit snapshot; все текстовые события маркируются как untrusted data. При отключённой памяти сохранённые рекомендации не возвращаются. `users.anonymize()` удаляет и events, и transit snapshots вместе с остальным личным контентом.

`shared_context._transit_snapshot()` строит активное небо через `chart_products.build_transit_contract`, кэширует его по пользователю и дате, а после истечения TTL обновляет через portable `ON CONFLICT DO UPDATE`. Это предотвращает раздельный и несовместимый пересчёт транзитов у разных агентов.

## Palm CV benchmark

Скрипт `scripts/benchmark_palm_cv.py` запускает на одном и том же наборе 15 фото: capture precheck, MediaPipe Hand Landmarker, ONNX fp16/int8 line segmentation и full-scope OpenCV candidate search. Official MediaPipe model asset находится в `models/hand_landmarker.task`; ONNX models имеют checksum allow-list. Full-scope engine каталогизирует все 16 именованных line zones и дополнительно mounts/fingers/markings, но выдаёт только bounded candidate segments; semantic line identity остаётся за vision adjudicator.

| Метрика | Результат |
|---|---:|
| Фото | 15 |
| `palm_vision` classified `usable` | 4 |
| MediaPipe `hand detected` | 13 |
| ONNX fp16 `detected` | 12 |
| ONNX int8 `detected` | 12 |
| fp16/int8 status agreement | 15/15 |
| Full-scope candidate evidence | 15/15 фото |
| Full-scope candidate segments | 798 суммарно |
| Full line catalog | 16 named line zones |
| Open-palm view classification | 13/15 |

Это **не accuracy study**: для fixtures нет human-annotated ground truth. Результат подтверждает только запускаемость, bounded output and conservative gating. Перед public launch нужен consented dataset 15–20+ images with ground-truth labels, left/right and folded-edge metadata.

## User palm-series semantic hardening acceptance

На 13 пользовательских кадрах (12 новых плюс базовый) MediaPipe обнаружил руку в **13/13**, full-scope candidate evidence получен в **13/13**, folded-edge классифицирован в **11/13**, а relationship/children/travel стали доступны для semantic adjudication в **11/11 folded-edge** кадрах. После semantic hardening каждый folded-edge pipeline request передал primary image и два bounded in-memory focus views (`hand_roi_enhanced`, `pinky_edge_enhanced`); открытый кадр получил только hand ROI view. View-aware ONNX ensemble помечает folded-edge как `out_of_domain`, чтобы principal-line model не создавала ложное `no_lines`; full-scope и edge focus view остаются источниками для relationship/children/travel adjudication. Полный `palm.analyze_and_save` завершился `complete` на **12/12 новых** кадрах, line contract был полным, raw storage flags — false.

Это acceptance wiring/operational test с controlled schema-valid vision response. Live provider semantic quality не закрыта: smoke test ранее получил upstream 403/invalid structured response и безопасный `needs_photo`. Candidate evidence и focus crops не являются доказательством семантической линии; для accuracy нужны consented human-annotated images.

## Mira skill and tool-routing verification

Все четыре агента обнаруживают свои file-backed skills: Mira — **34**, Lilith — 31, Lenormand — 35, Urania — 39. В initial system prompt не попадают полные тела всех skills: `skill_context()` выдаёт компактный `[SKILL_INDEX]`, короткие description/version/tool/dependency cards, routed hints и сокращённый handbook synopsis. Полное тело появляется только после явного generic tool call `activate_skill({skill_name})`; домен подставляется runtime-сервером. Dependency resolution сохраняет обязательные зависимости, например `heart-line-depth` активирует `anti-barnum-protocol` перед собственным workflow.

Целевой regression subset после подключения lazy activation, full-scope CV, semantic evidence views и ONNX ensemble проходит полностью. Проверены file-profile discovery для всех агентов, routing top-3, компактность prompt, отсутствие `ACTIVE_SKILL` bodies в initial prompt, реальный executor activation во всех четырёх доменах, Mira allow-list из `activate_skill`, `palm_scanner`, `palm_photo_guide`, `palm_history`, strict palm integration и placement/safety cases. Initial Mira skill index был 8,426 символов на вопросе «фото ладони и линия сердца»; `activate_skill` возвращает только запрошенный skill и его зависимости.

## Known limitations and release gates

Мира не получает raw mask, raw edge map и не делает palmistry claims из segmentation confidence. View-aware ONNX ensemble covers heart/head/life only on open-palm domain and exposes model agreement, confidence margin and bbox IoU; `palm_full_scope` combines CLAHE/Canny with blackhat-ridge candidate search, limits output to 32 strongest bounded segments and assigns stable segment IDs, но не присваивает им семантический label. `palm_evidence` supplies deterministic in-memory hand ROI and folded-edge focus views; it never persists them. Relationship, children and travel lines require folded-edge capture and remain vision-adjudicated evidence only. MediaPipe detects geometry but does not interpret palmistry. No end-to-end third-party palmistry engine was accepted as a production dependency.

Не выполнены и намеренно не объявлены закрытыми следующие внешние gates: live provider quality evaluation, mobile-device QA, production Docker/deployment, legal/privacy review for uploaded palm photos, and licensing review for every redistributable model. Existing `PALM_SYSTEM` fallback remains available when optional CV dependencies fail.
