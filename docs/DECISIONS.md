# OracleAI — Architecture Decision Records

Документ фиксирует значимые архитектурные решения. Каждая запись содержит дату, контекст, варианты, решение и последствия.

## ADR-001 — Единый calculation source of truth

**Дата:** 2026-08-25  
**Статус:** accepted, refinement in progress

### Контекст

OracleAI уже использует `kerykeion==5.12.9`, который работает поверх Swiss Ephemeris. `app/core/astro.py` явно задаёт Tropical zodiac, Placidus (`P`), Apparent Geocentric и True Node; API возвращает `natal_schema_version: 2`, exact и rounded значения, precision mode и active points. Предыдущий cross-engine benchmark в репозитории показывает совпадение OracleAI/Kerykeion/direct Swiss Ephemeris для контрольной карты.

### Рассмотренные варианты

| Вариант | Точность | Визуальный контроль | Риск/стоимость |
|---|---|---|---|
| Собственная математика + Swiss Ephemeris низкого уровня | Высокая, но ответственность за conventions и edge cases полностью на проекте | Полный | Большая поверхность тестирования и лицензирования |
| Готовый полный движок вместе с его визуализацией | Высокая при корректных conventions | Ограниченный; сложнее добиться уникального wheel | Vendor/style coupling, лицензия и кастомизация |
| Гибрид: Kerykeion/Swiss Ephemeris adapter + собственный canonical DTO + зрелый server-side chart renderer | Высокая и уже подтверждённая benchmark | Ограниченный визуальным engine | Нужны adapter, fixtures и явная лицензия |

### Решение

Оставить Kerykeion/Swiss Ephemeris единственным production source of truth. Не объединять два независимых full chart engines. Выделить явные `CalculationConfig` и versioned `ChartModel`, хранить exact values отдельно от UI-rounded values, а natal visual строить через зрелый server-side Kerykeion ChartDrawer → transient SVG → resvg raster adapter, как зафиксировано в [CHART_ENGINE_DECISION](CHART_ENGINE_DECISION.md). Direct `pyswisseph`, flatlib, Immanuel, Astrolog и sweph-wasm могут использоваться только как reference/regression engines для отдельных conventions.

### Обоснование

Переход на другой calculation engine не даёт измеримого выигрыша по natal precision, но добавляет расхождения conventions, адаптационный код и новые риски. Для визуального слоя Mode P сознательно принимает engine/style coupling, чтобы убрать самописную natal-wheel geometry и collision surface.

### Последствия

Нужно завершить выделение calculation contract, добавить fixtures для timezone/DST/полярных широт/границ знаков/unknown time/invalid input, уточнить availability и метод активных точек Chiron/Lilith, а также пройти юридическую проверку AGPL Swiss Ephemeris/Kerykeion для коммерческого SaaS. Dual licensing Swiss Ephemeris означает, что технический переход между AGPL bindings сам по себе не снимает лицензионный риск.

## ADR-002 — Evidence-first interpretation

**Дата:** 2026-08-25  
**Статус:** accepted, extension planned

### Контекст

`app/core/interpretation.py` уже формирует закрытый evidence block и проверяет текст на неподтверждённые планеты, дома, аспекты и детерминистичные обещания. `app/core/agent.py` применяет semantic retry и coverage gate для полного натального разбора.

### Решение

Сохранить разделение deterministic context builder и LLM interpreter. Следующая итерация добавляет strict JSON Schema, лимиты длины, валидацию, retry/fallback и context-bound follow-up. LLM не вычисляет градусы, дома, аспекты, узлы, Chiron или Lilith.

### Последствия

Текстовые legacy-контракты сохраняются через backward-compatible adapter до завершения миграции UI/PDF. Неизвестное время рождения остаётся date-only режимом; транзиты или планетарные периоды не могут быть сгенерированы из воздуха.

## ADR-003 — PDF rendering baseline

**Дата:** 2026-08-25  
**Статус:** superseded by Mode P image integration; target deployment smoke test remains open

### Контекст

Текущий `app/pdfgen/render.py` использует WeasyPrint HTML→PDF и при отсутствии системных зависимостей сохраняет `.html`. `builder.py` уже содержит RU/EN tables, canonical chart facts, wheel/matrix blocks и несколько тематических секций, но структура и визуальный контроль требуют аудита.

### Рассмотренные варианты

| Вариант | Плюсы | Минусы |
|---|---|---|
| Оставить WeasyPrint и усилить print-template | Минимальная миграция, Python-native | Ограничения CSS/layout и системные Cairo/Pango dependencies |
| Puppeteer/headless Chromium | Предсказуемее для сложного SVG/CSS, развитый print emulation | Runtime/browser dependency, deployment size и sandbox concerns |
| react-pdf/pdfmake | Выделенный PDF layout и меньше browser runtime | Отдельная вёрстка, сложнее переиспользовать canonical SVG/UI styles |

### Временное решение

WeasyPrint remains the HTML→PDF path. The natal visual now arrives as a high-resolution canonical PNG from the Mode P adapter; the PDF never receives raw natal SVG or a browser screenshot. Target deployment smoke and page raster inspection remain open; see [PDF_AUDIT](PDF_AUDIT.md).

## ADR-004 — Agent routing baseline

**Дата:** 2026-08-25  
**Статус:** accepted baseline, QA pending

### Наблюдение

В текущем checkout не найден единый центральный intent-classifier. Сценарии Telegram/Mini App выбирают код агента через UI/FSM/callback; `app/core/agents/runtime.py` исполняет уже выбранного агента и сужает его skills. Это предсказуемо для явного выбора, но не проверяет свободные смешанные или ошибочные запросы.

### Решение

Сначала провести 20–30+ case matrix с expected/actual agent и tool trace. Только после измерения решать между нормализацией + handoff rules, structured LLM classifier с confidence/fallback или сохранением текущего explicit-selection UX. Нельзя добавлять дорогую классификацию без доказанного routing failure и regression set.

## ADR-005 — Audit baseline environment

**Дата:** 2026-08-25  
**Статус:** recorded

* Checkout: ветка `master`, HEAD `888a63f`.
* Test command: `pytest -q` — завершён успешно после установки pinned development dependencies.
* Operational command: `python3 -m scripts.selfcheck` — завершён успешно; live LLM probe пропущен без `SELF_CHECK_LIVE=1`, Telegram/WEBAPP env отсутствуют в sandbox.
* Initial dependency installation требовала `build-essential`, `libsqlite3-dev`, `pkg-config` и `python3.12-dev` для сборки pinned `pyswisseph`.

## Competitor Benchmark

Раздел будет заполнен после пассивного исследования публичного `https://steercorp.io/`. Непроверенные paywall/private/onboarding claims должны оставаться явно помеченными как unknown; сведения нельзя реконструировать из предположений.

## References

[1]: https://github.com/g-battaglia/kerykeion "Kerykeion GitHub repository"  
[2]: https://pypi.org/project/kerykeion/ "Kerykeion on PyPI"  
[3]: https://www.astro.com/swisseph/sweph_e.htm "Swiss Ephemeris licensing and documentation"  
[4]: ../app/core/astro.py "OracleAI natal calculation implementation"  
[5]: ../app/core/interpretation.py "OracleAI evidence and grounding contract"  
[6]: ../app/pdfgen/render.py "OracleAI HTML-to-PDF renderer"


## Browser evidence notes — 2026-08-25

The public GitHub page confirms the repository is public, on `master`, with 92 commits and HEAD `888a63f`; the visible tree includes `app/`, `miniapp/`, `scripts/`, `tests/`, `docs/`, and the latest commit message indicates a revert of a natal chart redesign/PDF export branch. This supports treating the current checkout, not a historical feature branch, as the source of truth.

The public SteerCorp homepage visibly positions Steer as a Vedic astrology product with a ChatGPT integration, Android availability and an iOS waitlist. It publicly claims unlimited free ChatGPT questions, real-time transits, daily Panchang, Dasha predictions, Swiss Ephemeris precision, Vimsottari Dasha, 27 Nakshatras, Ashtakavarga, Yogas, 20+ divisional charts, relationship readings from both charts, and a future API/agentic platform. The page shows screenshots of a warm cream/gold mobile/chat product, Kundli-style charts, daily guidance and relationship chat; it does not itself establish a full localized PDF workflow or multilingual support. These are public claims, not independent black-box verification.


### SteerCorp support/privacy evidence

The public support page documents Google sign-in, required birth date/time/place, approximate-time use with reduced precision, multiple profiles for family/friends/partners, AI chat grounded in chart/Dashas/transits, and a five-step getting-started path: create profile, explore chart, review Dasha timeline, chat, and self-discovery questions. Account deletion is requested by email and is stated to be processed within 30 days. The page does not document a user-facing PDF/export flow or multilingual UI.

The public privacy policy states collection of account, birth/location, current location, and multiple-profile data, and claims generated Kundali, Dasha, Panchang, transit data, Swiss Ephemeris calculations and temporary caching. These are policy/marketing statements and were not independently verified inside the authenticated app.


## Competitor Benchmark — SteerCorp vs OracleAI

| Критерий | SteerCorp: подтверждено публично | OracleAI: подтверждено в текущем checkout | Приоритет |
|---|---|---|---|
| Визуал колеса | Тёплая cream/gold mobile-first подача; публично показаны Vedic Kundli screenshots, chart/transit/Panchang screens; анимация полного wheel публично не доказана | Собственный SVG wheel с планетами, узлами, домами, аспектами и staggered animation; есть fixed geometry, ограниченный набор линий и нет collision avoidance | P0: OracleAI должен повторить ясную legend/readability и превзойти уникальностью, collision avoidance и responsive SVG |
| Глубина интерпретации | Публично заявлены Vedic chart, Dashas, transits, Panchang и AI chat; фактическая глубина live-ответов не тестировалась | Есть evidence-first context, placement facts, grounding/coverage gate и четыре разных специалиста; публичный natal result ещё текстовый, не strict JSON | P0: сохранить evidence advantage и добавить глубокий структурированный синтез без выдуманных фактов |
| User journey | Google sign-in → birth details → chart → Dasha timeline → AI chat → 100 self-discovery questions; multiple profiles | Telegram onboarding/Mini App; карта и специальные инструменты доступны через bot/UI; свободный чат по умолчанию открывает Лилит | P1: сравнить шаги и сократить путь до первой персональной карты |
| PDF/export | На публичных страницах и support flow полный PDF/export не подтверждён | Есть HTML report builder и WeasyPrint path, RU/EN labels, wheel/matrix/reference blocks; premium page QA и final CTA ещё незавершены | P0: довести PDF до содержательного RU/EN отчёта без пустых страниц |
| Языки | Публичная поверхность англоязычная; multilingual behavior не подтверждён | RU/EN интерфейс, prompts/fallbacks и PDF localization | P1: сохранить двуязычность и сделать её видимой в reports/agent follow-up |
| Дополнительные функции | Публично заявлены Dashas, Panchang/Muhurta/Rahu Kaal, Nakshatras, Ashtakavarga, Yogas, 20+ divisional charts, compatibility, API roadmap, Android/iOS waitlist | Natals, transits/timing, compatibility, Tarot, Matrix, palm vision, diary/memory/practices, Vedic subset docs; breadth and cross-engine validation vary | P1: не копировать маркетинговые claims без deterministic evidence; развивать только измеримые skills |
| Premium brand | Светлая editorial cream/gold эстетика, крупный serif headline, phone screenshots, privacy-first copy и чёткие CTA | Тёмная космическая эстетика, Cinzel/PJS fonts, agent portraits, glass cards, motion and SVG sigils | P1: повторить сильную иерархию/CTA конкурента, превзойти specialist identity, proof envelope и visual depth |

### Что минимум повторить

OracleAI должен обеспечить такой же короткий путь от профиля к первой персональной карте, понятную визуальную иерархию chart/reading, сохранение нескольких профилей/партнёров, понятный CTA и ясное объяснение точности неполного времени рождения. Для premium-уровня обязательны содержательный отчёт, читаемая легенда, mobile-first layout и предсказуемые пустые/загрузочные состояния.

### Где OracleAI должен превзойти

OracleAI должен опираться на уже существующие сильные стороны: четыре явно различимых агента, evidence-first tool provenance, честные precision modes, RU/EN локализацию, расширенные Western points, Tarot/Matrix/palm domains и server-side safety boundaries. Превосходство должно быть измеримым: chart facts не выдумываются, follow-up цитирует конкретные placements, wheel строится индивидуально и PDF генерируется из canonical data, а не из screenshot.

### Ограничения benchmark

Steer claims about authenticated calculations, retention, latency, actual report quality, live pricing and API execution were not black-box tested. OracleAI live LLM provider quality was not accepted as a deterministic baseline in this sandbox. Therefore the table distinguishes public claims, inspected code and unverified behavior; it does not claim technical parity with all advertised Steer features.

### References for benchmark

[7]: https://steercorp.io/ "SteerCorp public homepage"  
[8]: https://steercorp.io/support.html "SteerCorp public support and FAQ"  
[9]: https://steercorp.io/privacy.html "SteerCorp public privacy policy"  
[10]: https://play.google.com/store/apps/details?id=coach.steer.app&hl=en_US "Steer app Google Play listing"


## Natal engine research — primary-source snapshot 2026-08-25

| Project | Snapshot | Accuracy/data | License | Integration assessment |
|---|---|---|---|---|
| [CircularNatalHoroscopeJS][11] | GitHub: 377 stars, 102 forks, 172 commits; Unlicense | JS/TS calculations for tropical/sidereal, ASC/MC, major bodies, nodes, Lilith, retrograde, multiple house systems, configurable major/minor aspects and custom orbs; README does not claim Swiss Ephemeris and credits Moshier-derived ephemeris work | Unlicense | Broad feature coverage and easy JS integration, but it would create a second calculation convention and lacks the Swiss Ephemeris provenance required for the source-of-truth path |
| [AstroDraw/AstroChart][12] | GitHub: 415 stars, 103 forks, 180 commits; npm 3.0.2, published 3 years ago | TypeScript SVG renderer only; explicitly does not calculate planetary positions; dependency-free and tested | MIT | Strong renderer reference and commercially friendly license, but it cannot replace Kerykeion/Swiss calculations; adopting it would add a second visual abstraction versus extending the existing custom SVG |
| [Kerykeion][13] | GitHub: 697 stars, 190 forks, 1,540 commits; AGPL-3.0; current repository package is pinned to 5.12.9 | Python engine with Swiss Ephemeris/NASA JPL provenance, planets, houses, aspects, nodes, SVG, synastry, transits, returns, structured JSON and AI context | AGPL-3.0; hosted API is advertised for closed-source commercial use, while self-hosting/importing requires legal review | Best fit and already integrated. Keep as the single production source; extract a canonical adapter and use its SVG only as reference, not as the product visual |
| [pyswisseph][14] | GitHub: 394 stars, 103 forks, 233 commits; AGPL-3.0 | Low-level Swiss Ephemeris Python extension, DE431 range, high-precision planetary/astronomical functions; requires ephemeris files for tests | AGPL-3.0 binding; original Swiss Ephemeris is dual AGPL/professional license | Excellent regression oracle and future low-level escape hatch; replacing Kerykeion would increase convention/normalization code without a measured precision gain |
| [AstroChart2][15] | npm/jsDelivr 0.7.3, GPLv3; described as alpha | Zero-dependency configurable SVG renderer, no calculation; includes nodes, Lilith, Chiron, collision/scaling examples; animation marked TODO | GPLv3 | Useful visual reference for collision/scaling ideas, but alpha status and GPLv3 make it inferior to custom SVG for a commercial premium surface |

### Engine decision

The evidence reinforces ADR-001: keep Kerykeion/Swiss Ephemeris as the only production calculation path, implement the project's own canonical DTO and SVG, and use CircularNatalHoroscopeJS/pyswisseph/AstroChart2 only as reference or regression fixtures. AstroDraw is a viable MIT renderer reference, but the current wheel already owns the product visual language and needs collision/accessibility/legend improvements rather than a renderer swap. Licensing is a release blocker for a closed-source commercial service and requires legal review before production distribution.

[11]: https://github.com/0xStarcat/CircularNatalHoroscopeJS "Circular Natal Horoscope JS GitHub"  
[12]: https://github.com/AstroDraw/AstroChart "AstroDraw AstroChart GitHub"  
[13]: https://github.com/g-battaglia/kerykeion "Kerykeion GitHub"  
[14]: https://github.com/astrorigin/pyswisseph "pyswisseph GitHub"  
[15]: https://www.jsdelivr.com/package/npm/astrochart2 "AstroChart2 jsDelivr package page"  


### Cross-engine benchmark artifact

`docs/audit/natal_benchmark_2026-08-25.json` records the deterministic control card (`1990-06-21 14:30`, Kazan, `Europe/Moscow`). OracleAI/Kerykeion and direct `pyswisseph` match at **0.0 arcseconds** for ASC, MC, all 12 Placidus cusps and the ten tested planetary longitudes. The optional `flatlib` comparison remains unavailable because it is not installed and is not part of the pinned production dependency set; it is not treated as evidence of a mismatch.


## ADR-006 — Product wheel renderer after real smoke tests

**Дата:** 2026-08-25  
**Статус:** superseded by Mode P on 2026-08-25

### Контекст

После обновления canonical chart contract были реально проверены два внешних визуальных слоя на одинаковых тестовых профилях: `@astrodraw/astrochart` 3.0.2 в Node/jsdom и Kerykeion 5.12.9 через текущий `ChartDataFactory` + `ChartDrawer`. Решение принималось по совместимости с canonical payload, читаемости плотных карт, контролю темизации/лейблов, текущими Mini App hooks и лицензии.

### Измеренные варианты

| Вариант | Реальный smoke result | Лицензия | Оценка интеграции |
|---|---|---|---|
| Текущий собственный SVG (retired) | Historical sparse/clustered/spread fixtures; no longer a product path | Project code | Explicitly cancelled by the latest migration brief |
| `@astrodraw/astrochart` 3.0.2 | Node/jsdom smoke успешно создал 3 SVG: 53,470 / 61,696 / 58,844 bytes; viewBox `0 0 760 760`; 27–42 text nodes; cusp labels присутствуют | MIT | Качественный reference renderer, но потребует adapter из canonical contract и заменит текущие interaction/accessibility hooks |
| Kerykeion 5.12.9 `ChartDrawer` + resvg_py 0.5.0 | Real SVG→PNG spike passed after CSS-variable removal; visual artifacts show glyphs, houses and aspect layer; raw SVG remains transient | AGPL-3.0 plus Swiss Ephemeris license gate | Selected Mode P adapter; commercial release remains blocked pending legal sign-off |

### Решение

Собственный natal SVG-слой удалён из production. Активный путь — серверный Kerykeion ChartDrawer → transient SVG → resvg PNG/WebP; Mini App, share и PDF получают только raster bytes. AstroChart остаётся research reference, а accessibility для клиента обеспечивается HTML placement list и structured precision/recovery states.

### Последствия

Natal visual changes выполняются только через публичный Kerykeion ChartDrawer/resvg adapter; ручная natal geometry, Canvas export и raw-SVG product path запрещены. Visual evidence теперь хранится как PNG/WebP artifacts. Лицензионный review Kerykeion/Swiss Ephemeris остаётся отдельным release gate для коммерческого развёртывания.

## ADR-007 — Confident voice and readable dense PDF

**Дата:** 2026-08-25  
**Статус:** accepted

### Решение

Пользовательские тексты и активные LLM-инструкции используют уверенный evidence-first голос: конкретный placement, карта, аспект или наблюдаемая особенность → ясная интерпретация → применимый следующий шаг. Общие рационализирующие оговорки о «символичности», развлечении или недостоверности не добавляются в обычные ответы. При этом `app/core/safety.py`, медицинские/юридические/финансовые границы, crisis/age/privacy и запреты на выдуманные расчёты остаются обязательными.

PDF сохраняет body `12.4pt` с line-height `1.56`, H2 `24pt`, H3 `17pt`, компактную двухколоночную композицию тематических глав, визуальные anchors (wheel/matrix) и полный calculation reference. Шесть страниц приняты как читаемый плотный результат: все 3 детерминированных профиля в RU/EN дали 6 страниц, без overflow и запрещённых user-facing markers; дальнейшее сокращение не должно выполняться за счёт уменьшения типографики.

### Evidence

* [Renderer research and smoke notes](audit/renderers/RESEARCH.md)
* [AstroChart smoke metrics](audit/renderers/astrochart/astrochart_smoke_results.json)
* [Kerykeion smoke metrics](audit/renderers/kerykeion/smoke_results.json)
* [Three-profile PDF results](audit/pdf_samples_v2/profiles/results.json)
* [Visual QA notes](audit/pdf_samples_v2/visual/visual_qa_notes.md)
