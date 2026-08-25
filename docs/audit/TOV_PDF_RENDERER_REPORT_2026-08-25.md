# OracleAI — ToV, PDF и renderer audit

**Дата:** 2026-08-25  
**Объём:** Telegram bot, Mini App, active LLM prompts, file-backed agent skills, offline fallbacks, PDF pipeline и natal wheel.

## Итог

Второй цикл модернизации завершён в рабочем checkout без commit/push. Пользовательские поверхности и активные инструкции моделей теперь используют уверенный immersive evidence-first голос: конкретный placement, выпавшая карта, наблюдаемая особенность кадра или рассчитанная связь → ясная трактовка → применимый следующий шаг. Общие рационализирующие оговорки удалены из обычного продуктового потока. Обязательные safety-границы не ослаблялись.

Production visual decision: **оставить собственный SVG wheel** в `miniapp/js/04-nativity.js`. AstroChart и Kerykeion были не просто изучены, а реально установлены/запущены на smoke fixtures. Их результаты зафиксированы как reference evidence; добавление второго production renderer не даёт измеримого преимущества перед уже canonical-data-driven слоем и добавляет adapter/runtime/licensing burden.

## 1. Semantic ToV audit

Первичный широкий grep по всему checkout дал **335 строк** совпадений. В это число входили docs, tests, audit artifacts, Terms/Privacy, legal/age copy, safety text и технические комментарии; оно не является числом пользовательских оговорок, которые нужно безусловно удалить.

После семантической фильтрации active surface (`app/` + `miniapp/`) до последнего cleanup было **10 строк**. Из них **5** были продуктовой/промптовой rationalizing language и были переписаны: четыре literal voice-contract блока в SYSTEM.md для Urania, Lenormand, Lilith и Mira и один несвязанный observability-комментарий. В широком втором проходе дополнительно обновлены повторяющиеся file-backed skill/playbook формулировки; логи фиксируют 92 изменённых файла в первом проходе и 38 файлов во втором проходе, с возможным пересечением. После финальной проверки осталось **5 deliberate matches**: две медицинские/профессиональные boundary-записи в `Mira/Urania DOMAIN_PLAYBOOK.md` и три обязательных записи в `app/core/safety.py` для crisis/high-stakes protection. Это safety/data-quality поведение, а не обычный ToV; оно сохранено намеренно.

| Область | До | После |
|---|---|---|
| Agent SYSTEM contracts | Literal examples of self-discrediting wording were present inside the voice contract. | Positive contract: speak as a confident specialist, connect each insight to concrete evidence, keep the interpretation precise and applicable. |
| Shared runtime | Общие оговорки могли попадать в базовые инструкции и fallback-тексты. | Базовая инструкция задаёт evidence-first synthesis без шаблонного самообесценивания; safety gate остаётся отдельным обязательным слоем. |
| Mini App | На chart/diary/palm/placements surfaces встречались дистанцирующие или рационализирующие подписи. | Прямые placement/observation/next-step формулировки; quality и data-availability guidance остаются там, где они нужны для точности. |
| PDF and natal prompt | В prompt/fallback/closing могли появляться слова, смещающие чтение в сторону развлечения или недостоверности. | Уверенная локализованная подача, grounded только на canonical facts; date-only режим сообщается как свойство доступных данных. |
| Safety | Crisis, medical/legal/financial, age/privacy и запрет на fabricated facts. | Не удалялись и продолжают применяться системно. |

Намеренно не изменялись Terms/Privacy, возрастная защита, кризисные ответы, high-stakes медицинские/юридические/финансовые границы, privacy/security controls и ограничения на недоступные расчёты. Эти элементы защищают пользователя и качество данных, а не снижают тон продукта.

## 2. PDF typography and density

Текущий PDF остаётся WeasyPrint HTML→PDF и получает canonical chart facts, wheel/matrix SVG, локализованные labels и calculation reference. Основная типографика теперь соответствует заданному диапазону: **body 12.4pt**, **line-height 1.56**, **H2 24pt**, **H3 17pt**. Whitespace сокращён композицией, а не уменьшением текста: тематические главы собраны в две колонки, reference tables уплотнены, redundant Matrix table удалена, wheel и matrix используются как meaningful visual anchors.

| QA profile | Time | Language | Pages | PDF size | Text chars | ToV markers |
|---|---:|---:|---:|---:|---:|---:|
| known_time | known | RU | 6 | 138,860 B | 18,892 | 0 |
| known_time | known | EN | 6 | 136,535 B | 19,069 | 0 |
| date_only | absent | RU | 6 | 132,187 B | 15,799 | 0 |
| date_only | absent | EN | 6 | 129,971 B | 16,294 | 0 |
| evening_time | known | RU | 6 | 138,508 B | 18,553 | 0 |
| evening_time | known | EN | 6 | 136,286 B | 17,942 | 0 |

QA harness: `scripts/qa_pdf_profiles.py`. All **6/6** documents were valid PDFs; all stayed at six pages, had no audited ToV marker, and passed text extraction. The date-only profile showed unavailable angular/house data directly, with no fabricated ASC, MC or houses.

The six-page result is accepted rather than compressed to five pages by reducing readability. It contains a meaningful cover, overview with wheel and matrix, full calculation reference, five paired thematic content blocks and closing. Generated pages `known_time_en-2.png` and `date_only_ru-3.png` were visually inspected at 120 dpi: body copy and tables remain readable, columns are balanced, footers are stable, and no clipping, accidental blank page or overflow was observed. Further reduction should use structural composition only.

## 3. Renderer research and real execution

Two external options were executed against real rendering paths.

| Renderer | Real test | License | Result and decision |
|---|---|---|---|
| Project custom SVG | Existing Mini App wheel with sparse/clustered/spread chart fixtures and canonical payload | Project code | **Selected for production.** Direct contract compatibility, existing collision lanes, semantic aspect styles, accessibility, responsive viewBox and reduced motion. |
| `@astrodraw/astrochart` 3.0.2 | Node 22 + jsdom; sparse, clustered and spread SVGs | MIT | 53,470 / 61,696 / 58,844 bytes; viewBox `0 0 760 760`; 27–42 text nodes; cusp labels in all. Good reference, not integrated because an adapter and second visual abstraction are unnecessary. |
| Kerykeion 5.12.9 `ChartDrawer` | Current `AstrologicalSubjectFactory` → `ChartDataFactory` → `ChartDrawer`; classic and modern SVG | AGPL-3.0 | 221,739 / 234,591 bytes; 115 / 163 text nodes; house labels and aspect layers in both. Useful reference, but not integrated as another frontend/runtime visual layer; commercial distribution requires license review. |

The current Kerykeion modern output demonstrates useful concepts—concentric rings and largest-gap planet decluttering. Those ideas may inform future changes to the project SVG, but no Kerykeion renderer code is imported into the Mini App. AstroChart’s MIT license is commercially friendlier, but its output still needs a project adapter and gives less control over the existing product interaction/accessibility contract. The measured evidence therefore supports evolution of the custom wheel rather than a renderer swap.

Primary sources: [AstroDraw/AstroChart](https://github.com/AstroDraw/AstroChart), [Kerykeion GitHub](https://github.com/g-battaglia/kerykeion), [Kerykeion Python library](https://kerykeion.net/python-library), [Swiss Ephemeris licensing](https://www.astro.com/swisseph/sweph_e.htm).

## 4. Verification

The final release gate was rerun after the last Urania and specialist prompt edits.

| Gate | Result |
|---|---:|
| Full `pytest -q` | **465 passed** |
| Mini App JavaScript `node --check` | passed |
| Python `compileall` | passed |
| `git diff --check` | passed |
| `scripts/selfcheck.py` | passed; configured proxy’s empty live responses correctly used offline fallback |
| `scripts/check_design_contract.py` | passed |
| Agent routing benchmark | **24/24**, 100% |
| Skill routing benchmark | **20/20**, 100% |
| Vedic routing benchmark | **10/10**, 100% |
| Mira/Lenormand benchmark | **20/20**, 100% |
| AstroChart smoke | 3/3 SVG outputs |
| Kerykeion smoke | 2/2 SVG outputs |
| Three-profile PDF QA | **6/6 PDFs**, 6 pages each |

## 5. Artifacts and decisions

* [ADR log](../DECISIONS.md), including ADR-006 renderer selection and ADR-007 confident voice/readable PDF.
* [Task backlog](../TASKS.md) and [agent map](../AGENTS.md).
* [Renderer research](renderers/RESEARCH.md), [AstroChart metrics](renderers/astrochart/astrochart_smoke_results.json) and [Kerykeion metrics](renderers/kerykeion/smoke_results.json).
* [Three-profile PDF metrics](pdf_samples_v2/profiles/results.json), extracted text and generated PDF files under `pdf_samples_v2/profiles/`.
* [Visual QA notes](pdf_samples_v2/visual/visual_qa_notes.md) and generated page images under `pdf_samples_v2/visual/`.
* Final release-gate logs under `release_gate/`.

No commit or push was made. The local renderer installation directory (`node_modules` and downloaded package archive) was removed from the audit tree; only reproducible smoke scripts, SVG examples and metrics remain.
