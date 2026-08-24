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

## Source 7 — Wikimedia Commons: Das Spiel der Hofnung / The Game of Hope
URL: https://commons.wikimedia.org/wiki/File:Das_Spiel_der_Hofnung_(The_Game_of_Hope).png

The Commons category lists a complete 36-card board image. The file page identifies the work as the 36 cards of Das Spiel der Hofnung (The Game of Hope), shows an original image of 3,900 × 4,900 pixels (with generated size links including 3,840 × 4,825), and marks the work public domain in its country of origin and the United States because it was published before January 1, 1931. The page still says that file-specific description terms govern reuse, so OracleAI should preserve attribution/source metadata in the asset manifest. The board must be deterministically sliced into 36 card assets after visual coordinate verification; Commons does not provide a ready-to-use 36-file product pack on this page.

Implementation decision: use this historical board only for a clearly labeled `lenormand-36-v1` reference deck. Keep the RWS Geldard assets as a separate `rws-78-geldard-v1` deck. Never let a deck selector merely rename the same cards; deck ID, card count, card catalog, image path, meanings and spread/ruleset must all change together.

## Source 8 — Tarot de Marseille candidates

Search results identified [mixvlad/TarotCards](https://github.com/mixvlad/TarotCards) as a repository containing public-domain and Creative Commons Tarot decks, including Rider-Waite, Sola Busca and Tarot de Marseille, plus Python asset tools. [Wikimedia Commons Tarot de Marseille](https://commons.wikimedia.org/wiki/Category:Tarot_de_Marseille) also provides historical card files, but the category states that each file has its own license. A complete third-school deck can therefore be added only after selecting a specific historical source, checking every file’s license/attribution requirements and recording the source in the deck manifest. The implementation should prefer a historical/public-domain Marseille source over a modern copyrighted recreation.

Visual inspection of the 3,900 × 4,900 original shows a clean 6×6 arrangement of cards numbered 1 through 36, with consistent portrait orientation and visible borders. The board is suitable for deterministic cropping, but crop coordinates must be measured from the original rather than inferred from the browser thumbnail. The final card assets should retain the historical border and playing-card insert because those are part of this source’s visual identity; semantic meanings remain in OracleAI’s own deck catalog.

Tile review 1–2: the top rows show cards 1–10 with complete borders, numbered labels and playing-card inserts; overlap between the tile boundaries is consistent with a 6-column grid. The cards are portrait-oriented and suitable for one-card-per-file crops. No crop should remove the historical number/insert region because it is part of the source identity.

Tile review 3–4: cards 5–14 retain readable borders, numbering and visual motifs; the left/right and row transitions remain consistent. The historical scans include minor stains and uneven background, so the cropper should preserve content while applying only a conservative border/white-margin trim and should not “clean” the artwork into a new derivative style.

Tile review 5–6: cards 15–18 are consistently framed and show distinct motifs (bear, stars, stork, dog) with readable identifiers. The board’s internal card number is stable evidence for mapping the cropped file to the canonical 36-card catalog.

Tile review 7–8: cards 19–28 remain readable across the middle rows; the tower, garden, mountain, paths, mice, letter and man motifs are distinct and their board numbers are visible. No evidence of a second deck or rotated card orientation appears in these tiles.

Tile review 9–10: cards 23–32 show the remaining middle/lower motifs and preserve readable number markers, including Mice, Heart, Woman, Lily, Sun and Moon. The image has authentic scan stains, but no obstacle to using it as a clearly labeled historical reference deck.

Tile review 11–12: cards 33–36 are complete and readable at the lower edge (Key, Fish, Anchor, Cross). Their borders and number labels are intact, so the full 1–36 mapping is visually verified across all 12 ordered tiles. The source is suitable for asset preparation with conservative crops.

## Source 9 — Official MediaPipe model/API contract

The official Google AI Edge guide documents a Hand Landmarker bundle containing both a palm detection model and a hand-landmark model. Python/Android/Web guides use a model asset, and the task can run in IMAGE, VIDEO or LIVE_STREAM modes. Outputs include handedness and 21 hand landmarks in image/world coordinates; detection, presence and tracking confidence thresholds are configurable. This is sufficient for Mira’s geometry/evidence adapter, but it is not a palm-line model. The implementation must therefore label landmarks as capture/pose evidence and keep line segmentation as a separate optional stage.

Reference: https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker

## Source 10 — Existing OracleAI RWS asset verification

Visual inspection of `miniapp/img/tarot/m00.jpg` shows The Fool with the expected Rider–Waite–Smith composition and title strip; `miniapp/img/tarot/cups01.jpg` shows the fully illustrated Ace of Cups. The repository contains exactly 78 local JPG files in this namespace (22 major + 56 minor), so the current default deck is not a placeholder. The new deck manifest should identify this namespace as `rws-78-geldard-v1` and keep all alternative deck assets in separate roots.

## Source 11 — MediaPipe runtime smoke test

The pinned `mediapipe==0.10.35` runtime and official `hand_landmarker.task` bundle (SHA-256 `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`) were exercised locally. The official MediaPipe sample image `test_image.jpg` produced `status=detected`, one hand, 21 landmarks, handedness `right`, and a normalized bounding box. The repository fixture `tests/fixtures/palm/palm_hand.jpg` is a macro photograph of palm texture rather than a hand-pose image; it correctly produced `status=no_hand`. This is an expected capture-quality boundary, not evidence that line segmentation exists. The application must keep `hand_geometry` and future `line_segmentation` as separate evidence channels.
