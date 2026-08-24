# OracleAI — архитектурный аудит модуля натальной карты

**Дата:** 24 августа 2026  
**Ветка:** `feat/agent-first-harness`  
**Статус:** этап диагностики завершён; правки ещё не включены в этот документ.

## Executive summary

Текущий модуль не является картинкой-заглушкой: расчётный слой использует Kerykeion/Swiss Ephemeris, а клиентский wheel строится программно как inline SVG. Основной дефект находится не в отсутствии расчёта, а в смешении нескольких presentation contracts и недостаточно защищённом geometry/text layer.

Визуальное колесо и текстовые interpretations уже находятся в отдельных DOM-блоках. Однако само колесо перегружено длинными названиями планет, фиксированными radial placements и отсутствием полноценного collision avoidance. Поэтому пользователь может воспринимать результат как «текст наложен на карту», хотя фактическая причина — overcrowded SVG labels и слабое разделение chart presentation zones.

PDF pipeline реализован через отдельный server-side HTML→PDF generator на WeasyPrint. Он способен собрать PDF в текущем окружении, но chart router не предоставляет отдельного authenticated download endpoint: генерация сейчас доступна через CLI/report builder path. При отсутствии системных библиотек WeasyPrint код честно сохраняет `.html`, а не невалидный `.pdf`; это может выглядеть как «PDF не работает».

## 1. Движок и отрисовка wheel

| Вопрос | Фактическое состояние |
|---|---|
| Calculation engine | `app/core/astro.py` использует Kerykeion через Swiss Ephemeris; LLM не считает положения самостоятельно |
| Client renderer | `miniapp/js/04-nativity.js`, кастомный inline SVG `nativitySvg()` |
| Coordinate model | Позиции вычисляются программно из `abs_deg`/`abs_deg_exact` через polar coordinates; дома, planet markers, nodes и aspects — SVG primitives |
| Responsive model | SVG использует `viewBox`, `width:100%`, `max-width:280px`, `height:auto` |
| Houses | Client wheel рисует house arcs из `houses` и номера домов |
| Planets | Символы размещаются на одном radial ring `r - 22*scale`; рядом стоящие планеты не разводятся |
| Nodes | Rahu/Ketu/Lilith рисуются на другом кольце, но отдельного collision solver нет |
| Aspects | Первые 8 аспектов превращаются в SVG `<line>` между planet coordinates |
| Text inside wheel | При `size >= 200` под glyph добавляется полное имя планеты; это создаёт crowding внутри маленького круга |

PDF wheel реализован отдельно в `app/pdfgen/layout.py` через `wheel_svg()`. Там есть простой radial staggering: близкие точки пытаются сдвигаться по радиусу. Этот алгоритм не переиспользуется клиентским SVG renderer, поэтому web и PDF могут визуально расходиться.

## 2. Text/interpretation layer

Текст не позиционируется поверх SVG через абсолютный layout. `miniapp/js/10-chart.js` выводит wheel в `.nw`, затем отдельно создаёт signature, precision notice, takeaway и `.chart-insights`. Interpretation sections реализованы через native `<details>` accordions: `identity`, `mind_career`, `relationships`, `nodes`.

Это правильное направление, но текущая presentation model имеет несколько слабых мест:

1. Wheel остаётся перегруженным собственными labels, поэтому visual collision ошибочно выглядит как overlap с interpretation text.
2. `chartSectionsHtml()` показывает длинные `intro`, `meaning` и notes в одном вертикальном потоке без лимита на уровне UI; отдельные item cards защищают контейнер, но отсутствует явный «показать полностью» для длинных значений.
3. `chartHtml()` содержит inline styles для precision notice и footer/action row, из-за чего chart visual contract распределён между `10-chart.js`, base chart CSS и `15-ritual-redesign.css`.
4. Full details block для planets/aspects отделён, но не имеет отдельного structured summary model для client/PDF parity.

## 3. LLM layer

Основной путь находится в `app/core/agent.py:563` (`interpret_chart()`). Модель получает system prompt агента Urania, `skills.guide(db, 'natal')`, deterministic `chart_evidence` и `interpretation.generation_rules('chart')`.

Текущий контракт — **plain text, не JSON**. Prompt требует ровно 8 нумерованных секций: identity, Mercury, Mars, career/finance, Venus, partnership, nodes и synthesis. Указывается русский язык, обращение на «ты», placement fact перед interpretation, concrete self-observation question и запрет unsupported claims. Запрос ограничен `max_tokens=2600`.

После генерации работает quality gate: текст должен быть не короче 900 символов, пройти grounding validation и покрыть обязательные темы. При отказе выполняются retries с feedback; затем используется deterministic `_full_chart_fallback()`.

Следствие: LLM output достаточно защищён от hallucinated placements, но не является стабильным field-level contract. UI не получает отдельные `sun`, `moon`, `houses[]`, `aspects[]` narrative fields; он получает один большой prose response, который невозможно надёжно разложить по карточкам без дополнительного парсинга.

## 4. PDF generation

| Слой | Фактическая реализация |
|---|---|
| Orchestration | `scripts/gen_pdf.py` принимает CLI order/CSV и вызывает `app.pdfgen.builder.generate()` |
| Data | `builder.build_report_data()` получает chart через `astro.compute_chart_async()`, Matrix и sky |
| Text | `builder._section_text()` генерирует 10 длинных prose chapters; без LLM используются deterministic offline sections |
| HTML template | `app/pdfgen/layout.py` создаёт standalone HTML + embedded `PAGE_CSS` |
| Wheel | `layout.wheel_svg()` — отдельный server-side SVG generator |
| PDF renderer | `app/pdfgen/render.py` импортирует WeasyPrint и вызывает `HTML(...).write_pdf()` |
| Fallback | При недоступном WeasyPrint сохраняется соседний `.html`; расширение `.pdf` не подделывается |
| API download | В `app/api/routers/chart.py` нет отдельного PDF export endpoint; существующий chart API отдаёт JSON chart/sections |

На текущем sandbox sample build WeasyPrint доступен (`69.0`), RU и EN report HTML/PDF собираются, размеры sample PDF составили примерно 132–135 KB. Это доказывает, что pipeline не «брошен», но не доказывает качество page breaks на длинном live LLM content.

## 5. Root causes, которые определяют стратегию фикса

| Приоритет | Root cause | Последствие |
|---|---|---|
| P0 | Client wheel and PDF wheel have separate geometry implementations | visual drift and duplicated collision logic |
| P0 | Client planet labels use one ring and render full names inside the wheel | labels overlap at close degrees and make wheel look broken |
| P0 | No stable structured narrative schema from LLM | prose length and section boundaries are not deterministic |
| P1 | Wheel/text separation exists semantically but lacks a strong responsive composition contract | chart can feel visually merged on narrow screens |
| P1 | PDF is CLI-oriented and has no chart API export action | user-facing PDF button cannot reliably complete an export flow |
| P1 | Inline styles and chart styling are distributed across several files | later overrides can regress sizing/spacing |
| P2 | Existing PDF text sections are intentionally long (4–6 paragraphs each) | dense pages and variable pagination under long responses |

## 6. Recommended implementation order

Сначала нужно выделить shared chart data contract и единый geometry helper для client/PDF: normalized points, angles, sign sectors, house cusps, aspect metadata and collision lanes. Затем client wheel следует перевести на компактные glyph-only labels with radial collision avoidance; interpretation cards должны оставаться отдельным flow layer below/alongside the wheel.

После этого LLM contract следует перевести на validated structured JSON with bounded fields and deterministic fallback. Web renderer and PDF builder должны потреблять одну semantic structure, но иметь разные layout templates. PDF export нужно закрыть authenticated API endpoint, который вызывает server-side renderer and returns a real PDF response; CLI remains useful for batch generation.

## References внутри репозитория

- `app/core/astro.py` — deterministic ephemeris calculation, planets, houses, aspects, Rahu/Ketu.
- `miniapp/js/04-nativity.js` — current inline SVG wheel renderer.
- `miniapp/js/10-chart.js` — chart form, wheel shell, interpretation accordions and share action.
- `app/core/agent.py` — current prose LLM interpretation, quality gate and fallback.
- `app/pdfgen/layout.py` — standalone PDF CSS and SVG wheel.
- `app/pdfgen/render.py` — WeasyPrint renderer and HTML fallback.
- `app/api/routers/chart.py` — chart JSON endpoints; no PDF export endpoint.
- `tests/test_natal_sections.py` and `tests/test_pdfgen.py` — current regression coverage.

## Визуальная baseline-проверка PDF

На sample RU exact case (`Алексей`, 21.03.1990, 08:15, Москва) WeasyPrint сформировал 7-страничный A4 PDF размером 141 977 bytes. На страницах 1–3 визуально подтверждены: отдельная обложка, отдельные facts/wheel/Matrix зоны, читаемая таблица планет и отсутствие наложения wheel на narrative text. Колесо и Matrix в overview визуально компактны и не обрезаны. Это baseline для следующего этапа; длинные LLM-generated chapters и mobile screen rendering требуют отдельной проверки.


## 7. Post-audit implementation update — 25 августа 2026

Разделы 1–6 выше сохранены как архитектурная диагностика состояния **до** redesign. Ниже зафиксировано, что изменено после аудита и чем подтверждено.

### 7.1 Wheel/text composition

`miniapp/js/04-nativity.js` теперь рендерит premium inline SVG с `viewBox`, `preserveAspectRatio`, restrained sign sectors, house cusps, aspect lines и glyph-only planet/node markers. Полные названия не помещаются внутрь круга: они остаются в accessibility/data attributes и показываются в отдельной интерактивной plaque после выбора точки. `.chart-result .nw` получил отдельный responsive stage contract с `height:auto`, `min-height:0` и независимым flow-контейнером; interpretation cards находятся ниже wheel и не позиционируются поверх SVG.

Collision avoidance теперь является deterministic 2D placement solver: он перебирает radial lanes и angular fan-out, проверяет фактическую дистанцию окружностей marker-to-marker и выбирает defensive max-clearance fallback. На live close-degree fixture из 10 планет и 2 узлов в одном секторе получены `12` уникальных координат, минимальная дистанция центров `23.22` SVG units и положительный minimum clearance `3.19` units в `260×260` viewBox. Это существенно сильнее прежнего radial-only fallback, который давал overlap.

Web live geometry после v113 height fix: stage `392×392`, SVG `346×346`, ratio stage `1`, ratio SVG `1`, `scrollWidth=clientWidth=390`; документ не имеет горизонтального overflow (`document scrollWidth=1280`, viewport width `1280`).

### 7.2 Structured interpretation contract

`app/core/agent.py::interpret_chart()` теперь запрашивает только strict JSON с `summary` и объектами `sun`, `moon`, `ascendant`, `mercury`, `mars`, `career`, `relationships`, `nodes`, `synthesis`. Каждое поле ограничено по длине (`fact ≤220`, `interpretation ≤400`, `question ≤220`), нормализуется parser-ом и проходит grounding/coverage quality gate. На невалидный или неполный JSON сохраняется deterministic full-chart fallback. Web renderer строит bounded accordion cards; legacy plain-text fallback сохранён для совместимости.

`POST /api/chart/interpret` теперь возвращает `{text, structured}`. Исправлен first-request cache bug: structured payload читается после live `interpret_chart()` в том же запросе, а не только при следующем cache hit. Regression test проверяет именно этот сценарий.

### 7.3 Real PDF export

`GET /api/chart/pdf` — authenticated endpoint с `llm` rate limit, который вызывает server-side `pdf_builder` и возвращает только настоящий `application/pdf`; при недоступном WeasyPrint выдаётся контролируемая ошибка, а не файл HTML с расширением PDF. Cover теперь содержит имя, дату, время (если известно), место, centered natal wheel и ссылку на проект. На всех страницах footer имеет форму `OracleAI · N`.

Последняя визуальная проверка Alexey PDF подтвердила cover wheel, строку `21.03.1990 · 08:15 · Москва`, читаемые facts/reference pages, отсутствие видимого clipping/overlap и непрерывный брендированный footer на страницах 1–7. Multi-case generation через WeasyPrint дала реальные A4 PDF:

| Case | Precision / input | Pages | Bytes | Result |
|---|---|---:|---:|---|
| Алексей | 1990-03-21, 08:15, Москва | 7 | 164,880 | valid PDF, A4 |
| Мария | 1987-11-04, date-only | 6 | 152,840 | valid PDF, A4 |
| Jordan | 2001-07-19, 23:40, London | 7 | 162,051 | valid PDF, A4 |

### 7.4 Parity and limitations

Web и PDF используют один зафиксированный geometry contract (`viewBox`/aspect ratio, sign/house rings, glyph-only markers, annulus and fan-out principles), но клиентский JavaScript и server-side Python пока содержат **параллельные реализации**, а не буквально импортируют один исходный модуль. Это осознанная cross-runtime граница; audit не объявляет literal code sharing выполненным.

Ключевая оставшаяся эксплуатационная граница не относится к natal redesign: постоянный staging/production website по-прежнему невозможен без предоставленного пользователем hosting target, domain/DNS и production secrets. Текущий local/demo server остаётся DEV_MODE и не должен называться permanent staging.
