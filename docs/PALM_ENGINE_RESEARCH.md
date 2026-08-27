# Palm-analysis engine research

**Дата исследования:** 26 августа 2026

## Вывод

OracleAI не должен обещать, что существующая модель полностью «понимает хиромантию». Текущий `app/core/palm_vision.py` измеряет только качество кадра; `app/core/palm_landmarks.py` опционально даёт hand pose/handedness/21 landmarks, но не распознаёт palm lines. Для безопасного улучшения выбран архитектурный паттерн **CV evidence helper → strict multimodal LLM interpretation**: компьютерное зрение указывает геометрию/видимость, а LLM интерпретирует только подтверждённые evidence и просит пересъёмку при недостатке данных.

## Кандидаты

| Источник | Что реально делает | Сигнал зрелости | Решение OracleAI |
|---|---|---|---|
| [MediaPipe Hands](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/hands.md) | Palm detector + 21 3D hand landmarks, normalized image/world coordinates и handedness; это pose, не palm-line segmentation. | Официальный активно используемый open-source stack; документация описывает single-shot palm detector и landmark model. | Использовать как optional pose/crop/hand-side helper; не выдавать landmarks за линии. |
| [yeonsumia/palmistry](https://github.com/yeonsumia/palmistry) | Warping, principal-line detection, classification и length measurement; MediaPipe + deep model + K-means. | Apache-2.0, но 52 stars, 46 commits, основная часть — старые notebooks; production API/model packaging отсутствуют. | Не интегрировать напрямую; использовать как research reference. |
| [lakshay102/Palm-Astro-Application](https://github.com/lakshay102/Palm-Astro-Application) | U-Net/ResNet18 segmentation demo для background/heart/head/life lines и геометрических features. | 3 stars, 2 commits, ориентирован на training/demo; нет доказательства production robustness. | Не интегрировать напрямую; не считать verified engine. |
| [samuelwbarber/palm-line-reader](https://github.com/samuelwbarber/palm-line-reader) | MIT-licensed 5.55M-param ONNX U-Net; fixed 512×512 RGB input, four classes background/heart/head/life; browser/WASM/WebGPU inference. README states validation foreground Dice 0.8098 and explicitly says its fortune reading is nonsense. | Reproducible model contract, training pack, browser demo, MIT license; current repository has only 2 commits/0 stars, so independent validation is still required. | Лучший candidate for optional helper, but only as segmentation evidence. Requires model provenance, benchmark on OracleAI capture distribution, confidence/quality gates and legal notice before public activation. |
| [Efficient Palm-Line Segmentation with U-Net Context Fusion Module](https://arxiv.org/abs/2102.12127) | Research U-Net/context-fusion palm-line segmentation; reports F1 about 99.42% and mIoU 0.584 on its handcrafted dataset. | Peer-reviewed conference reference, CC BY 4.0 arXiv license; dataset/domain generalization and production code are not established by the abstract. | Research baseline only; not a drop-in production engine. |
| [MediaPipe Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker) | Current task-oriented hand landmark API suitable for image/video/live-stream modes. | Official Google AI Edge documentation. | Compatible with existing lazy `palm_landmarks.py` adapter once the model asset and optional dependency are supplied. |

## Candidate ONNX contract

The inspected `palm-line-reader` model is `student_fp16.onnx` (11,284,720 bytes; SHA-256 `e2c9f826676b3aaf0a715f3087fcd4fc0b4dccd8c53de05fd26696a8399f8dd6`). Input is float32 NCHW `[1,3,512,512]`, RGB, plain resize without letterbox, ImageNet mean/std normalization. Output is raw float32 logits `[1,4,512,512]`; argmax classes are `0=background`, `1=heart_line`, `2=head_line`, `3=life_line`. The model is fixed-shape opset 17. The source README reports the fp16 student as the recommended size/quality tradeoff and says it is distilled from a teacher using pseudo-labels; it also warns that accuracy drops on off-distribution framing.

## Integration safety decision

The model must never directly produce personality, health, future, relationship, age, death, pregnancy, income or deterministic fate claims. The adapter should return only segmentation summary: class coverage, connected-component count, bounding boxes/path summaries and confidence/quality metadata. Mira’s LLM receives this block as untrusted CV evidence, must cross-check it against the image and deterministic capture/landmark metadata, and must return `needs_photo` if the crop or line evidence is weak. Relationship/children/travel lines are outside this three-line model and still require the folded-edge capture flow.

## References

[1]: https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/hands.md "MediaPipe Hands documentation"
[2]: https://github.com/yeonsumia/palmistry "Fortune On Your Hand: View-Invariant Machine Palmistry"
[3]: https://github.com/lakshay102/Palm-Astro-Application "Palm-Astro Application"
[4]: https://github.com/samuelwbarber/palm-line-reader "Palm Line Reader"
[5]: https://arxiv.org/abs/2102.12127 "Efficient Palm-Line Segmentation with U-Net Context Fusion Module"
[6]: https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker "MediaPipe Hand Landmarker"
