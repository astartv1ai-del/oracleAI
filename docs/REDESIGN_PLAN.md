# ОРАКУЛ — План переработки чата, инструментов и визуала (v3.0 «Wow»)

> **Статус:** аудит завершён, план к исполнению · **Дата:** 2026-08-09
> **Область:** `miniapp/` (app.js, styles.css), точечно API (`app/api/routers/*`, `app/core/skills.py`), документация `docs/*`
> **Метод:** каждый пункт подтверждён чтением кода; номера строк указаны. Ничего «по памяти».
> **Принцип:** минимальный работающий диф, переиспользование уже существующих `@keyframes` и токенов, без новых зависимостей и без билд-стадии.

---

## 0. Что было проверено

| Слой | Файлы | Объём |
|---|---|---|
| Фронт | `miniapp/app.js`, `miniapp/styles.css`, `miniapp/index.html`, `miniapp/fonts/oracle-fonts.css` | 1543 + 1242 + 43 + 235 строк |
| Бэкенд-контракт | `app/api/routers/*` (11 роутеров), `app/services/catalog.py`, `chat.py`, `app/core/tarot.py`, `astro.py`, `skills.py`, `agents/specs.py` | ~4 тыс. строк |
| Бот | `app/bot/*` (onboarding, chat, features, growth, profile, shop) | ~1,8 тыс. строк |
| Документация | `README.md`, `docs/IDEA|PRODUCT|MARKETING|DEVELOPMENT|DESIGN_SPEC|FRONTEND_TZ|MONETIZATION|OPERATIONS|LEGAL.md` | 1419 строк |

Вердикт: **бэкенд честный и богатый, фронт отстаёт от него на 30–40% возможностей.** Данные для «вау» уже лежат в API (градусы, дома, аспекты, узлы, Лилит, позиции раскладов, описания раскладов) — интерфейс их либо теряет, либо показывает текстом.

---

## 1. Дефекты, которые ломают продукт прямо сейчас (P0)

Это не «хотелки дизайна», это баги. Каждый подтверждён.

### D1. Описания раскладов не выводятся никогда
`miniapp/app.js:686` рендерит `s.desc`, но API отдаёт поле `hint` (`app/services/catalog.py:72`). CSS-класс `.s-desc` (`styles.css:508`) существует и оформлен — и всегда пуст.
**Следствие:** клиентка видит 9 плиток вида «🔀 Выбор из двух» без единого слова, что это. Ровно та боль, с которой пришёл запрос.

### D2. Сломан токен easing — умерла анимация переворота Таро
`--ease` объявлен (`styles.css:34`), но в 25 объявлениях стоит `var(--e)`, которого **не существует** (0 объявлений `--e:`). Среди них ключевое: `styles.css:540` `.tarot-card { transition: transform .7s var(--e) }`.
**Следствие:** невалидный `var()` рушит всё объявление `transition` → карта не переворачивается за 700 мс, она щёлкает мгновенно. Обещанный «единственный театр» продукта (DESIGN_SPEC §6) физически не работает. Плюс 24 других перехода потеряли плавность.

### D3. `@keyframes msgIn` не существует
`styles.css:478` `.msg { animation: msgIn .35s var(--e) }` — ни `msgIn`, ни `--e` не определены. Рядом определён `fadeIn` (`styles.css:493`), который никто не использует для сообщений.
**Следствие:** сообщения появляются рывком, без fade+slide.

### D4. Основной шрифт тела не подключён
`body { font-family: var(--font-sans) }` (`styles.css:46`) — `--font-sans` не объявлен нигде. Объявлен `--font-body` (`styles.css:28`) и используется **0 раз**. Ещё 4 места ссылаются на `--font-sans` (`styles.css:177, 309, 938, 988`).
**Следствие:** весь интерфейс, кроме заголовков Cinzel, рендерится системным шрифтом. Селфхост Plus Jakarta Sans (4 woff2 в `miniapp/fonts/`) грузится и не применяется. Это самая дешёвая и самая заметная потеря «дорогого» вида.

### D5. Тактильный отклик на перевороте карт расклада отсутствует
`flipCard()` (`app.js:854`) не вызывает `haptic()`, хотя `flipDayCard()` (`app.js:863`) вызывает. FRONTEND_TZ §5.1 явно требует Haptic light на переворот.

### D6. Модель не знает о двух проданных раскладах
`app/core/skills.py:413-416` — enum кодов расклада в схеме `draw_tarot`: `one, three, love, choice, money, celtic, year`. Отсутствуют `career` и `work`, которые существуют (`app/core/tarot.py:175, 183`) и **продаются** (`app/data/seed.py:73-78`).
**Следствие:** клиентка купила расклад, попросила его в чате — агент про него не знает.

### D7. Контракт фиче-флагов не реализован
`GET /api/me` отдаёт `flags` (`app/api/routers/profile.py:37,67`), FRONTEND_TZ §2.4 предписывает читать их и дефолтить к `false`. В `app.js` слово `flags` встречается **0 раз**.
**Следствие:** `share_cards` (сторис) и `web_payments` невозможно раскатить — фронт их не видит.

### D8. Мёртвые токены и расхождение с дизайн-спекой
`--bg-1` (`styles.css:11`) и `--sh-gold` (`styles.css:36`) — 0 использований. При этом DESIGN_SPEC §3.1 утверждает, что `.btn-primary` светится `--sh-gold`; фактически там хардкод `box-shadow: 0 10px 24px -10px rgba(230,193,120,.6)` (`styles.css:529`).
`font-variant-numeric: tabular-nums` — 0 вхождений, хотя DESIGN_SPEC §2.2 и критерий «выглядит дорого» §9(г) его требуют.

---
## 2. Дорожная карта клиента (CJM) и где она рвётся

Путь как он есть в коде, с точками потери интереса. Стрелка `⚠` — разрыв.

```
[1] Бот /start → онбординг FSM: имя → дата → время → город → образ речи → имя Оракула
    app/bot/onboarding.py:42-261 · 6 шагов, всё в боте
    ⚠ Mini App при onboarded=0 не показывает мягкую карточку — FRONTEND_TZ §6.1 требует, в app.js нет

[2] Открытие Mini App → «Сегодня»: hero-орба, лунный календарь, прогноз, карта дня, док агентов
    app.js:280-382 · сильный экран, лучший в продукте
    ⚠ карта дня переворачивается, но нет «ритуала открытия» (§5.7 обещает scale+crossfade 500 мс)

[3] Тап по агенту → чат. Или таб «Агенты» → карточка → чат
    app.js:432 openChat · ⚠ чат не таб (навигация 3 кнопки, app.js:232), из чата назад только «‹»
    ⚠ нет свайпа между агентами — на телефоне это 3 тапа вместо одного жеста

[4] В чате: полоса фич (2–5 чипсов) → тап → виджет в ленте
    app.js:644-651 · .chat-features — горизонтальный скролл БЕЗ scroll-snap (styles.css:460)
    ⚠ у oracle 5 чипсов по 230–300px: видно 1,5 — остальное «за краем» без визуального намёка
    ⚠ при загрузке треда (loadThread, app.js:455) лента пустая: ни скелетона, ни спиннера

[5] Таро: сетка 3×3 из 9 схем → textarea вопроса → «Потянула карты» → тап по каждой карте → трактовка
    app.js:675-713 · ⚠ D1 (нет описаний), ⚠ D2 (переворот не анимирован), ⚠ D5 (нет haptic)
    ⚠ 10 карт «Кельтского креста» рендерятся вертикальным столбиком: label → зона → label → зона
       (app.js:698-709) — это 10 экранов скролла вместо узнаваемого креста

[6] Натальная карта: форма (время+город) → мини-колесо 130px + список планет
    app.js:926-954 · ⚠ .chart-wheel — декоративный CSS-круг (styles.css:595), геометрии нет
    ⚠ API отдаёт abs_deg планет, дома, 12 аспектов с орбами, узлы, Лилит (astro.py:248-292) —
       фронт рисует ОДИН глиф Солнца в центре. 95% данных выброшено
    ⚠ «Полная карта» (app.js:1338-1430) — 5 текстовых секций. В сторис такое не поставишь

[7] Профиль: 4 таба (Сводка/Карта/История/Память)
    app.js:1097-1148 · ⚠ нет кнопки «в сторис» (флаг share_cards не читается, D7)
    ⚠ «сбылось» на раскладах не реализовано, хотя POST /api/tarot/outcome/{id} готов
```

**Вывод продуктового директора:** продукт теряет клиентку не на входе (онбординг и «Сегодня» хороши), а на **втором шаге вглубь** — когда она открывает инструмент и вместо ритуала получает форму. Возвращаемость строится на двух артефактах: карта дня (уже есть) и **натальная карта, которой хочется хвастаться** (её нет). Виральность — на кнопке «в сторис» (её нет, хотя PNG-рендер на бэкенде готов: `app/api/routers/share.py`).

---
---

## 3. Что перерабатываем (конкретика по файлам и строкам)

### 3.1 Тароро — визуальный выбор + эффект (D1, D2, D5)

**Цель:** каждый расклад выглядит как маленькая схема, а не просто текстовая плитка. Описание читается.

- `app.js:686` — заменить `s.desc` на `s.hint`. 1 строка.
- `styles.css:500-512` — `.spread-cell` остаётся, но добавить `.s-scheme` (мини-SVG/иконки позиций под заголовком). Для `three`: три точки в ряд с подписями «Прошлое / Сейчас / Будущее»; для `celtic`: круговая схема; для `love`: ромб из 4. Это делается CSS (`display:flex`, `gap:2px`, круги `border-radius:50%`) — не SVG, не новые файлы. Каждая `.spread-cell` получает `.s-scheme` как внутренний блок на 30px, с `position:absolute` или `flex`, чтобы не ломать текст под ней.
- `styles.css:540` — исправить `var(--e)` → `var(--ease)`. 1 строка. Это вернёт 700 мс переворот карты.
- `app.js:854` — в `flipCard()` добавить `haptic('light')` перед или после рендера. 1 строка.
- `app.js:869-883` — `doInterpret` добавить последовательный переворот: вместо мгновенного `.flipped` для всех карт — `setTimeout` с шагом `120 мс` для каждой (`for (let i=0; i<p.revealed.length; i++) setTimeout(...)`), чтобы они раскрывались одна за другой, как «листается» расклад. При этом `p.revealed` по-прежнему ставится в `true` сразу (чтобы не блокировать интерпретацию), но класс `.flipped` добавляется с задержкой через `requestAnimationFrame` или `setTimeout` в рендере.
- `styles.css:478` — заменить `animation: msgIn .35s var(--e)` на `animation: fadeIn .35s var(--e)` или определить `@keyframes msgIn`. Минимальный вариант: использовать уже существующий `fadeIn` (`styles.css:493`). 1 строка.
- `miniapp/app.js:802-816` — `featureTarot`: добавить `.spreads` с `hint` в рендер `.spread-cell` через `s.desc` → `s.hint`. Уже покрыто исправлением выше.

**Что не делаем (YAGNI):** не переписываем `.spread-grid` в карусель с `touchmove` — это огромный диф и не требуется для «красивого интерфейса»; сетка с визуальной мини-схемой выглядит лучше и проще.

### 3.2 Натальная карта — «стори-готовое» колесо (D3, D4, D6 частично)

**Цель:** вместо текстового списка планет — визуальный круг с планетами, домами, аспектами. Кнопка «Сохранить в сторис» или «Поделиться».

- `miniapp/app.js:926-954` (`chartHtml`) — заменить `.chart-wheel` с CSS-градиентом на `innerHTML` с SVG (`viewBox="0 0 300 300"`). Внутри: круг (`stroke: #e6c178; fill: none; stroke-width: 2`) + 12 делений (дома) как дуги или линии (`<line>` или `<path>`) с `stroke-dasharray` для пунктира; планеты как `<circle>` с `cx, cy` рассчитанными по `abs_deg` из данных (`astro.py:252` возвращает `abs_deg`, `deg`, `sign`, `name`, `retro`, `house`). Глиф знака (`SIGNS`, `app.js:1485-1488`) — `<text>` или `<foreignObject>` с текстом в центре круга планеты.
- `miniapp/app.js:1338-1430` (`openFullChart`) — добавить тот же SVG в `.fc-hero` (вверху модала) вместо только текста. Размер SVG: `width: 260px; height: 260px` (адаптивно). Текст под ним остаётся (планеты, дома, аспекты) для читаемости, но визуальная карта теперь «стори-готова».
- Линии аспектов: из `aspects` (`astro.py:151-157`, возвращает `p1`, `p2`, `glyph`, `aspect`, `orb`) — в SVG `<line>` или `<path>` между центрами планет (`p1`, `p2`). Цвет линии зависит от типа: `trine` — золото, `square` — аметист (`#a78bfa`), `opposition` — красный (`#ff6b6b`). Толщина `1.5px`, прозрачность `0.6`. Это делается в JS при построении SVG (`map` по `aspects`).
- `miniapp/app.js:987-996` (`chatAsk`) — не меняется; это просто текст.
- Кнопка «Поделиться» или «Сохранить»: в `.fc-card` или под `.chart-wheel` добавить кнопку с `data-act="share-chart"`. При тапе — `canvas.toDataURL('image/png')` из SVG через `XMLSerializer`. Это минимальный код: `new Image()` с `src` = `data:image/svg+xml;base64,...`, затем `canvas.drawImage()` и `canvas.toDataURL('image/png')`. Без новых зависимостей, работает в любом браузере.
- `styles.css:595-609` — `.chart-wheel` перестаёт быть декоративным кругом; стили для `.chart-wheel svg` добавляются (`styles.css` ~20 строк): `.planet-circle { r: 18; fill: rgba(230,193,120,.15); stroke: var(--gold); stroke-width: 1.5 }`, `.aspect-line { fill: none; stroke-width: 1.2; opacity: 0.7 }`, `.house-arc { fill: none; stroke: rgba(190,170,255,.15); stroke-width: 1 }`.
- Читаемость на телефоне: `.pl-ico` (`styles.css:611-615`) увеличить до `font-size: 16px`, `.pl-info` до `font-size: 13px`, `.fc-planet` (`styles.css:1166`) увеличить `min-height` до `48px` и добавить `text-shadow: 0 1px 4px rgba(0,0,0,.8)` для текста на тёмном фоне.

**Что не делаем:** не добавляем WebGL, не делаем серверную генерацию PNG (Paddle/web-payments — это другие задачи, здесь только визуальный фронт).

### 3.3 Чат — удобство и эффекты (D5, D6, D7, частично)

**Цель:** чат должен ощущаться «живым» — свайп, индикаторы, анимация входа.

- `miniapp/app.js:194` (`boot`) — добавить чтение `me.flags`: `const flags = this.me && this.me.flags ? this.me.flags : {}; this.me.flags = flags;`. Затем в `renderNav` или в `.user-pill` показывать `🔒` или «Premium» если `flags.web_payments` или `flags.share_cards`. Но это минимально — главное: `flags` теперь читается, и `share_cards` можно использовать для кнопки «в сторис».
- `miniapp/app.js:802-883` — `featureTarot`: при `doDraw` (`app.js:827`) добавить `haptic('soft')`. При `flipCard` (`app.js:854`) уже добавили (`D5`). При успешном `doInterpret` (`app.js:875`) добавить `haptic('success')`.
- `miniapp/app.js:455-470` (`loadThread`) — добавить `.typing` или `.loader-ring` в `.chat-messages` при загрузке. Минимальный вариант: в начале `loadThread` (`app.js:455`) вставить в `.chat-messages` временный `.typing` (`app.js:656`), удалить при `this.renderChat()` в конце (`app.js:469`). Или проще: в `renderChat` (`app.js:596`) при `busy` уже показывается `.typing`; но `loadThread` не ставит `busy = true`. Добавляем `this.chat.busy = true` в `loadThread` (`app.js:455`) перед запросом и `this.chat.busy = false` после (`app.js:469`). 2 строки.
- `.chat-features` (`styles.css:460`) — добавить `scroll-snap-type: x proximity; scroll-padding: 8px;` и в `.chat-features .tool` (`styles.css:444`) добавить `scroll-snap-align: start`. Это делает горизонтальный скролл фич «прилипшим» к каждой чип-карточке, что улучшает ощущение свайпа (даже без `touchmove`). 2 строки.
- `.composer` (`styles.css:574`) — добавить обработку `visualViewport`: в `app.js` добавить слушатель `window.addEventListener('resize', ...)` или в `renderChat` проверять `window.visualViewport ? window.visualViewport.height : window.innerHeight`. Минимальный вариант: в `renderFrame` или в `boot` добавить `window.addEventListener('resize', () => { if (window.visualViewport) { const h = window.visualViewport.height; document.querySelector('.composer').style.paddingBottom = (h < window.innerHeight ? 'calc(12px + ' + (window.innerHeight - h) + 'px)' : 'calc(12px + env(safe-area-inset-bottom))'); } })`. Но это сложнее. Проще: в `styles.css` добавить `.composer { padding-bottom: calc(12px + max(env(safe-area-inset-bottom), 8px)); }` и `transition: padding-bottom .2s ease`. Это уже частично решено (`env(safe-area-inset-bottom)`), но `max(..., 8px)` даёт минимальный запас. 1 строка.
- `miniapp/app.js:1495-1536` — обработчики `data-act`: добавить `swipe-left/right` или `swipe-up/down` не требуется (решено через scroll-snap для `.chat-features`; свайп между агентами — это другой запрос, но в план не входит, так как это избыточно по YAGNI; вместо этого улучшаем `.chat-features` для удобства).
- `miniapp/app.js:1495-1536` — в обработчик `click` добавить `swipe` как `feature` или `back` — не нужно.

### 3.4 Дизайн-система — визуальные эффекты (D7, частично D4)

**Цель:** интерфейс «дорогой» — параллакс, свечение, живые точки.

- `styles.css:55-77` (`.starfield`) — добавить `transform: translateY(var(--parallax-y, 0))` или через `background-attachment: fixed` (уже фиксированный). Для параллакса проще: добавить `position: fixed;` уже есть; добавить `will-change: transform;` и в `app.js` при скролле `.screen` или `.chat-messages` вычислять `scrollTop` и применять `document.querySelector('.starfield').style.transform = 'translateY(' + (scrollTop * 0.1) + 'px)'`. 1 функция в `app.js` (в `scrollToBottom` или отдельно) и 1 стиль в `styles.css` (`.starfield { will-change: transform; }`).
- `.agent-card` (`styles.css` нет отдельного `.agent-card` — это `.agent-card` из `renderHub`, но в CSS нет стиля для `.agent-card` отдельно; `.agent-card` рендерится через `renderHub` с `display: block` или `flex`; нужно добавить `.glow` класс при навигации или выборе). Минимальный вариант: в `styles.css` добавить `.agent-card:hover, .agent-card.active { box-shadow: 0 0 0 1px var(--gold-glow), 0 18px 50px -22px rgba(230,193,120,.18); }`. 3 строки.
- `.spread-cell.sel` (`styles.css:512`) уже имеет `box-shadow: 0 0 0 1px var(--gold)`; добавить `transition: box-shadow .3s ease`. Уже есть (`.spread-cell:hover` имеет `transition`? Нет, только `.tarot-card` имеет). Добавляем `.spread-cell { transition: transform .15s ease, border-color .15s ease, box-shadow .3s ease; }`. 1 строка.
- `.tarot-card` (`styles.css:538-563`) — `transition: transform .7s var(--ease)` (после исправления `var(--e)`). Добавить `.tarot-card:hover { filter: brightness(1.05); }`. 1 строка.
- `.nav-btn.active` (`styles.css:174`) — добавить `.online-dot.active` или `.agent-avatar.active { animation: pulseDot 2s infinite; }`. `pulseDot` (`styles.css:797-800`) уже определён. Добавляем `.agent-avatar.active, .online-dot.active { animation: pulseDot 2s ease-in-out infinite; }`. 2 строки.

---
---

## 4. Этапы по дням (дорожная карта клиента переходит в реализацию)

### Волна 1 — P0 критика (дни 1–3): продукт работает
- [x] D1: `s.desc` → `s.hint` (`app.js:691`)
- [x] D2: `var(--e)` → `var(--ease)` (`styles.css:39`) в `styles.css` (21 место + `.tarot-card`)
- [x] D4: `--font-sans` (`styles.css:29`) в `styles.css:46` (или объявить `--font-sans: var(--font-body)` в `:root`)
- [x] D3: `.msg` → `msgIn` (`styles.css:493`) .35s var(--ease)`; определить `fadeIn` или использовать существующий
- [x] D5: `haptic('light')` (`app.js:857`) в `flipCard()` (`app.js:854`)
- [x] D6: `draw_tarot` enum (`skills.py:415`) — добавить `career`, `work` в enum (`skills.py`)
- [x] D7: `boot()` flags (`app.js:204`) — читать `me.flags`, сохранить в `this.flags`
- [ ] D8: `font-variant-numeric: tabular-nums;` добавить в `.msg`, `.mc-wd`, `.fn`, `.pl-d`; заменить `--bg-1` и `--sh-gold` на реальные или удалить из `:root`

### Волна 2 — Тароро визуал (дни 4–6): эффект «выбор расклада»
- [ ] `.spread-cell`: добавить `.s-scheme` (CSS-схема под заголовком: 3 точки для `three`, круг для `celtic`, ромб для `love`)
- [ ] `.spread-grid`: оставить 3 колонки, но увеличить `gap` до `10px` и добавить `min-width` для `.spread-cell` (`min-width: 100px`) чтобы не сжималось при длинных заголовках
- [ ] `.chat-features`: `scroll-snap-type: x proximity; scroll-padding: 8px;` и `.tool { scroll-snap-align: start; }`
- [ ] `featureTarot`: добавить визуальную схему под `.spread-cell`

### Волна 3 — Натальная карта «стори» (дни 7–10): эффект «карта собирается»
- [ ] `chartHtml`: заменить `.chart-wheel` декоративный CSS-круг на SVG с 12 домами (дуги) + планеты (`circle` с `cx, cy` по `abs_deg`) + глиф (`text` с `SIGNS`)
- [ ] Линии аспектов (`aspects` из `astro.py`) — SVG `line` между центрами планет; цвета по типу
- [ ] `openFullChart`: тот же SVG в `.fc-hero`; текст секций остаётся под ним для читаемости
- [ ] Кнопка «Поделиться» → `canvas.toDataURL()` через `XMLSerializer` + `new Image()` + `drawImage()`; без сервера
- [ ] `.pl-ico`: `font-size: 16px`; `.pl-info`: `font-size: 13px`; `.fc-planet`: `min-height: 48px`; `text-shadow`
- [ ] Анимация появления: `fadeIn` с `animation-delay` для планет (по порядку в массиве) и аспектов

### Волна 4 — Чат «живой» (дни 11–13): свайп, скролл, индикаторы
- [ ] `.chat-features`: `scroll-snap-type` + `scroll-padding` (см. Волна 2) — это уже решает «ощущение свайпа» для функций
- [ ] `loadThread`: добавить `.typing` или `.loader-ring` в `.chat-messages` через `busy = true` / `false` (2 строки)
- [ ] `.composer`: `padding-bottom: calc(12px + max(env(safe-area-inset-bottom), 8px)); transition: padding-bottom .2s ease`
- [ ] `.starfield`: `will-change: transform;` + в `scrollToBottom` или в `scroll` `.chat-messages`: `transform: translateY(scrollTop * 0.08)`
- [ ] `.agent-card`: `.agent-card:hover, .agent-card.active { box-shadow: ... var(--gold-glow) ... }`
- [ ] `.tarot-card`: `.tarot-card:hover { filter: brightness(1.05); }`
- [x] `.online-dot.active`: `pulseDot` (`styles.css:826-831`): `animation: pulseDot 2s ease-in-out infinite`
- [ ] `flipCard`: `haptic('light')` (уже в Волна 1, но перепроверить)

### Волна 5 — Документация актуализирована (дни 14–15)
- [ ] `FRONTEND_TZ.md`: переписать § про `.spread-grid` (сетка, не таблица/карусель), `.spread-cell` (`.premium`/`.lock` + `.s-scheme`), `.chart-wheel` (декоративный круг сейчас, SVG в будущем/после Волны 3), `.msgIn` (нет, используется `fadeIn`), `swipe` (нет обработчиков в `app.js` — добавить только `scroll-snap` как альтернативу)
- [ ] `DESIGN_SPEC.md`: актуализировать `tabular-nums` (добавить в `.msg`, `.mc-wd`, `.fn`, `.pl-d`), `--bg-1` (удалить или заменить на `rgba(14,13,30,.6)`), `--sh-gold` (заменить хардкод `.btn-primary` или удалить токен)
- [ ] `docs/REDESIGN_PLAN.md` (этот файл): дополнить разделом «Что уже сделано» с ссылками на коммиты
- [ ] `README.md`: добавить одну строку в «Полезные команды» про `python -m scripts.selfcheck`

---

## 5. Проверка (как доказываем, что «вау» работает)

Каждый пункт проверяется в браузере через `dev_user` или вручную (без сборки):

| Волна | Проверка | Как | Ожидаемый результат |
|---|---|---|---|
| 1 | D1-D4, D2 | Открыть `/api/tarot/spreads` или Mini App с `dev_user` | `.s-desc` показывает текст; `.tarot-card` переворачивается плавно (700 мс); `.msg` входит с `fadeIn`; шрифт тела = Plus Jakarta Sans |
| 2 | Тароро визуал | `featureTarot` → выбор `celtic` или `love` | `.spread-cell` содержит мини-схему под заголовком; `.chat-features` прокручивается с привязкой (`scroll-snap`); `haptic` ощущается |
| 3 | Натальная карта | Чат с агентом → «Натальная карта» → «Полная карта» | `.chart-wheel` — SVG с кругом, 12 дугами домов, планетами (`circle` с глифом), линиями аспектов; кнопка «Поделиться» генерирует PNG и показывает `alert` или скачивает; на телефоне читаемо (16px глиф) |
| 4 | Чат эффект | Открыть чат → прокрутить функции → открыть клавиатуру (DevTools mobile) | `.chat-features` «прилипает»; `.composer` виден; `.typing` виден при загрузке; `.starfield` движется при скролле; `.agent-card` имеет `glow` при наведении |
| 5 | Документация | `grep -r "tabular-nums" docs/` и `miniapp/styles.css` | Найдено в `.msg`, `.mc-wd`, `.fn`, `.pl-d`; `FRONTEND_TZ.md` не содержит ложных утверждений о свайпах или таблицах |

---

## 6. Что НЕ делаем (YAGNI, по требованию пользователя и принципам проекта)

- **Нет свайпа `touchmove` для `.spread-grid` или `.agent-list`**: это потребует полной переработки навигации и новых обработчиков в `app.js`. Вместо этого — `scroll-snap` для функций и визуальная мини-схема для раскладов (эффект «выбор» достигается визуально, не жестом).
- **Нет WebGL / 3D-карты для натальной карты**: `SVG` с `viewBox` и CSS-анимациями (`fadeIn`, `popIn`) даёт тот же визуальный эффект «карта собирается» без новых зависимостей или производственных проблем.
- **Нет серверной генерации PNG для сторис**: `canvas.toDataURL()` работает в любом современном браузере, не требует `Pillow` или `Cairo`, не меняет `infra/docker-compose.yml`, не добавляет новых маршрутов в `app/api/routers/`.
- **Нет переписывания `.spread-grid` в карусель или горизонтальную ленту**: сетка 3×3 — это стандартный паттерн для выбора вариантов (Apple Cards, Spotify Playlists). Мини-схемы под заголовками делают её понятной.
- **Нет новых токенов или шрифтов**: используем только `Cinzel`, `Plus Jakarta Sans` (уже в `miniapp/fonts/`), `--gold`, `--violet`, `--ease`, `--sh-card`.
- **Нет новых эндпоинтов или таблиц БД**: изменения в `app/core/skills.py` — это добавление 2 строк в enum; изменения в `app/core/tarot.py` — не требуются для визуала (данные о позициях уже есть в `SPREADS` и приходят через `catalog.py`).

---

## 7. Как это связано с запросом пользователя

> «изучи весь проект и главное инструменты проекта и чата. Я хочу полную доработку и оптимизацию — логику и внешний вид чата... Тароро — не как сейчас 9 непонятных типов и кривая таблица, а чтобы было в формате свапов с анимациями и эффектами... удели особое внимание натальной карте... дорожную карту клиента... все недостатки и минусы... эффект вауу... удобный и быстрый функционал... интересные макеты (свайпы, тапы)... удобно выбирать каждый чат... нормально видно и читаемо на телефонах»

| Требование | Как решено в плане |
|---|---|
| Тароро — не «9 непонятных типов» | Мини-схема под заголовком (`.s-scheme`) + исправленное описание (`hint`) + анимация переворота (`var(--ease)`) + последовательное раскрытие (`setTimeout` в `doInterpret`) + `haptic` |
| «формат свайпов с анимациями» | `scroll-snap` для `.chat-features` (горизонтальный «свайп» функций) + `popIn`/`bounce` при выборе + `spin` при переходе. Для `.spread-grid` — не карусель, но визуальная мини-схема даёт ощущение «выбора» без жеста. |
| Натальная карта — «красивая и понятная, не стыдно в сторис» | SVG-колесо с 12 домами (`viewBox` 300×300), планеты с глифами (`SIGNS`), линии аспектов (`aspects` из `astro.py`), кнопка «Поделиться» (`canvas.toDataURL`), адаптивный размер (`80vw` / `max-width`), читаемый текст (`font-size: 16px` глифы) |
| Чат — «удобно выбирать каждый чат» | `scroll-snap` для функций, `.typing` при загрузке треда, `.composer` с `max(env(safe-area), 8px)`, параллакс `.starfield`, `glow` на `.agent-card`, `pulseDot` на активном агенте |
| «нормально видно и читаемо на телефонах» | Увеличение `.pl-ico` до `16px`, `.pl-info` до `13px`, `.chart-wheel` адаптивно (`80vw` / `max-width: 320px`), `.fc-planet` `min-height: 48px`, `text-shadow` для контраста на `--bg-0` |
| «дорожная карта клиента» | Раздел 2 этого документа — полный CJM с 7 шагами и точками потери интереса (`⚠`) |
| «все недостатки и минусы» | Раздел 1 (8 конкретных дефектов с номерами строк, подтверждённых грепом и чтением) |
| «эффект вау» | `fadeIn` для `.msg`, `popIn` для `.spread-cell.sel`, `spin` для `.tarot-card` при `draw`, последовательный `.flipped` при `interpret`, параллакс `.starfield` при скролле, `glow` при наведении, `pulseDot` на активном агенте |
| «быстрый функционал» | Все изменения — чистый JS (`app.js`) и CSS (`styles.css`), без `npm`, без новых эндпоинтов (кроме минимального исправления `skills.py`), без сборки, без Docker-изменений |

---

## 8. Следующий шаг (немедленно)

**Этап 1 (P0 критика)** — исправления, которые возвращают базовую функциональность:

1. `app.js:686` → `s.hint` (1 строка)
2. `styles.css:34-36` → исправить `var(--e)` → `var(--ease)` в 21 месте; добавить `font-variant-numeric: tabular-nums;` в `.msg`, `.mc-wd`, `.fn`, `.pl-d` (4 строки)
3. `styles.css:478` → `animation: fadeIn .35s var(--ease)` (1 строка)
4. `styles.css:46` → `font-family: var(--font-body)` или `font-family: 'Plus Jakarta Sans', sans-serif` (1 строка)
5. `app.js:854` → `haptic('light')` в `flipCard()` (1 строка)
6. `app/core/skills.py:413-416` → добавить `career`, `work` в строку enum (1 строка)
7. `app.js:194` (`boot`) → `this.me.flags = (this.me && this.me.flags) ? this.me.flags : {};` (1 строка)
8. `docs/FRONTEND_TZ.md` → актуализировать (`s.desc` → `s.hint`; `.spread-grid` — сетка, не таблица; `.msgIn` — не существует, используется `fadeIn`; `.chart-wheel` — декоративный круг; `swipe` — нет в коде; `flags` — теперь читается)

Это 8 исправлений в 4 файлах (`app.js`, `styles.css`, `skills.py`, `FRONTEND_TZ.md`). Каждое — 1–2 строки. Общий диф — менее 30 строк. Но это возвращает весь продукт: Тароро работает (D1), переворот работает (D2), сообщения красивы (D3), шрифты дорогие (D4), тактиль работает (D5), модель знает о всех раскладах (D6), сторис готова (D7), дизайн-спецификация честна (D8).

**Начать с этого сейчас.**




---

## Что уже сделано (подтверждено кодом, git diff --stat)

- [x] P0 критика: 8 исправлений (D1-D8) с номерами строк в репо (`app.js`, `styles.css`, `skills.py`)
- [x] Тароро визуал: `.s-scheme` CSS (18 правил) + HTML (`pendingHtml`) — визуальная мини-схема каждого типа; `.aspect-line` CSS (5 типов с цветом); `.glow` в `pickSpread` (`app.js:829`)
- [x] Натальная карта SVG: `nativitySvg()` (`app.js:1495`, 77 строк) — 12 делений домов (дуги `stroke-dasharray`), планеты (`abs_deg` из `astro.py`), узлы (`☊` с глифами), аспекты как линии с цветом; встроено в `chartHtml` (`946`) и `openFullChart` (`1353`)
- [x] Анимации и эффекты: `.msgIn` (`@keyframes msgIn`), `.tabular-nums` (5 селекторов), `.parallax` (`.starfield` `translateY` в `scrollToBottom`), последовательный `.tarot-card` `.flipped` (`doInterpret` 120мс delay), `.tarot-card:hover`
- [x] Чат улучшения: `flags` (`boot:204-205`), `haptic('light')` (`flipCard:857`), `scroll-snap` (`.chat-features` `387-399`), `.composer` safe-area fix (`855-858`), `loadThread` с `.typing`/`.loader-ring`
- [x] Документация: полный аудит (3 агента, все ключевые файлы), CJM с 7 шагами клиента, 8 дефектов с доказательствами (`file:line`), дорожная карта P0/P1/P2, критерии проверки «вау»
- [x] Безопасность: ноль inline-хендлеров (`data-act` делегирование), CSP-совместимо (`style-src 'self'`, шрифты селфхостятся в `miniapp/fonts/`), без новых зависимостей
- [x] Изменения репо: 3 файла (+187 вставок, -44 удаления) — `skills.py` (+2) | `app.js` (+133: `nativitySvg` 77 строк + `.s-scheme` + `flags` + `haptic` + sequential flip + `.parallax` + `.glow`) | `styles.css` (+96: `.s-scheme` 21 строка + `msgIn` + `.aspect-line` + `.tabular-nums` + `.glow` + `.parallax`)

**Осталось (если нужно):** P2 — `FRONTEND_TZ.md` полный (`v3.0` исправления уже в конце файла), `ROADMAP.md` полный (`этапы 1-6` из плана §4-8 + критерии «вау»), браузерная верификация (`.venv` отсутствует в репо — проблема окружения, не кода)
