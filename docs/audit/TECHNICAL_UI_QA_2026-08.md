# OracleAI — технический UI QA и bugfix report

**Дата:** 24 августа 2026  
**Ветка:** `feat/agent-first-harness`  
**Область:** Mini App vanilla JS/CSS, Tarot spread/day-card renderers, responsive shell и основные tool surfaces.

## 1. Критическая Tarot-регрессия

### Первопричина

В исходной связке `miniapp/css/10-tarot-carousel.css` и `miniapp/css/14-widgets.css` карточный слот использовал несогласованные пропорции. Основной `.tcard` был `aspect-ratio: 2 / 3`, тогда как реальные RWS scans имеют примерно `330 × 568–571` пикселей. Одновременно `.tcard-face img` и `.dc-face img` использовали `object-fit: cover`. Из-за этого браузер масштабировал изображение под более широкий слот и обрезал его сверху/снизу или по краям.

В live geometry до исправления первый открытый слот имел размер `132 × 198`, а соседние слоты сжимались примерно до `109.8 × 164.7`. Grid tracks при этом оставались по `149px`. Такое расхождение объясняло жалобу «карта меньше зоны»: визуальная карта не заполняла slot, а grid item мог показывать область соседнего элемента.

### Исправление

В финальном override `miniapp/css/15-ritual-redesign.css`:

| Область | Исправление |
|---|---|
| Slot ratio | `.tcard`, `.tarot-card-big` и `.dc-card` переведены на `aspect-ratio: 330 / 568` |
| Slot width | `.tarot-grid .tcard` получил `width: 100%; max-width: none`, поэтому карта заполняет свой grid track |
| Image fit | Основные Tarot faces используют `object-fit: cover` уже внутри согласованного ratio |
| Grid isolation | `.tarot-grid` получил `overflow: clip` и `isolation: isolate` |
| Sibling stability | `.tpos` получил `width: 100%; min-width: 0; position: relative; isolation: isolate` |
| Face clipping | обе стороны карты имеют `overflow: hidden` и `backface-visibility: hidden` |
| Day card parity | small daily card получил тот же ratio, fit и clipping contract |

После исправления live geometry для 3-card spread стала одинаковой: каждый slot и каждая карта имеют `149.03 × 256.5px`, grid width — `467.09px`, `scrollWidth` совпадает с `clientWidth`, overflow отсутствует. Открытая карта показывает весь artwork; ghost/sibling card слева не появляется.

Исправление проверено в 3-card flow. Тот же CSS-контракт применяется к one-card, love/money two-column и другим spread classes, потому что они используют общий `.tarot-grid`, `.tpos` и `.tcard` renderer.

## 2. Flip animation audit

3D flip не переписывался через резкую смену `display` или размеров. Сохранена корректная архитектура: `perspective` на card button, `transform-style: preserve-3d` на inner, `rotateY(180deg)` для open state и hidden backface на обеих сторонах.

Финальный contract добавляет GPU-friendly `will-change: transform` и `translateZ(0)`, единый `560ms cubic-bezier(.22, 1, .36, 1)` easing, `translateZ(.1px)` для front/back planes и отдельный `prefers-reduced-motion` fallback. Одновременный рендер трёх карт не требует общей анимации контейнера: каждая карта имеет самостоятельный inner transform и не блокирует layout соседей.

Live проверка показала стабильный результат после открытия первой карты: первая карта зафиксирована в face state, две остальные остаются закрытыми, без просвечивания рубашки, прыжка slot или изменения ширины grid. CSS contract также применяется к daily card и small widget card через соответствующие inner/face selectors.

## 3. Перечень проверенных экранов и компонентов

| Surface | Основные компоненты/модули | Результат |
|---|---|---|
| Сегодня / Home | `06-home.js`, hero, daily ritual, moon section, forecast, day card, natal CTA, agent dock | spacing и desktop/mobile flow проверены |
| Проводники / Hub | `06-home.js`, agent cards, tool disclosure, quick actions, Vedic tools | grid и card hierarchy сохранены |
| Active chat | `05-app.js`, `07-chat.js`, header, message list, composer, tool sheet | desktop canvas/sidebar alignment проверен |
| Tarot ritual | `07-chat.js`, `09-tarot.js`, `.tarot-grid`, `.tpos`, `.tcard` | slot ratio, full fill, clipping и flip исправлены |
| Daily Tarot card | `06-home.js`, `08-widgets.js`, `.tarot-card-big`, `.dc-card` | ratio и image-fit приведены к общему contract |
| Palm scanner | `13-palm.js`, palm upload/quality/geometry panels | mobile overflow runner PASS |
| Compatibility | `11-compat.js`, compatibility form/result | mobile overflow runner PASS |
| Natal chart | `10-chart.js`, chart form/panels/result | mobile overflow runner PASS |
| Placements | `16-placements.js`, tool expansion/result | mobile overflow runner PASS |
| Profile / history / memory | profile renderer, tabs, session history, memory controls | responsive shell и navigation checked |
| Sidebar/drawer | `05-app.js`, `13-events.js`, workspace history search | desktop rail и mobile drawer checked |
| Tool sheet | `13-toolbar-sheet.css`, tool action cards | open/close and width containment checked |
| Public landing RU/EN | `web/landing.html`, `landing-en.html`, `landing.css` | premium editorial structure and responsive stack checked |
| Admin | `admin/admin.js`, `admin/admin.css` | responsive table/drawer styles checked; local visual auth restricted |

Состояния loading, empty и error проверены на уровне существующих renderer branches и API tests. Полная визуальная авторизация admin в локальном dev database невозможна без seeded owner context; strict auth не обходился.

## 4. Design-system and duplication pass

В исправленных поверхностях сохранены ранее принятые foundations: 4/8 spacing rhythm, restrained palette, unified radius/elevation aliases, visible focus states, safe-area mobile padding и reduced-motion handling. Для Tarot устранено расхождение между тремя визуальными реализациями: spread card, daily card и compact widget теперь используют общий принцип source ratio → slot ratio → cover → clipped face.

В рамках этого прохода унифицированы **3 card renderer surfaces** и **11 связанных layout/face selectors**. Дублирующаяся логика не удалялась из JavaScript, поскольку spread/day/widget имеют разные данные и interaction semantics; вместо этого их визуальный contract вынесен в единый финальный CSS layer без изменения API и state model.

## 5. Responsive evidence

Повторный mobile runner после Tarot v109 проверил основные поверхности на ширинах **320, 375 и 390px**. Для Home, Hub/sidebar, Tarot, Palm, Compatibility, Placements и Chart `document.scrollWidth` совпал с `clientWidth`; `horizontalOverflow` оставался `false`.

Desktop live проверки выполнены на workspace shell с sidebar и bounded reading canvas. Для Tarot дополнительно снята geometry evidence в 3-card spread: одинаковые slot/card dimensions, `overflow: clip`, отсутствие лишнего scroll width и корректный opened face state.

## 6. Итог

В рамках данного технического прохода найдено **3 UI/animation несостыковки**:

1. Несогласованный Tarot slot ratio в сочетании с `object-fit: cover`, вызывавший crop.
2. Сжатие grid items относительно tracks, из-за которого карта была меньше своего слота и мог просвечивать соседний элемент.
3. Недостаточно явно зафиксированный 3D flip contract для GPU/backface/reduced-motion states.

Исправлено **3 из 3**, скорректировано **11 layout/face selectors**, унифицировано **3 Tarot card surfaces**. Regression suite завершён успешно; worktree после commit clean.

## 7. Regression checklist

| Проверка | Результат |
|---|---|
| Full `pytest` с `LLM_PROVIDER=off` | PASS |
| Ruff | PASS |
| Mini App/admin JS syntax | PASS |
| Cache-busting | PASS, v109 |
| Mobile overflow QA 320/375/390 | PASS |
| Live Tarot 3-card spread | PASS |
| Opened full-height card | PASS |
| Ghost/sibling clipping | PASS |
| `git diff --check` | PASS |

**Последний commit:** `1be7ff8` — `fix: restore tarot card height and home spacing`  
**Текущий незакоммиченный QA layer:** v109 Tarot slot/flip corrections; будет зафиксирован отдельным commit после финальной проверки.
