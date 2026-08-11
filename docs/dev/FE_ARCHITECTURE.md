# Архитектура фронтенда miniapp «Оракул»

Vanilla JS + CSS, без фреймворков и сборки. Всё в одном объекте `window.app`.
Интерактивность — через `data-act` + один делегирующий обработчик на документе (CSP запрещает inline-обработчики).

## 1. Где живёт и как раздаётся

| Что | Где |
|---|---|
| Клиент | `miniapp/` в корне репо |
| Раздача | FastAPI монтирует `miniapp/` как статику: `app.mount("/static", StaticFiles(directory=MINIAPP_DIR))` (`app/api/main.py:139`) |
| Корневой URL | `GET /` → `miniapp/index.html` (`app/api/main.py:106`) |
| Кеш | `/static/*` → `Cache-Control: public, max-age=3600`; HTML и API — `no-cache` (`app/api/main.py`) |
| Ассеты без хеша | Имена файлов не содержат хеша (`app.js`, не `app.abc123.js`) → cache-busting через `?v=N` в `index.html` |
| Изображения агентов | `/static/img/agents/{code}.jpg` |
| Изображения карт Таро | `/static/img/tarot/{slug}.jpg` (slug вида `m00`, `wands01`, из поля `img` карты) |

### Bootstrap (`miniapp/index.html`)

Порядок в `<head>/<body>`:

1. `oracle-fonts.css?v=N` — шрифты Cinzel / Plus Jakarta Sans (woff2).
2. `<script src="https://telegram.org/js/telegram-web-app.js">` — CDN Telegram WebApp SDK (единственный внешний скрипт).
3. `styles.css?v=N` — ныне агрегатор `@import` модулей `css/*.css` (см. §4).
4. `<div id="app-root">` — корень приложения, рендер через `app.renderFrame()`.
5. `<div class="starfield">` — фон: звёзды, метеоры, созвездия, туманности, силуэт Лилит (`/static/img/lilith-sil.png`).
6. `app.js?v=N` — весь клиент (монолит, 2700 строк; см. §4 целевую структуру `js/`).

При каждой выкладке, меняющей ассеты, версию надо поднять (`?v=43` → `?v=44`). Забыл поднять — до часа юзеры получают старую копию из кеша.

## 2. Глобальный контракт

Нет сборщика → нет модулей ES/CommonJS. Всё, что нужно нескольким функциям, лежит в глобальной области скрипта `app.js`:

- **`window.app`** (`app.js:2620`) — единственный объект приложения. Все методы — на нём, рендер и обработка экшенов зовутся через `app.*`.
- **Хелперы** (top-level функции):
  - `esc(s)` — экранирование `& < > "`; `rich(s)` — esc + восстановление только закрытых пар `<b>/<i>`; `richMd(s)` — + `**...**` → `<b>`.
  - `api(path, opts)` — fetch-обёртка: добавляет заголовок `X-Init-Data` (из `window.Telegram.WebApp.initData`), поддержка `?dev_user=` для локальной разработки, один ретрай (сетевой сбой всегда; 5xx — только для GET, чтобы не задвоить мутацию на сервере).
  - `haptic(kind)` — haptic-отклик Telegram: `notificationOccurred` для `success/error`, `impactOccurred` для `soft`/`light`. Молча без WebApp.
  - `fmtDate()`, `fmtDay(iso)` — даты по-русски.
  - `moonSvg(emoji, cls)` — SVG-фаза луны из эмодзи (карта `MOON_DISC`); уникальный id градиента на каждый вызов.
  - `toRoman(n)`, `agentSprite(a, cheer)`, `ringSvg(pct)` (круговой прогресс), `careerWindow(d)`.
  - `nativitySvg(c, size)` — SVG-колесо натальной карты (отдельная функция, не метод app).
  - `spreadScheme(code)` — мини-схема расклада точками.
- **Константы**: `WD_SHORT/WD_LOWER/MON_RU` (дни/месяцы), `MOON_DISC`, `AGENT_PROPS` (эмодзи-проп агентов), `FEATURES` (реестр фич-кнопок агентов), `AGENT_FALLBACK`, `CAREER_WIN` (тип карьерного окна по фазе Луны), `TEMPLATES` (шаблоны-фразы по агентам), `SIGNS`/`SIGN_ELEM`/`PLANET_GLYPH` (астрологические таблицы).

Почему глобально: отсутствие бандлера. Один скрипт выполняется последовательно сверху вниз; модальные окна, делегирование и эвенты обращаются к `app` из глобальной области.

## 3. Запуск в Telegram

`const tg = () => window.Telegram && window.Telegram.WebApp;` — безопасный геттер SDK.

При старте `app.boot()` (`app.js:238`):

- `tg().ready()`, `tg().expand()` — показать полноэкранный WebApp.
- `setHeaderColor('#08070f')` — шапка в цвет фона.
- Взаимодействия: `haptic()` (см. §2) + `navigator.vibrate(...)` для «тяжёлых» действий (матрица — 30 мс, отметка дня практики — `[10,40,20]`, отправка — `[10,40,14]`).
- `initViewport` — слушает `window.visualViewport.resize`: когда Telegram поднимает клавиатуру, композер чата получает `padding-bottom` под её высоту (G001).
- Аутентификация: `X-Init-Data` из `tg().initData`; для локальной отладки — `?dev_user=<id>` в URL.

## 4. Интерактивность: `data-act` + делегирование

CSP запрещает inline `onclick/oninput/onkeydown`. Вместо них:

- Каждому интерактивному элементу вешается `data-act="<name>"` (+ опциональные `data-*` параметры).
- Один обработчик `click` на `document` ищет ближайший `[data-act]` (`app.js:2625`) и делает `switch` по `act`, параметры читает из `el.dataset`.
- Вложенные `data-act` (чип внутри карточки): `el.closest('[data-act]')` берёт ближайший — отдельный `stopPropagation` не нужен.
- Дополнительно: `keydown` (Enter в `#chat-input` → `app.doSend()`), `input` (`#tarot-q` сохраняет вопрос в pending, `#chat-input` — черновик в `app.chat.draft`).

Полный реестр кейсов `switch` (58): `go, chat, chat-fn, back, clear, feature, tool-fn, tool-toggle, today-ask, day-flip, matrix-node, matrix-ask, moon-expand, p-action, diary-add, diary-summary, career-day, career-ask, sessions, moon, moon-week, moon-day, ptab, new-session, open-session, del-session, send, fill, memories, full-chart, fc-explain, del-mem, add-mem, pick-open, pick-choose, draw, flip, flip-card, interpret, compat, compat-rel, sphere, spd-toggle, planet, el-filter, reading, share-reading, outcome, ref-copy, report, build, ask, all-readings, bell, ask-chart, share-chart, modal-close, feature`.

## 5. Модульная структура

### 5.1 CSS — уже разбит (фактическое состояние)

`styles.css` = агрегатор `@import` в порядке каскада:

| Файл | Содержимое |
|---|---|
| `00-tokens.css` | `:root` дизайн-токены + базовые `body/*` |
| `01-sky-shell.css` | каркас: `#app-root`, шапка, нижняя навигация, `.starfield` (фон), `.screen` |
| `02-skeleton.css` | скелетоны загрузки, hero-сфера |
| `03-profile.css` | агент-карточки, `.btn`, профиль, память |
| `04-atmosphere.css` | метеоры и мерцающие звёзды (анимации) |
| `05-agents.css` | хабы агентов, док-аватарки, чипы-подсказки |
| `06-composer-chat.css` | чат: лента, композер, лунный календарь на главной |
| `07-home-bg.css` | туманности, чипы, модал-обвязка |
| `08-day-memory.css` | карта дня, память, полная карта, матрица (частично) |
| `09-chart-panels.css` | натальная карта: колесо, плашки, таблицы |
| `10-tarot-carousel.css` | расклад: карты, переворот, выбор схемы |
| `11-misc.css` | онбординг-интро, outcome-чипы, рефералка |
| `12-compat.css` | спидометр любви, фильтр стихий, колесо |
| `13-toolbar-sheet.css` | панель инструментов (bottom sheet), табы агентов |
| `14-widgets.css` | виджеты: карьерные окна, прачки, дневник, день |

### 5.2 JS — целевая структура после рефакторинга (сейчас `app.js` монолит)

Монолит `app.js` (2700 строк) планируется к разбиению на `miniapp/js/`. Целевые модули:

| Модуль | Что несёт (из текущего `app.js`) |
|---|---|
| `01-utils.js` | `esc/rich/richMd`, `api`, `haptic`, `fmtDate/fmtDay`, `moonSvg`, `toRoman`, `ringSvg`, константы `WD_SHORT/MON_RU/MOON_DISC` |
| `02-art.js` | `agentSprite`, `AGENT_PROPS`, `spreadScheme`, SVG-арт |
| `03-data.js` | `FEATURES`, `AGENT_FALLBACK`, `CAREER_WIN`, `TEMPLATES`, `loadAgents`, `loadToday`, `agentSpec` |
| `04-nativity.js` | `nativitySvg`, `SIGNS`, `SIGN_ELEM`, `PLANET_GLYPH`, `planetGlyph`, интерактив колеса (`selectPlanet`, `filterElement`) |
| `05-app.js` | `app`-объект, `boot`, каркас/навигация, `go`, модалы |
| `06-home.js` | `renderHome`, лунный календарь главной, карта дня |
| `07-chat.js` | `openChat`, `renderChat`, `loadThread`, `doSend`, сессии, свайпы, интро чата |
| `08-widgets.js` | `pendingHtml`, `todayWidget`, `moonWidget`, `matrixWidget` |
| `09-tarot.js` | `featureTarot`, `doDraw`, `flipCard`, `doInterpret`, `openReading`, итд |
| `10-chart.js` | `featureChart`, `chartHtml`, `chartForm`, `doBuildChart`, `openFullChart`, шаринг |
| `11-compat.js` | `featureCompat`, `doCompat`, `compatWidgetHtml`, `selectSphere` |
| `12-misc.js` | практики, дневник, карьерные окна, память, разборы, рефералка, уведомления |
| `13-events.js` | делегирование `click/keydown/input` + `app.boot()` — ВСЕГДА подключается последним |

Почему `13-events.js` последний: до него на `window.app` должны существовать все методы, на которые ссылается `switch`. Порядок подключения в `index.html` = порядок номеров; нарушение порядка → `app[v.fn]` в момент клика undefined.

### 5.3 Жизненный цикл

Три экрана + чат-оверлей. `app.view` ∈ `{'home','hub','profile'}`; чат живёт внутри `hub` (`this.chat.key != null` → `renderHub` рендерит чат).

```
boot()
 ├─ Telegram: ready/expand/setHeaderColor
 ├─ renderFrame()  — шапка + #app-main + нижняя навигация
 ├─ api('/api/me') → app.me (имя, флаги, лимиты)
 ├─ loadAgents()   → app.agents  (api /api/agents)
 ├─ loadToday()    → app.today + app.moonWeek
 ├─ go('home')     — первый рендер
 ├─ initSwipe()    — свайп-навигация между экранами + жесты в чате
 ├─ initViewport() — подъём композера под клавиатуру TG
 └─ maybeIntro()   — онбординг-интро (1 раз, localStorage)
```

Состояние:

- `app.me` — `/api/me` (имя, флаги, подписка, кристаллы, allowance).
- `app.agents` — каталог агентов; `app.today`/`app.moonWeek` — прогноз и лунная неделя.
- `app.chat = { key, spec, messages, pending, busy, tid, sessions, draft }` — всё состояние активного чата; `pending` — виджет в полёте (kind: `tarot-pick|tarot-cards|chart|compat|moon|matrix|today|practices|diary|career|history`).
- `app.chart`, `app.spreads` — кеши карты и раскладов.

Рендеры строятся методом `main.innerHTML = ...`; после любых изменений `app.pending`/`messages` вызывается `renderChat(document.getElementById('app-main'))` — полный ререндер ленты. Исключения, работающие точечно по DOM без ререндера: `flipCard` (переворот карты), `addInterpretBtn`, `selectSphere`, `filterElement`.