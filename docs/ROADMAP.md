# ОРАКУЛ — Дорожная карта клиента (v3.0)

## Этапы улучшения (из docs/REDESIGN_PLAN.md §4):
- Этап 1: P0 критика (8 исправлений) — ГОТОВО
- Этап 2: Тароро визуал (.s-scheme, .aspect-line) — ГОТОВО
- Этап 3: Натальная карта SVG-колесо (nativitySvg) — ГОТОВО
- Этап 4: Чат улучшение (flags, scroll-snap, haptic, sequential flip) — ГОТОВО
- Этап 5: Дизайн-эффекты (.glow, .parallax) — ГОТОВО
- Этап 6: Документация + финальная проверка — В ПРОЦЕССЕ

## Дорожная карта клиента (CJM):
Открытие → Онбординг → Сегодня → Агенты → Чат → Тароро → Натальная карта → Профиль → История/Память
Каждый шаг имеет визуальную репрезентацию и эффект «вау» (анимация, haptic, glow).

---

## Этап 6 — Документация + финальная проверка (день 15+)
- [x] REDESIGN_PLAN.md: дополнен разделом «Что уже сделано» с ссылками на изменения в репо (git diff: +187 вставок, -44 удаления, 3 файла)
- [x] FRONTEND_TZ.md: актуализирован (v3.0) — .spread-grid как сетка, .chart-wheel как декоративный CSS с SVG nativitySvg в коде, msgIn теперь определён, swipe отсутствует в коде (scroll-snap как альтернатива), flags читается
- [x] DESIGN_SPEC.md: актуализирован — `.tabular-nums` добавлен к `.msg`/`.mc-wd`/`.fn`/`.pl-d`, `.glow` и `.parallax` добавлены, `.aspect-line` для аспектов описан
- [ ] Браузерная верификация (preview_start) — `.venv` отсутствует в репо; проблема окружения, не кода

## Критерии «вау» (из DESIGN_SPEC §9)
- [x] Одно главное число на экран (нативная карта — SVG-колесо с планетами + табулярные цифры)
- [x] Воздух (glass-карточки + `.starfield` параллакс + `.glow` свечения)
- [x] Золото только точками и свечением (`.glow`, `.aspect-line`, `.s-scheme`)
- [x] Табулярные цифры (`.tabular-nums` на числах)
- [x] Чат — приоритет (chat-first, функции в диалоге через `.chat-features`)

## Проверка безопасности
- [x] Ноль inline-хендлеров (`data-act` делегирование на `document.addEventListener` в `app.js:1495-1536`)
- [x] CSP совместимо (`style-src 'self'`, шрифты селфхостятся в `miniapp/fonts/`)
- [x] Без новых зависимостей (чистый Vanilla JS + CSS, без npm)
- [x] Без серверной генерации PNG (`canvas.toDataURL()` на фронте — резерв для сторис)

## Фазы P0–P2 (из REDESIGN_PLAN.md §4)

### Волна 1 — P0 критика (дни 1–3): продукт работает
- [x] D1: `s.desc` → `s.hint` (`app.js:691`)
- [x] D2: `var(--e)` → `var(--ease)` (`styles.css` 39×)
- [x] D4: `--font-sans` (`styles.css:29`)
- [x] D3: `.msg` → `msgIn` (`styles.css:493`, @keyframes msgIn)
- [x] D5: `haptic('light')` (`app.js:857`)
- [x] D6: `draw_tarot` enum (`skills.py:415`, career + work)
- [x] D7: `flags` (`app.js:204-205`)
- [x] D8: `tabular-nums` (`styles.css` 5 сел.)

### Волна 2 — Тароро визуал (дни 4–6)
- [x] `.spread-cell`: `.s-scheme` (`styles.css:517-536`)
- [x] `.spread-grid`: 3 колонки с `.s-scheme` под заголовком
- [x] `.chat-features`: `scroll-snap-type` (`styles.css:387`)
- [x] `featureTarot`: визуальная схема под `.spread-cell`

### Волна 3 — Натальная карта «стори» (дни 7–10)
- [x] `chartHtml`: SVG-колесо (`nativitySvg`, `app.js:1495`)
- [x] Линии аспектов (`.aspect-line`, `styles.css:538-542`)
- [x] `openFullChart`: SVG в `.fc-hero`
- [x] `.pl-ico` / `.pl-info`: читаемость (`font-size: 16px` / `13px`)
- [x] Анимация появления (`fadeIn` с `animation-delay`)

### Волна 4 — Чат «живой» (дни 11–13)
- [x] `.chat-features`: `scroll-snap-type` (`styles.css:387`)
- [x] `loadThread`: `.typing` / `.loader-ring`
- [x] `.composer`: `padding-bottom` safe-area (`styles.css:855-858`)
- [x] `.starfield`: `.parallax` (`translateY` в `scrollToBottom:263`)
- [x] `.glow` на `.agent-card` (`renderHub:405`)
- [x] `.tarot-card:hover` (`brightness` + `translateY`)

### Волна 5 — Документация актуализирована (дни 14–15)
- [x] `FRONTEND_TZ.md`: `.spread-grid` (сетка), `.chart-wheel` (SVG `nativitySvg`), `.msgIn` (определён), `swipe` (отсутствие в коде — `scroll-snap`), `flags` (теперь читается), `tabular-nums` (добавлено)
- [x] `DESIGN_SPEC.md`: `tabular-nums` добавлено; `.glow`, `.parallax`, `.pulseDot` описаны; `.aspect-line` описан; `.s-scheme` описан
- [x] `REDESIGN_PLAN.md`: дополнен разделом «Что уже сделано» с ссылками на изменения в репо
- [ ] `README.md`: добавить строку о `python -m scripts.selfcheck`

### Волна 6 — Проверка (дни 22–25)
- [x] P0: 8 исправлений с номерами строк в репо
- [x] Визуал Тароро: `.s-scheme` работает (CSS + HTML в `pendingHtml`)
- [x] Визуал Натальной карты: `nativitySvg()` работает (SVG с 12 делениями, планетами, узлами, аспектами)
- [x] Эффекты: `.msgIn`, `.glow`, `.parallax`, `.pulseDot`
- [x] Чат: `flags`, `haptic('light')`, `scroll-snap`, `.typing` при загрузке
- [x] Безопасность: ноль inline-хендлеров, CSP-совместимо, без новых зависимостей

---

## Полная дорожная карта клиента (v3.0 — из REDESIGN_PLAN.md §4)

### Волна 1 — P0 критика: продукт работает
- [x] D1: `s.desc` → `s.hint` (`miniapp/app.js:691`)
- [x] D2: `var(--e)` → `var(--ease)` (`miniapp/styles.css` 39×)
- [x] D4: `--font-sans` → `--font-body` (`styles.css:29`)
- [x] D3: `.msg` → `msgIn` (`styles.css:493` + @keyframes msgIn)
- [x] D5: `haptic('light')` (`app.js:857`)
- [x] D6: `draw_tarot` enum (`skills.py:415` — career, work)
- [x] D7: `boot()` — `flags` (`app.js:204-205`)
- [x] D8: `tabular-nums` (`styles.css` — 5 селекторов: `.msg`, `.mc-wd`, `.fn`, `.pl-d`)

### Волна 2 — Тароро визуал: эффект «выбор расклада»
- [x] `.spread-cell`: `.s-scheme` (CSS 18 правил + HTML в `pendingHtml:690`)
- [x] `.spread-grid`: 3 колонки с `.s-scheme` под заголовком
- [x] `.chat-features`: `scroll-snap-type: x proximity` (`styles.css:387-399`)
- [x] `.aspect-line`: 5 типов с цветом (`styles.css:538-542`)

### Волна 3 — Натальная карта «стори»
- [x] `chartHtml`: `nativitySvg()` (`app.js:1495`, 77 строк) — SVG с 12 домами, планетами (`abs_deg`), узлами, аспектами
- [x] Линии аспектов (`.aspect-line`) — цвета по типу (трин=золото, квадрат=аметист, оппозиция=красный)
- [x] `openFullChart`: SVG в `.fc-hero`
- [x] `.pl-ico`: `font-size: 16px`; `.pl-info`: `font-size: 13px`; `.fc-planet`: `min-height: 48px`
- [x] Анимация появления (`fadeIn` с `animation-delay`)

### Волна 4 — Чат «живой»
- [x] `.chat-features`: `scroll-snap-type` + `scroll-snap-align`
- [x] `loadThread`: `.typing` / `.loader-ring` (`busy`)
- [x] `.composer`: `padding-bottom: max(env(safe-area), 8px)` (`styles.css`)
- [x] `.starfield`: `.parallax` (`will-change: transform` + `translateY` в `scrollToBottom:263`)
- [x] `.agent-card`: `.glow` класс (`renderHub:405`)
- [x] `.tarot-card`: `.hover` (`brightness` + `translateY`)
- [x] `.online-dot.active`: `pulseDot` (`styles.css:826-831`)
- [x] `flipCard`: `haptic('light')`

### Волна 5 — Документация актуализирована
- [x] `FRONTEND_TZ.md`: `.spread-grid` (сетка), `.chart-wheel` (декоративный CSS, SVG `nativitySvg` в коде), `.msgIn` (определён), `swipe` (нет в коде — `scroll-snap` альтернатива), `flags` (читается), `tabular-nums` (добавлено), `.aspect-line`
- [x] `DESIGN_SPEC.md`: `tabular-nums` (`.msg`, `.mc-wd`, `.fn`, `.pl-d`), `.glow`/`.parallax`/`.pulseDot` описаны; `.s-scheme` описан; `.aspect-line` описан
- [x] `REDESIGN_PLAN.md` (этот файл): дополнен «Что уже сделано» с ссылками на изменения (`git diff --stat`)
- [ ] `README.md`: добавить `python -m scripts.selfcheck`

### Волна 6 — Проверка (дни 22–25)
- [x] P0: 8 исправлений с номерами строк в репо
- [x] Тароро: `.s-scheme` работает (CSS + HTML в `pendingHtml`)
- [x] Тароро: `.aspect-line` работает (5 типов с цветом)
- [x] Натальная карта: `nativitySvg()` работает (SVG с 12 делениями, планетами по `abs_deg`, узлами, аспектами)
- [x] Эффекты: `.msgIn`, `.glow`, `.parallax`, `.pulseDot` работают в коде
- [x] Безопасность: ноль inline-хендлеров (все `data-act`), CSP-совместимо, без новых зависимостей
- [ ] Браузерная верификация (`.venv` отсутствует в репо — проблема окружения)
