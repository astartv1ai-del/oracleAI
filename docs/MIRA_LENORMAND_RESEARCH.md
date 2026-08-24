# Mira и Madame Lenormand: исследование foundations и план конкурентного усиления

**Дата:** 24 августа 2026 года  
**Статус:** research-backed implementation note  
**Автор:** Manus AI

## Executive conclusion

Для Mira наиболее реалистичная production-архитектура состоит из четырёх слоёв: deterministic capture precheck, hand detection/handedness, rectification/landmarks и отдельный palm-line segmentation adapter. Ни MediaPipe, ни найденные GitHub-проекты не дают готовой доказательной «хиромантии»: они помогают с геометрией изображения и computer-vision pipeline, но не превращают традиционные трактовки в факты.

Для Madame Lenormand основа должна быть не computer vision, а deterministic reading ledger: deck ID, card order, spread positions, orientation, adjacency/combinations, checksum и сохранённый вопрос. RWS Tarot и Petit Lenormand нельзя смешивать: нынешний агент работает с 78-карточной RWS-колодой, тогда как классический Lenormand — отдельная 36-карточная система. Поэтому найденные RWS datasets подходят как reference/data-layer для будущего deck adapter, но не как готовая Lenormand-колода.

## Исследованные foundations

| Кандидат | Что подтверждено первоисточником | Что можно переиспользовать | Ограничение |
|---|---|---|---|
| [MediaPipe Hand Landmarker][1] | 21 image/world landmarks, handedness, still/video/live inputs, configurable confidence thresholds | capture geometry, hand box, side/orientation, finger joints, rectification inputs | не делает palm-line segmentation и не интерпретирует хиромантию |
| [yeonsumia/palmistry][2] | Apache-2.0 research pipeline: warp, principal-line detection, pixel classification, line-length measurement | reference для rectification + principal-line adapter | notebook-heavy, без releases; нужен audit model/data quality и modern dependency isolation |
| [MuntahaShams/palm-line-detection][3] | preprocessing, line localization, bounding-box visualization и confidence; Heart/Head/Life/Fate classes | reference для annotated evidence UI и confidence display | README называет segmentation/mobile deployment future work; license identifier не найден |
| [gph4ppy/Taroter][4] | public Swift scanner app с Apple Vision/Core ML/Create ML topics | UX/reference для future physical-card scanner | не найдено accuracy benchmark, детальная model card или license context; не готовый interpretation engine |
| [metabismuth/tarot-json][5] | MIT dataset с RWS card metadata и scans; README отдельно описывает image rights | future RWS deck metadata/image adapter | public-domain status изображений зависит от юрисдикции; не Lenormand |
| [dariusk/corpora Tarot][6] | structured card entries: name, rank, suit, keywords, light/shadow meanings; source attribution to Mark McElroy | candidate vocabulary/reference layer | terms of reuse нужно проверять; fortune-telling strings нельзя импортировать verbatim из-за anti-fatalism contract |

## Recommended Mira pipeline

### Сейчас реализовано

OracleAI уже добавил `app/core/palm_vision.py` с deterministic `palm-precheck-v1`. Он измеряет размер, aspect ratio, brightness, contrast и edge sharpness, возвращает bounded score/issues и явно помечает `hand_detection` и `line_segmentation` как `not_attempted`. При invalid/extreme capture vision call блокируется; мягкие blur/contrast warnings остаются видимыми и не ломают существующий JSON-retry contract.

Mira теперь показывает пользователю hand/view evidence, precheck summary, confidence rows для линий/холмов/пальцев и раскрываемую карту зон. Её file-backed harness дополнен skills `visual-evidence-protocol`, `palm-line-topology`, `palm-technique-triangulation` и `capture-rectification`. Это реальное улучшение наблюдаемости, но не заявление о полноценной автоматической segmentation.

### Следующий production step

1. Изолировать MediaPipe adapter в optional dependency или отдельный worker, чтобы основной Telegram API не зависел от тяжёлого CV stack.
2. На собственном consented benchmark dataset проверить hand presence, handedness, crop/occlusion и view classification. Метрики должны быть отдельно от качества символической трактовки.
3. После этого добавить rectified palm ROI и 21-landmark evidence. UI должен отображать только bbox/landmarks при достаточном confidence и позволять пользователю скрыть overlay.
4. Отдельно валидировать principal-line segmentation на размеченных примерах. Для каждой линии хранить `mask/curve confidence`, visible extent и “not enough evidence”; не переводить pixel mask прямо в судьбу, здоровье или сроки.
5. Использовать `yeonsumia/palmistry` только как Apache-2.0 reference/adapter candidate после проверки dataset provenance, model weights, license compatibility, reproducibility и performance на OracleAI photos.
6. Не принимать bounding boxes из `MuntahaShams/palm-line-detection` как точную линию: собственное README описывает segmentation как future work.

### Техники хиромантии, которые должны покрываться evidence-first

Базовый coverage уже включает life/head/heart/fate/Sun/Mercury, mounts, fingers, thumb, hand-shape elements, bracelets, markings, relationship/children/travel views и comparative reading. Следующий expert layer должен выражаться в явных полях и skills: origin/path/termination, continuity, branches, intersections, islands, crosses/stars/squares/triangles, mount topography, finger proportions, thumb mechanics, hand-side context и school-specific terminology. Каждая техника обязана иметь `visibility`, `confidence`, `observed description`, `traditional lens` и `limitation`; отсутствие признака не равно отсутствию качества или черты характера.

## Recommended Madame Lenormand pipeline

### Сейчас реализовано

`tarot.reading_ledger()` создаёт `tarot-ledger-v1` с `rws-78-v1`, spread, card ID/name, position, orientation, adjacent-pair rule и checksum. Один и тот же ledger передаётся в Mini App draw response, agent tool и interpretation evidence block. Lenormand получила skills `card-ledger-evidence`, `combination-synthesis`, `question-to-spread` и `tarot-proof-safety`. Mini App показывает deck, checksum, orientation и adjacency combinations.

Это решает главный trust gap: LLM не выбирает карты и не меняет порядок после draw. Ledger подтверждает только состав и порядок расклада; он не доказывает истинность символического значения или будущего события.

### Следующий production step

1. Сделать explicit `DeckAdapter` с каталогом `rws-78-v1` и будущим `lenormand-36-v1`; не называть RWS-агента Lenormand без ясного deck label.
2. Добавить deck-specific meaning records с provenance, upright/reversed policy и school/version metadata.
3. Расширить combination engine с bounded rules для adjacency, repeated suit, major/minor balance, orientation tension и position semantics. Каждое правило должно иметь unit test и counter-reading.
4. Разделить “question clarification”, “draw”, “interpretation” и “outcome feedback”, чтобы пользователь видел вопрос и выбранный spread до draw.
5. Не копировать внешние fortune-telling strings без licensing review и rewrite под OracleAI non-fatalism safety boundary.
6. Использовать outcome marks только как user feedback, а не как доказательство предсказательной точности.

## Quality and safety gates

Mira quality gate должен блокировать только отсутствие evidence/invalid capture, а не требовать от всех фотографий лабораторной резкости. Lenormand quality gate должен проверять: card uniqueness, card IDs in deck, positions length, orientation enum, ledger checksum stability, no unknown cards, no unrecorded cards in generated text и no deterministic/fatalistic claims. Для обоих агентов нужны RU/EN/code-switched routing cases с expected skill in top-3; top-1 является полезным improvement metric, но не единственным contract.

> Нельзя честно обещать, что внешний open-source проект «понимает руку» или что Tarot dataset делает правильные расклады. Правильный путь — использовать CV projects для измеряемой visual evidence, а традиционные meanings и decision language удерживать в модульном OracleAI harness.

## References

[1]: https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker "Google AI Edge MediaPipe Hand Landmarker"
[2]: https://github.com/yeonsumia/palmistry "yeonsumia/palmistry"
[3]: https://github.com/MuntahaShams/palm-line-detection "MuntahaShams/palm-line-detection"
[4]: https://github.com/gph4ppy/Taroter "gph4ppy/Taroter"
[5]: https://github.com/metabismuth/tarot-json "metabismuth/tarot-json"
[6]: https://github.com/dariusk/corpora/blob/master/data/divination/tarot_interpretations.json "dariusk/corpora Tarot interpretations"
