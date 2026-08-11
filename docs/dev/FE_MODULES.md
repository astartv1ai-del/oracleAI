# FE_MODULES.md — каталог модулей и протоколы данных

Целевая структура после рефакторинга. Все модули — классические `<script>`, единый глобальный объект `window.app` (методы добавляются как `app.method = function() {...}`). Порядок подключения в `index.html` жёсткий: данные/хелперы раньше, события последним.

## Таблица модулей `miniapp/js/`

| Файл | Что содержит | Добавляет к `app` | Зависит от |
|---|---|---|---|
| `01-utils.js` | `tg, haptic, api, esc, rich, richMd, fmtDate, fmtDay, toRoman` | — (хелперы) | — |
| `02-art.js` | `agentSprite, moonSvg, ringSvg, careerWindow` (SVG-генераторы) | — | utils |
| `03-data.js` | `FEATURES, TEMPLATES, SIGNS, SIGN_ELEM, PLANET_GLYPH, signElement, spreadScheme` | — | utils |
| `04-nativity.js` | `nativitySvg` (SVG-колесо натальной карты) | — | utils, data |
| `05-app.js` | `const app = window.app = {}` + состояние (state, view, chat) + init: `initViewport, initSwipe, maybeIntro, maybeChatGuide, renderFrame, navItems, renderNav, go, scrollToBottom, agentSpec` | ядро | utils, data |
| `06-home.js` | Экраны «Сегодня»/«Хаб» | `renderHome, renderHub` | app, utils |
| `07-chat.js` | Окно чата, агент-табы, тулбар, свайпы, сессии | `openChat, toast, toggleSessions, toggleMoonWeek, collapseMoonDays, toggleMoonDay, openMoon, switchPTab, renderChat, pendingHtml, closeChat, cycleAgent, setToolbox, toggleToolbox, pendingQ` | app, utils, data |
| `08-widgets.js` | Виджеты в сообщениях + их интеракция | `moonWidget, todayWidget, matrixWidget, practicesWidget, diaryWidget, diarySummaryHtml, careerWidget, todayFlip, todayAsk, selectMatrixNode, matrixAsk, expandMoonDay, careerDay, careerAsk` | app, utils, data, nativity |
| `09-tarot.js` | Таро: колода, расклады, пикер, флип | `openSpreadPicker, chooseSpread, flipCard, addInterpretBtn, flipDayCard, doDraw, doInterpret` | app, utils, data |
| `10-chart.js` | Натальная карта: форма, колесо, аск, PNG-экспорт | `chartHtml, chartForm, chatAsk, fillInput, askChart, downloadPng, downloadUrl, shareChart, selectPlanet, filterElement` | app, utils, nativity |
| `11-compat.js` | Совместимость: спидометр, сферы, выбор связи | `featureCompat, setCompatRel, compatWidgetHtml, selectSphere, toggleSpdAnswer, doCompat` | app, utils, data |
| `12-misc.js` | Модалы, память, чтения, рефералка, отчёты | `renderMemModal, showModal, closeModal, openMemories, openFullChart, explainChart, delMem, addMem, openReading, shareReading, setOutcome, refCopy, openReport, doBuildChart, openAllReadings, openBell, shareChart, newSession, openSession, delSession, doSend, askAgent` | app, utils, data |
| `13-events.js` | `window.app = app` + делегирование click/keydown/input по `data-act` (57 кейсов) + boot | экспорт | ВСЁ |

Правило зависимостей: модуль может ссылаться на глобалы из файлов выше по порядку; вверх — нельзя. `13-events.js` всегда последний.

## CSS-модули `miniapp/css/`

| Файл | Тема |
|---|---|
| `00-tokens.css` | `:root` дизайн-токены + базовый сброс `*, html, body` |
| `01-sky-shell.css` | звёздное небо, app-shell, шапка, навигация, колокольчик, карточки |
| `02-skeleton.css` | скелетон, «Сегодня» (hero-orb, карта дня, dock, хаб) |
| `03-profile.css` | профиль в табах, агент-карточки, чипы, чат-начало, статистика, модал |
| `04-atmosphere.css` | метеоры, twinkle, полярная, reduced-motion |
| `05-agents.css` | dock-grid, луна, compact-карточки, теги памяти, онлайн, ask-чипы |
| `06-composer-chat.css` | композер, пузыри, виджеты, главная, hero-moon, лунный календарь |
| `07-home-bg.css` | туманность, скроллбары, шаблоны-фразы |
| `08-day-memory.css` | карта дня (3D-арка), память-модал, полная карта-секции |
| `09-chart-panels.css` | наталка-таблицы, масштаб, сессии, toast, свечения, параллакс |
| `10-tarot-carousel.css` | карусель раскладов, RWS-колода, пикер-схем |
| `11-misc.css` | рефералка, outcome, онбординг, reduced-motion |
| `12-compat.css` | тип связи, спидометр, натальное колесо, легенда стихий |
| `13-toolbar-sheet.css` | агент-табы, тулбар, bottom-sheet, чат-гайд, fresh-glow |
| `14-widgets.css` | утренний прогноз, матрица, карьерные окна, практики, книга судьбы |

`styles.css` — только `@import` в порядке `00→14`. Каскад: поздний файл переопределяет ранний.

## Протоколы данных (поля рендеров, сверено с кодом)

Формат: объект `app.chat.pending` (или ответ API `r`) → используемые поля.

### todayWidget (`/api/today`)
```
p = { loading, sphere, emoji, moon, day, card, forecast, flipped }
```
- `sphere` — выбранная сфера дня (строка-ключ).
- `moon` — данные луны дня (эмодзи/фаза).
- `card` — карта дня (имя/аркан), `flipped` — перевёрнута ли (переворот по тапу).
- `forecast` — текст прогноза; `day` — дата/заголовок.

### moonWidget (`/api/moon*`)
```
p = { days: [...], sel }
```
`days[i]` — элемент лунного календаря (день, фаза, эмодзи). `sel` — выбранный день.

### matrixWidget (`/api/matrix`)
```
p = { loading, selected, data: { <key>: node } }
```
Ключи `data`: `personal, spirit, family, destiny, center, love, money`.
Узел: `{ n, arcana, title, keywords, plus, minus, advice }`.
Интеракция: `data-act="matrix-node" data-key` → `selectMatrixNode`, `matrixAsk`.

### practicesWidget (`/api/practices`)
```
p = { loading, items: [...], error }
```
`items[i]` — практика: `{ code, title, fit, referral, progress, ... }`.
Экшен: `data-act="p-action" data-code data-a`.

### diaryWidget (`/api/diary`)
```
p = { loading, entries: [...], streak, prompt, wroteToday, error }
```
`entries[i]` — запись дневника; `streak` — серия дней; `prompt` — тема дня.
Экшены: `diary-add`, `diary-summary` (`/api/diary/summary`).

### careerWidget (`/api/career`)
```
p = { loading, days: [...], error }
```
`days[i]` — календарный день: `{ emoji, phase, title, ... }`.
Экшены: `career-day` (по `data-i`), `career-ask`.

### compatWidgetHtml (`/api/compat`, `/api/compat/full`)
```
r = { scores, spheres, total, verdict, relation, ... }
```
- `scores` — оценки по сферам (объект).
- `spheres` — массив сфер (`{ key, value, pct, ... }`).
- `total` — итоговый балл; `verdict` — вердикт; `relation` — тип связи (love/friend/work/family).
Экшены: `compat-rel` (выбор связи), `sphere` (тап по сфере), `spd-toggle` (раскрыть ответ).

### Натальная карта (chartHtml / nativitySvg)
```
chart = { planets, houses, aspects, nodes, sun, ascendant }
```
- `planets[i]` — `{ name, sign, abs_deg, retro, ... }`.
- `houses[i]` — `{ n, abs_deg, ... }`; `aspects[i]` — `{ p1, p2, glyph }`.
- `nodes[i]` — `{ name, sign, abs_deg }`; `sun` — `{ symbol, sign }`; `ascendant` — `{ sign }`.
Экшены: `planet` (выбор планеты `data-p`), `el-filter` (стихии), `ask-chart`, `share-chart`, `full-chart`.

## Как добавить новый модуль/виджет (чеклист)
1. Новый файл `miniapp/js/NN-name.js` (классический script), методы через `app.xxx = function() {}`.
2. Подключить `<script src="/static/js/NN-name.js?v=N">` в `index.html` ДО `13-events.js` и ПОСЛЕ своих зависимостей.
3. Кнопку/элемент → `data-act="имя"`, кейс добавить в switch `13-events.js`.
4. Стили — новым файлом `css/NN.css` (или в существующий тематический), токены из `:root`.
5. Добавить `@import url('css/NN.css');` в `styles.css` в порядке каскада.
6. Поднять `?v=N` во всех ссылках `index.html` (js + css) на `+1`.