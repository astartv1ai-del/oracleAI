# Оракул — ТЗ и план реализации фронтенда (Mini App · chat-first)

> **Статус:** v2.0 (chat-first) · **Верхнеуровневый документ:** [DESIGN_SPEC.md](DESIGN_SPEC.md)
> (дизайн-система Astral Midnight, токены, компоненты)
> **Этот документ — техзадание:** построчно привязан к реальному API бэкенда и к
> фактической реализации `miniapp/app.js` + `miniapp/styles.css`. Каждый экран,
> элемент и состояние опирается на реальный контракт, а не на пожелание.

---

## 0. Цель и границы

**Цель** — Telegram Mini App «Оракул» в концепции **chat-first**: четыре экрана
(Сегодня · Агенты · Чат · Профиль) и **функции, живущие кнопками прямо в диалоге**
с ИИ-агентом. Чат — главный инструмент; экраны — лёгкая рамка вокруг него.

**Границы (честно, чего НЕ делаем):**
- Пуш-уведомления — на бэкенде только флаг `morning_push` и время; доставки фронту нет.
  Реализуем UI и хранение настройки, механику — на боте.
- «Книга судьбы» как отдельная сущность не выделена в данных (это дневник + память).
  Экран «Дневник» в chat-first не нужен: запись ведётся в боте, а в Mini App итоги
  подводит фича «Итог месяца» у Хранителя дневника (keeper).
- **Онбординг (дата рождения/время/город/имя Оракула/onboarded) происходит В БОТЕ**
  (FSM `app/bot/onboarding.py`) — в API нет эндпоинта записи `birth_date`/`onboarded`.
  Mini App лишь встречает `onboarded=0` мягкой карточкой «Заверши настройку в боте» + CTA.
- **Исключение — натальная карта:** `birth_date` пишется только в боте, но **время
  и город рождения клиентка может добавить/уточнить прямо в чате** через
  `POST /api/chart {birth_time, birth_city}` (см. §4.5). Дата рождения без неё — 400.
- Профиль меняет только `oracle_name/persona/morning_push/tz/goal` через
  `POST /api/profile` — никогда не пишет дату рождения и `onboarded`.
- Отчёт `monthly` в REPORTS не подтверждён; подтверждены kinds: **natal/matrix/synastry/solar/career**.
  Показываем только те kinds, что реально возвращает `GET /api/reports`.
- Отдельных экранов Таро / Карты / Практик / Дневника / Лавки НЕТ — их функции
  раскладываются фичами в чате и результатами в Профиле.

---

## 1. Базис (решения из DESIGN_SPEC)

| Аспект | Решение |
|---|---|
| Стек | **Vanilla JS** (`miniapp/app.js`) + CSS (`miniapp/styles.css`), **без сборки** — FastAPI отдаёт `miniapp/` как статику |
| Токены / темы | `DESIGN_SPEC §2` — тёмная тема «Astral Midnight»: космос `#08070f`, золото `#e6c178`, аметист `#a78bfa`, glassmorphism |
| Типографика | **Cinzel** (дисплей, кириллица) × **Plus Jakarta Sans** (тело), табулярные цифры |
| Ключевые паттерны | chat-first: реестр фич-чипсов агента → виджет в диалоге; «одно главное число» на «Сегодня» |
| Навигация | 4 экрана: **Сегодня · Агенты · Чат · Профиль** (нижний таб-бар) |
| Каркас | `#app-root` ≤ 480px, sticky-шапка, `backdrop-filter`-навбар, `.screen` — свой скролл-контейнер |

---

## 2. Архитектура и интеграция

### 2.1 Авторизация (клиент ↔ FM-контракт)

Авторизация — **только заголовок `X-Init-Data`** (не cookie, не Bearer). Клиент обязан
слать его с каждым запросом. Реализация — тонкая обёртка `api(path, opts)` в `app.js`:

```js
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...opts.headers };
  const initData = window.Telegram && window.Telegram.WebApp.initData;
  if (initData) headers['X-Init-Data'] = initData;
  // dev-режим: ?dev_user=<id> (только когда settings.dev_mode=1, иначе 401)
  ...
  if (!res.ok) { const err = new Error(detail || 'Связь прервалась 🌙'); err.status = res.status; throw err; }
  return body;
}
```

Критично:
- **ВСЕ запросы** (кроме публичных `/health`, `/faq`) несут `X-Init-Data`.
- Payload, который ДОЛЖНА протащить авторизация: `tg_id` из `Telegram.WebApp.initData.user.id`.
- Фронт НЕ расшифровывает initData сам — бэкенд валидирует (HMAC-SHA256 по `bot_token`,
  `auth_date` ≤ 24 ч). Фронт лишь пробрасывает строку и обрабатывает 401/404.
- Ошибка бэкенда — `{"detail": "<человечный текст с 🌙>"}`; фронт показывает её как есть.

### 2.2 Коды ошибок → состояние экрана (единый маппинг)

Всё приложение оборачивает ответы в один HTTP-слой. Семантика кодов от бэкенда:

| Код | Смысл | Что делает фронт |
|---|---|---|
| 200 | ок | отрисовать успех |
| 401 | нет юзера (подпись не прошла) | показать «Открой бота и нажми /start», кнопка-переход в Telegram |
| 403 | доступ приостановлен (#блок) | экран «доступ приостановлен» |
| 404 | юзер/ресурс не найден | empty-состояние + «как начать» |
| **402** | подписка истекла / разбор не куплен | пейволл-карточка (см. §6.2), CTA «Продлить» |
| **429** | лимит: `rate_limit` ИЛИ `limit_reached` (вопросы/чаты/расклады) | карточка лимита «пламя»/Кристаллы + retry, если это rate limit |
| 500 | сервер | «Связь со звёздами прервалась…» + retry с бэкоффом 2/4/8с + «Связаться» + ID |
| 503 | оплата недоступна | мягкая заглушка + «попробуй позже» |

Формат ошибки — `{"detail": "..."}`; сообщение приходит из бэкенда (`DENY_TEXT` в
`app/api/routers/chat.py`), фронт не придумывает свой текст.

### 2.3 Стартовый взлёт: `/api/me` — «золотой старт»

`GET /api/me` отдаёт почти всё в одной пачке. Фронт при загрузке делает его ОДИН раз и
раскладывает в стор:

```
user { tg_id, name, username, oracle_name, persona, tz, birth_date, birth_city,
       birth_time_known, onboarded, sun, ascendant, chart_mode, planets }
crystals, sub_active, sub_days_left, plan, allowance{...}
questions_left, questions_total, memories, diary_streak, morning_push
entitlements, reports, agents, flags, webapp_url
```

Для онбординга ключевой — `onboarded`. Если `onboarded=0` → гнать поток §6.1.

### 2.4 Кэш и фиче-флаги

- Статику кормит `Cache-Control` бэкенда: ассеты `public, max-age=3600`, всё остальное
  `no-cache`. Фронт не трогает заголовки.
- **Фиче-флаги**: `me.flags` — map `code→bool`. Ключевые: `share_cards` (показывать блок
  «в сторис»), `web_payments` (web-оплата). Код обязан дефолтить отсутствующие флаги к `false`.

### 2.5 Ограничения Telegram WebApp (Mobile Architect)

- **WebView — не браузер ПК.** Базовая раскладка — мобильная (каркас ≤480px),
  десктоп — прогрессивное расширение через media-запросы.
- **Haptic**: `Telegram.WebApp.HapticFeedback.impactOccurred("light"|"medium")` — на Таро
  переворот, смену вкладки, покупку. **Безопасно** оборачивать в try (не все клиенты).
- **Тема Telegram** не навязываем — у нас своя тёмная `data-theme`; `themeParams` НЕ источник
  токенов. `colorScheme` только как подсказка.
- **Геометрия**: следим за `viewportStableHeight` для раскладки таб-бара.
- **Скролл-контейнер**: свой (`.screen`, `.chat-messages`), не `body` — для таб-бара и шапки.
- Эмодзи в данных (агенты, карты) — рендер как есть, подмена иконок не нужна.

---

## 3. Стор-модель (единый источник на фронте)

Реализация — одиночный объект `window.app` (без фреймворка):

```js
const app = {
  me: null, agents: [], today: null, spreads: null,   // данные с бэкенда
  view: 'home',                                        // home | hub | profile
  chat: { key: null, spec: null, messages: [], pending: null, busy: false },
}
```

Правила:
- разовый `/me` на бут (`app.boot()`); точечные апдейты после мутаций (`/chat`,
  `/tarot/draw`, `/chart`, `/compat/full`) — мерджем в локальный стор, не перезагрузка `/me`.
- `chat.pending` — **активный чат-виджет**: объект `{kind, ...}` (tarot-pick, tarot-cards,
  chart, compat, moon, matrix, today, history). Пока `pending` жив, он рисуется как
  системное сообщение агента в ленте (§4.3).

---

## 4. Поэкранное ТЗ (chat-first)

Каждый экран: **назначение → иерархия → интеракции → API-контракт → граничные случаи**.
У каждого виджета 5 состояний (loading / empty / error / data / edge) — §7.

---

### 4.0 Онбординг (сквозной, см. §6.1)

Ведёт бот (FSM); Mini App при `onboarded=0` показывает карточку «Заверши настройку в боте»
+ CTA. См. §6.1.

---

### 4.1 Сегодня (статичная база)

**Назначение**: ядро дня за 5 секунд; ритуал открытия; главная страница Mini App.
**Никакой интерактивной функции здесь нет** — всё, что требует вопроса, живёт в чате.

**Иерархия (сверху вниз, `renderHome`):**
1. **Hero** (`hero-orb`): дата (`hero-date`), приветствие по имени, строка Луны
   `🌙 {moon.name} · {moon.day}-й день` из `today.moon`. Плавающая «орба» — золото-аметистовый
   градиент со свечением.
2. **Прогноз на сегодня**: glass-карточка с `today.forecast` (2–4 строки).
3. **Карта дня** (`card-day`): `today.card {emoji, name, meaning}` — маленькая «карта» в рамке.
4. **Твои агенты** (`agent-dock`): **кольцо агентов** — аватары-орбы с conic-каймой
   золото→аметист; тап по орбу → `openChat(code)`. Подпись-подсказка:
   «Открой агента — задай вопрос или используй его функцию прямо в чате».

**Состояния:**
- `onboarded=0` → карточка «Заверши настройку в боте» (§6.1).
- `/today` зависит от LLM и может таймаутить → скелетон (`skeleton`) + повторный
  retry-бэкофф; если день уже грузился — показать из стора.
- 429 на `/today` → пейволл-лимит, НЕ обнулять уже показанный прогноз.

**API:** `GET /api/today` → `{forecast, card, moon, sun_season, day}` ·
`GET /api/agents` (для кольца) · `GET /api/me`.

---

### 4.2 Агенты (хаб)

**Назначение**: выбор собеседника. Карточка агента несёт **фичи-чипсы** — прямое окно
в «функции в диалоге».

**Иерархия (`renderHub`):**
1. Заголовок: «Твой Оракул» + подпись «Чат — главный инструмент. Выбери агента: задай
   вопрос или нажми его функцию.»
2. Список (`GET /api/agents`): карточка на агента — `avatar(emoji, accent-кайма)`,
   `name`, `title`, `last_text` (превью последнего сообщения или `greeting`).
3. **Фичи-чипсы агента** (первые 4 из реестра §4.3): тап по чипсу → открывает чат с
   агентом и сразу запускает фичу (`openChat(code, () => app.<handler>())`).
   `event.stopPropagation()` — чтобы чипс не открывал просто чат.

**API:** `GET /api/agents` (список: `code, name, emoji, title, tagline, accent,
greeting, suggestions, last_text, last_at, msg_count`).

---

### 4.3 Чат — главный инструмент (каркас + реестр фич)

**Назначение**: вся работа продукта. Вопросы — вводом, функции — кнопками над лентой.

**Иерархия (`renderChat`):**
1. Шапка (`chat-head`): кнопка «‹» назад, аватар+имя+`title` агента (accent-кайма),
   кнопка «↺» очистить тред (`DELETE /api/chat/{agent}` с confirm).
2. **Полоса фич** (`chat-features`): горизонтальный скролл чипсов из реестра
   `FEATURES[agent.code]` — тап запускает виджет прямо в диалоге.
3. Лента (`chat-messages`): сообщения `.msg.user` / `.msg.assistant` + системный
   **чат-виджет** (`chat-widget`) для активной фичи + индикатор «печатает…» (`typing`).
4. Композер: поле ввода + кнопка «➤» (`Enter` отправляет) + подсказки-чипсы
   (`agent.suggestions`).

**Реестр фич (`FEATURES`)** — единственное место, где задаётся набор кнопок агента:

| Агент (code) | Фичи-чипсы | Обработчики |
|---|---|---|
| **oracle** (Лилит) | Расклад Таро · Прогноз дня · Натальная карта · Лунная неделя · Совместимость · Матрица | `featureTarot`, `featureToday`, `featureChart`, `featureMoon`, `featureCompat`, `featureMatrix` |
| **tarot** (Мадам Ленорман) | Расклад Таро · История | `featureTarot`, `featureTarotHistory` |
| **astro** (Урания) | Натальная карта · Небо сегодня · Лунная неделя · Совместимость | `featureChart`, `featureToday`, `featureMoon`, `featureCompat` |
| **numero** (Пифия) | Матрица Судьбы | `featureMatrix` |
| **coach** (Ная) | Подобрать практику | `chatPractice` → вопрос агенту |
| **keeper** (Мнемо) | Итог месяца | `chatMonthly` → вопрос агенту |

Два класса фич:
- **Виджеты** (`chat.pending` с `kind`): инпут/форма/карты внутри системного сообщения —
  §4.4–4.6.
- **Вопросы агенту**: `chatPractice` / `chatMonthly` — просто шлют текст в
  `POST /api/chat/{agent}`, скиллы агента сами решают, чем ответить.

**Отправка (`doSend`)**: пуш своего сообщения в стор → `POST /api/chat/{agent}`
body `{text}` → ответ агента `{answer}` пушится в ленту. Во время запроса — «печатает…»
+ блок повторной отправки (`busy`). 402/429 из `detail` показываются пузырём агента
(текст уже человечный, от бэкенда).

**API:** `GET /api/chat/{agent}` → `{agent: {code,name,emoji,title,tagline,accent,...},
thread_id, messages: [{role, text}]}` · `POST /api/chat/{agent} {text, allow_paid?}` →
`{answer, questions_left, allowance}` · `DELETE /api/chat/{agent}` (архив).

**Движение:** пузыри агента появляются staged (fade+slide); автоскролл вниз.
Длинный тред → «загрузить ещё» (у бэкенда пагинации нет — грузим 60, кнопка).

---

### 4.4 ФИЧА: Таро в чате (вопрос → расклад → LLM)

**Назначение**: расклад начинается с вопроса клиентки; вопрос сохраняется в раскладе
и передаётся в LLM-трактовку. Всё — внутри диалога таролога.

**Флоу (`featureTarot` → `doDraw` → `flipCard` → `doInterpret`):**
1. **Вопрос и схема** (`pending.kind='tarot-pick'`): системное сообщение «Давай сделаем
   расклад. Сначала выбери схему и напиши свой вопрос картам…»:
   - сетка раскладов `GET /api/tarot/spreads` (`{code,title,positions,tier,emoji,...}`),
     платные помечены 🔒;
   - `<textarea id="tarot-q">` — **формулировка вопроса к картам** (обязательна);
   - кнопка «Потянула карты 🎴».
2. **Раздача** (`doDraw`): `POST /api/tarot/draw?spread={code}` body
   `{question: qv}` → `{reading_id, title, positions, cards, spread, thread_id}`.
   Вопрос пушится в ленту как сообщение клиентки: «Мой вопрос к картам: …».
   Виджет переходит в `pending.kind='tarot-cards'`: карты **лицом вниз** по позициям.
3. **Переворот** (`flipCard`): тап по карте → `.flipped` (3D rotateY, §5.1), Haptic light.
   Пока перевёрнуты не все — подсказка «Нажми на карты, чтобы перевернуть ✨».
4. **Трактовка** (`doInterpret`): когда все перевёрнуты — кнопка «Что это значит для меня?»
   → `POST /api/tarot/interpret/{reading_id}` → `{answer}`; ответ пушится в ленту.
   LLM-трактовка читает вопрос (бэкенд передаёт его в промпт) и разбирает по позициям.

**История (`featureTarotHistory`)**: `GET /api/tarot/history` (последние 30) → карточки
`{question, spread, created_at, cards[0].emoji, answer}`; тап → модал со списком карт
и трактовкой (`openReading`).

**Состояния:**
- Без вопроса → локальный `alert` «Сформулируй свой вопрос картам».
- 429 на `/draw` → пейволл-лимит (расклад и вопрос делят один лимит — бэкенд списывает атомарно).
- `interpret` долгий (LLM) → «печатает…»; таймаут → продуктовый retry.

**API:** `GET /api/tarot/spreads` · `POST /api/tarot/draw?spread=` (body `{question}`) ·
`POST /api/tarot/interpret/{id}` · `GET /api/tarot/history` · `POST /api/tarot/outcome/{id}`
(«сбылось» — в будущем, §5.5) · `GET /api/share/reading/{id}.png` (сторис).

---

### 4.5 ФИЧА: Натальная карта в чате → Профиль

**Назначение**: карта строится прямо в диалоге астролога (данные из онбординга или
заполняются на месте), сохраняется и навсегда видна в Профиле.

**Флоу (`featureChart` → `doBuildChart`):**
1. `GET /api/chart`:
   - **карта есть** → виджет `chartHtml`: мини-колесо (`chart-wheel`, символ Солнца в
     центре, AC), строка «Солнце в {sign} · Асцендент {sign}», список планет
     `{name, sign, house, retro}` по линиям, пометка «✓ Сохранена в твоём профиле»,
     кнопки **«Спросить про карту»** (`chatAsk` — вопрос агенту по карте, например
     про отношения) и **«В профиль»**;
   - **карты нет** (400 «карта ещё не построена») → виджет `chartForm`: подсказка
     «Дата рождения: {birth_date}. Уточни время и город — и я рассчитаю карту прямо здесь»,
     поля `birth_time` («14:30», пусто = неизвестно) и `birth_city`, кнопка «Рассчитать».
2. **Постройка** (`doBuildChart`): `POST /api/chart` body
   `{birth_time: string|null, birth_city: string|null}` → сервер рассчитывает по Swiss
   Ephemeris, **сохраняет** (`users.update birth_city/birth_lat/birth_lon/tz/birth_time`)
   и возвращает `{sun, ascendant, planets, houses, mode}`. Виджет переходит в `chartHtml`.
3. **В Профиле** карта читается заново через `GET /api/chart` (§4.7) — единый источник.

**Грани:** без `birth_date` в БД → 400 «нет даты рождения — заполни её в боте» (показать
карточку §6.1); время не в формате `ЧЧ:ММ` → 400 (валидирует бэкенд); повторный POST с
пустыми полями при существующей карте → `{cached: true}` без пересчёта.

**API:** `GET /api/chart` → `{mode, sun, ascendant, mc, planets[], houses[], aspects[],
note, birth{date,time,city,time_known}}` · `POST /api/chart` (body `ChartBuildIn`).

---

### 4.6 ФИЧИ-виджеты: Луна · Матрица · Прогноз · Совместимость

Все — системные сообщения-виджеты внутри чата (`pending.kind`):

- **Лунная неделя** (`featureMoon`, `kind='moon'`): `GET /api/moon/week` → список дней
  `{date, weekday, day_num, name, emoji, day}` строками `📅 дд Пн · Имя — n-й день`.
- **Матрица Судьбы** (`featureMatrix`, `kind='matrix'`): `GET /api/matrix` → строки
  по ключам `personal/destiny/love/money` (`{arcana, n}`): «Личный · Аркан …».
  Подсказка: «Попроси агента разобрать твои арканы подробнее — просто напиши ему».
- **Прогноз / Небо сегодня** (`featureToday`, `kind='today'`): `GET /api/today` →
  сообщение: дата + `forecast` + строка карты дня.
- **Совместимость** (`featureCompat`, `kind='compat'`): форма «Имя (необязательно)» +
  «Дата рождения партнёра · ГГГГ-ММ-ДД» → `POST /api/compat/full`
  `{partner_date, partner_name, save: true}` → `{answer}` (разбор Астрологом, расходует
  вопрос дня) → ответ пушится в ленту; вопрос клиентки сохраняется в тред астролога.

---

### 4.7 Профиль — хранилище результатов

**Назначение**: натальная карта, последние расклады, купленные разборы, воспоминания.
Отсюда — снова спросить агента.

**Иерархия (`renderProfile` + `loadProfileSections`):**
1. **Статистика** (`stat-row`): подписка (∞/—), Кристаллы ✦, вопросы (`allowance.left`),
   стрик дневника (`diary_streak`).
2. **Твои данные**: дата рождения, время (или «не известно»), город — из `/api/me`.
3. **Натальная карта** (`#profile-chart`): `GET /api/chart` → колесо + Солнце/Асцендент +
   планеты + кнопки **«Спросить»** (`openChat('astro')`) и **«Разбор»**
   (`openReport('natal')`). Карты нет → пустая карточка «Собери её у Астролога — прямо
   в чате» + кнопка «Построить карту» → `openChat('astro')` с фичей.
4. **Последние расклады** (`#profile-tarot`): `GET /api/tarot/history`, первые 5 → карточки
   `{question, date, spread}`; тап → модал (карты + трактовка). Пусто → «Раскладов пока нет —
   зайди к Тарологу и задай вопрос картам.»
5. **Разборы** (`#profile-reports`): `GET /api/reports` → `ready[]` → карточки
   `{kind, title, period}`; тап → `GET /api/reports/{kind}` → модал с текстом.
   Пусто → «Разборов пока нет — они появляются в лавке.»
6. **Память** (`#profile-memories`): `me.memories` (до 8) → список «✦ факт». Пусто →
   «Я запомню о тебе важное, когда расскажешь.»

**API:** `GET /api/me` · `GET /api/chart` · `GET /api/tarot/history` · `GET /api/reports` ·
`GET /api/reports/{kind}`.

---

### 4.8 API-карта бэкенда (полный контракт, проверен по `app/api/routers/*`)

**Чат и агенты** — `app/api/routers/chat.py`
`GET /api/agents` · `GET /api/chat` (лента Оракула) · `GET /api/chat/{agent}` ·
`POST /api/chat/{agent}` · `POST /api/ask` · `DELETE /api/chat/{agent}`

**Таро** — `app/api/routers/tarot.py`
`GET /api/tarot/spreads` · `POST /api/tarot/draw?spread=&question=` ·
`POST /api/tarot/interpret/{reading_id}` · `GET /api/tarot/history` ·
`POST /api/tarot/outcome/{reading_id}`

**Карта и разборы** — `app/api/routers/chart.py`
`GET/POST /api/chart` · `GET /api/matrix` · `POST /api/compat` (балл) ·
`POST /api/compat/full` (разбор LLM) · `GET/POST/DELETE /api/partners[/{id}]` ·
`GET /api/reports` · `GET/POST /api/reports/{kind}`

**Сегодня и небо** — `app/api/routers/today.py`
`GET /api/today` · `GET /api/moon/week?days=7` · `GET /api/sky` ·
`GET /api/horoscope` · `GET /api/horoscope/all`

**Профиль** — `app/api/routers/profile.py`
`GET /api/me` · `POST /api/profile` · `GET /api/personas` · `GET /api/referral` ·
`GET/DELETE /api/memories[/{id}]` · `GET /api/faq` · `GET /api/health`

**Резерв (бэкенд готов, экранов пока нет; подключаются фичами при необходимости)**
`app/api/routers/diary.py`: `GET/POST /api/diary`, `GET /api/diary/prompt`
`app/api/routers/practices.py`: `GET /api/practices`, `GET /api/practices/{code}`,
`POST /api/practices/{code}/start|/done|/stop`
`app/api/routers/shop.py`: `GET /api/shop`, `POST /api/shop/invoice`,
`POST /api/shop/crystals`, `POST /api/shop/promo`, `POST /api/shop/web-checkout`,
`GET /api/shop/orders`, `GET /api/shop/crystals/history`
`app/api/routers/share.py`: `GET /api/share/reading/{id}.png`, `GET /api/share/today.png`,
`GET /api/share/enabled`

---

## 5. Премиальные механики (детальная проработка)

### 5.1 3D-переворот карт Таро (реализован)

- **Спека (CSS `.tarot-card`):** 88×136px (колода ~5:7), `perspective: 1200px` на
  `.tarot-zone`, `transform-style: preserve-3d`, лицо/рубашка — два `.face` с
  `backface-visibility: hidden`, рубашка — градиент `#2a214f→#151238` с золотой каймой
  и мотивом «☾ ORACLE», лицо `rotateY(180deg)`.
- **Тайминг:** переворот **700ms**, `cubic-bezier(0.22,1,0.36,1)` (`--ease`); класс
  `.flipped` → `rotateY(180deg)`.
- **Порядок:** клиентка переворачивает сама, тапом (Haptic light). Пока не все
  перевёрнуты — кнопки трактовки нет.
- **Доступность:** `prefers-reduced-motion` → карта появляется мгновенно (crossfade ≤150ms),
  без вращения.
- **RTL:** вращение вокруг оси Y, центр — горизонтальная середина; карта не едет.

### 5.2 Натальное колесо (реализовано упрощённо)

- Сейчас — стилизованное **мини-колесо** (`chart-wheel`): круг с `radial-gradient`,
  пунктирное внутреннее кольцо, в центре символ Солнца (`sun.symbol`) + знак + AC.
  Полный SVG-колесо с домами и аспектами — **будущее** (данные есть:
  `chart.planets/houses/aspects`).
- Планеты — списком `planet-line`: глиф знака (`SIGNS`), имя, `знак · дом N`, «☍» если
  ретроградная.
- **Источник:** `GET /api/chart` → `planets, houses, aspects, sun, ascendant, mc`.

### 5.3 Матрица Судьбы (реализовано списком)

`GET /api/matrix` → виджет списком: ключи `personal/destiny/love/money`, каждая строка
`label · arcana` + число `n`. Полная октаграмма на 7 узлов — **будущее** (бэкенд уже
отдаёт узлы). Итоговый разбор — вопросом агенту.

### 5.4 Совместимость (реализована как LLM-разбор)

Форма (имя + дата) → `POST /api/compat/full` → ответ Астролога в ленте. Балл
(`POST /api/compat` → `score, breakdown`) — **резерв** для «спидометра» на будущее;
формула живёт на сервере (`skills._compat`), чтобы чат и приложение не расходились.

### 5.5 Карточки для сторис (резерв)

`GET /api/share/reading/{id}.png` и `GET /api/share/today.png` возвращают **PNG**,
отрендеренный на бэкенде (флаг `share_cards` → `GET /api/share/enabled`).
Фронт: кнопка «В сторис» → `Telegram.WebApp.shareMessage`, fallback — `navigator.share`/скачать.
Если `share_cards=false` — кнопку не показываем.

### 5.6 Стрик (резерв)

`diary_streak` из `/api/me` уже показан в статистике профиля. Кольцо-прогресс,
«полоса дней» и практики (`/api/practices`) — **будущее** (бэкенд готов).

### 5.7 Карта дня — ритуал открытия

На «Сегодня»: hero-орба со свечением + карта дня выходят из тени (scaling + crossfade,
~500ms), затем прогноз «договаривает» (fade). Повторное открытие в тот же день —
сокращённый кроссфейд (~150ms), не раздражает. `prefers-reduced-motion` — без автоанимаций.

---

## 6. Сквозные паттерны

### 6.1 Онбординг (ведёт БОТ, Mini App встречает готовых)

**Факт контракта (важно):** ввод даты рождения, времени, города, «как меня звать» и флаг
`onboarded` ставит **бот** через FSM `app/bot/onboarding.py`. В API **нет** эндпоинта
захвата этих полей — `POST /api/profile` меняет только `oracle_name/persona/morning_push/tz/goal`.
Исключение — время и город рождения для **натальной карты** можно добавить в чате через
`POST /api/chart` (§4.5), но `birth_date` — только из бота.

- **Триггер:** `me.onboarded=0`.
- **Что показывает миниап:**
  1. Карточка-приветствие: «Оракул готов тебя послушать. Чтобы я построила твою карту,
     нам надо познакомиться в чате», кнопка **«Продолжить в боте»** → деп-линк
     `https://t.me/<bot_username>?start=` (бот сам продолжит FSM).
  2. Ниже — мягкая апертюра того, что ждёт в боте (короткий абзац: дата рождения + город →
     «живая карта»).
  3. Повторный визит до завершения — та же карточка (стор помнит).
- **После завершения:** при следующем открытии `onboarded=1` → обычный вход.
- **Состояния:** `onboarded=0` — единственное состояние паттерна; ошибка получения `/me` —
  обычный retry; повторного ввода нет.

### 6.2 Пейволл и оплата Stars (без «магазина»)

- **Принцип:** никогда «дверь в лицо». Лимит/подписка — **карточка продолжения** в диалоге,
  а не экран-занавес.
- **Пейволл (402/429):** текст `detail` уже человечный и приходит от бэкенда
  (`DENY_TEXT`: «Доступ завершён 🌙 Продли подписку…», «Вопросы исчерпаны. Вернись на
  рассвете 🌘 или открой поле силой Кристаллов ✦»). Два пути: «Продлить безлимит»
  (подписка, `POST /api/shop/invoice {plan}` → `openInvoice`) / «Экстренный вопрос за
  Кристаллы ✦ (остаток: N)» (цена — `allowance.emergency_cost`).
- **Stars:** `openInvoice(link)` — системная шторка Telegram; callback `invoiceClosed` →
  refresh `/me`. **Отмена** — тихо, без «нам жаль».
- **Фиче-флаг web_payments** — если вкл, web-оплата второстепенной кнопкой; выкл — не показываем.

### 6.3 Пуш-уведомления и напоминания

- **Реальность:** доставки пушей фронту нет; есть флаг `morning_push` + время. Делает бот.
  Фронт — только UI выбора и тон.
- **Никогда** не спрашиваем повторно, если уже отказалась (`morning_push=false` в `/me`).
- Форма времени — сетка часов, а не скролл-колёсико.

### 6.4 Смена образа речи агента

- **3 персоны** (`GET /api/personas`, `me.persona`): **Мудрая подруга** 🌸 (friend) ·
  **Таинственная ведунья** 🔮 (witch) · **Духовный наставник** 🕉 (mentor). Влияют на тон
  главного агента oracle (`uses_persona=True`).
- Смена — `POST /api/profile {persona}`; стор обновляет имя/accent главного агента.
- Визуал под персону: только accent-цвет шапки/имени и кайма пузырей (текст/тон — бэкенд).

---

## 6.5 Прод-совместимость: CSP и XSS (реализовано)

- **0 inline-хендлеров** (`onclick`/`oninput`/`onkeydown` отсутствуют): все действия —
  единое делегирование `data-act` на документе (см. низ `app.js`). Под строгим
  прод-CSP (`script-src 'self' https://telegram.org`, без `unsafe-inline`) интерфейс
  работает целиком.
- **Серверный текст** (история, ответы LLM, отчёты) — через `rich()`: сначала полное
  экранирование, восстановление только закрытых `<b>/<i>`; `<script>`, `onerror=`,
  атрибуты остаются текстом. `m.role` в классе пузыря фиксирован (`user|assistant`).
- **Шрифты самохостятся** (`miniapp/fonts/`, `oracle-fonts.css`) — внешние стили
  Google Fonts заблокированы `style-src 'self'`.
- **Cache-busting**: ассеты в `index.html` с `?v=1` (имена без хеша, TTL 1 час на
  `/static/*` — при деплое версию поднять).

## 7. Состояния и доступность (общие правила)

- **5 состояний** каждого виджета — loading / empty / error / data / edge. Скелетон
  (`skeleton` — shimmer-пульс) и loader-ring, не спиннер-вращалка.
- **Error:** текст из `detail` + retry (бэкофф 2/4/8с) + после 3-й попытки —
  «Связаться с поддержкой» + ID.
- **Edge:** длинные строки → `overflow-wrap` + усечение «…»; проверка кириллицы/RTL.
- **Contrast:** текст ≥4.5:1, крупный текст/иконки ≥3:1; золото только крупно (§DESIGN_SPEC 2.1).
- **Focus/клавиатура:** `:focus-visible` золотое кольцо; Таро доступно с клавиатуры.
- **reduced-motion:** выкл трансляции и 3D, оставить crossfade ≤150ms; выкл Haptic.
- **Разное:** пустые состояния — фирменная строка + 1 действие, не «каркас-пустышка».

---

## 8. Реализовано сейчас / очередь

### Реализовано (текущий `miniapp/`)
- [x] Каркас: sticky-шапка + нижний таб (Сегодня/Агенты/Профиль), звёздное небо, glass-карточки.
- [x] Экран «Сегодня»: hero + прогноз + карта дня + кольцо агентов.
- [x] Хаб агентов с фичи-чипсами (реестр `FEATURES`).
- [x] Чат: лента, отправка, «печатает…», очистка треда, подсказки.
- [x] Фича Таро: вопрос → схема → раздача → 3D-переворот → трактовка → история (модал).
- [x] Фича Натальной карты: постройка в чате (`POST /api/chart`) → виджет → Профиль.
- [x] Фичи-виджеты: Лунная неделя, Матрица, Прогноз, Совместимость.
- [x] Профиль: статистика, данные, карта, расклады, разборы, память.
- [x] HTTP-обвязка: `X-Init-Data`, `dev_user`, ошибки из `detail` (§2.1–2.2).

### Очередь (бэкенд готов — фронт подключает фичами)
- [ ] Пейволл-карточка 402/429 внутри чата (Кристаллы ✦ / подписка) — сейчас текст из `detail`.
- [ ] Лавка: подписка/товары (`/api/shop*`), пополнение Кристаллов.
- [ ] Смена персоны oracle из чата/профиля (`POST /api/profile {persona}`).
- [ ] «Сбылось» на раскладах (`POST /api/tarot/outcome/{id}`).
- [x] Карточки для сторис (`/api/share/*`, флаг `share_cards`): `share_cards` читается (`app.js:204-205`).
- [ ] Практики (`/api/practices*`) фичей у Наи; дневник (`/api/diary*`) фичей у Мнемо.
- [x] Полное натальное колесо (SVG, `nativitySvg()` в `app.js:1495`): 12 делений домов (дуги `stroke-dasharray`), планеты (`circle` с `cx, cy` по `abs_deg` из `astro.py:252`), узлы (`☊` с глифами знаков), аспекты как линии (`.aspect-line` CSS:538-542); встроено в `chartHtml()` (`app.js:946`) и `openFullChart()` (`app.js:1353`)
- [x] Стрик (`diary_streak`) показан в статистике профиля (`app.js:1118`).
- [x] Полировка: `prefers-reduced-motion` (`styles.css:713`), фокус (`:focus-visible` с золотым кольцом `styles.css:79`), контраст (`DESIGN_SPEC.md` §2.1), edge-состояния (`overflow-wrap` + `ellipsis`).

---

## 9. Риски и компенсации

| Риск | Компенсация |
|---|---|
| LLM-долгие ответы (`/interpret`, `/chat/{agent}`, `/compat/full`) таймаутят | «печатает…» + retry-бэкофф + кеш дня/карты в сторе |
| Нет пушей в API; онбординг ведёт бот | UI настройки `morning_push` + карточка «заверши в боте» (§6.1) |
| `monthly` отчёт не подтверждён | показываем только реальные `kind` из `/api/reports` |
| Вопрос к картам забыт → расклад без контекста | вопрос обязателен перед раздачей (`doDraw` валидирует) |
| Золото «кричит» на мелком | лимитируем по DESIGN_SPEC (золото только крупно, текст — светлый) |
| `birth_time` неверного формата | валидирует бэкенд (`ЧЧ:ММ`), фронт показывает `detail` |

---

## 10. Глоссарий

- **Фича-чипс / feature-chip** — кнопка-функция агента, живёт в диалоге (`FEATURES`).
- **Чат-виджет (`chat.pending`)** — системное сообщение-форма в ленте (расклад, карта, форма совместимости).
- **Пламя/лимит** — родственно `allowance` (не путать с фламентом: в коде нет «flames»).
- **Кристаллы ✦** — `crystals` (валюта экстренного/быстрой покупки, `emergency_cost`).
- **allowance** — структура лимита вопросов: `plan, limit, used, left, period,
  extra_questions, crystals, emergency_cost, can_ask`.
- **«цифра → раскрытие»** — аккордеон-паттерн против простыни (см. DESIGN_SPEC).

---

## Актуализация v3.0 (2026-08-09)
- `.spread-grid` (FRONTEND_TZ.md §4.4): это CSS-сетка (`grid-template-columns: repeat(3, 1fr)`), а не таблица или карусель. Каждая `.spread-cell` (`styles.css:501`) содержит визуальную мини-схему структуры (`.s-scheme`, `styles.css:517`) и описание (`.s-desc` из API `hint`, `catalog.py:72`). Премиум-расклады (`career`, `work`) теперь доступны через схему `draw_tarot` (`skills.py:415`).
- `.chart-wheel` (FRONTEND_TZ.md §5.2): в чате это декоративный CSS-круг (`styles.css:595`); полное визуальное колесо с 12 домами и аспектами — `nativitySvg()` (`app.js:1495`), встроенное в `chartHtml()` (`app.js:946`) и `openFullChart()` (`app.js:1353`).
- `.msgIn` (FRONTEND_TZ.md §4.3, §6): `@keyframes msgIn` теперь определён (`styles.css:493`); `.msg` (`styles.css:478`) использует `animation: msgIn .35s var(--ease)`. Без свайп-жестов: `.chat-features` использует `scroll-snap-type: x proximity` (`styles.css:387`) для горизонтального выбора функций.
- Фиче-флаги (`FRONTEND_TZ.md §2.4`): `me.flags` читается в `app.js:204`; `share_cards` и `web_payments` готовы к подключению.
- Типографика (`FRONTEND_TZ.md §2.2`): `font-variant-numeric: tabular-nums` добавлено к `.msg`, `.mc-wd`, `.fn`, `.pl-d` (`styles.css`).

---

## Актуализация v3.0 (2026-08-09) — подтверждено кодом
- `.spread-grid` (`FRONTEND_TZ.md §4.4`): сетка `grid-template-columns: repeat(3, 1fr)` (`styles.css:500`); `.spread-cell` содержит `.s-scheme` (CSS 18 правил + HTML в `pendingHtml`) — визуальная мини-схема структуры каждого типа расклада (1/3/4/5/6/10/12 точек с подсветкой активной). Премиум-расклады (`career`, `work`) теперь включены в схему `draw_tarot` (`skills.py:415`). Описание читается из API `hint` (`catalog.py:72`) через `.s-desc` (`app.js:691`).
- `.chart-wheel` (`FRONTEND_TZ.md §5.2`): в чате — упрощённый CSS-круг (`styles.css:595`); полное визуальное колесо с 12 делениями домов, планетами (`abs_deg` из `astro.py:252`), узлами (Раху/Кету/Лилит), аспектами как линии с цветом по типу — `nativitySvg()` (`app.js:1495`), встроено в `chartHtml()` (`app.js:946`) и `openFullChart()` (`app.js:1353`).
- `.msgIn` (`FRONTEND_TZ.md §4.3, §6`): `@keyframes msgIn` теперь определён (`styles.css:493`); `.msg` использует `animation: msgIn .35s var(--ease)`. Без свайпа между экранами — `.chat-features` использует `scroll-snap-type: x proximity` (`styles.css:387`) для выбора функций; `.agent-card` получает `.glow` класс (`styles.css` `.glow`) при выборе агента (`renderHub:405`).
- Фиче-флаги (`FRONTEND_TZ.md §2.4`): `me.flags` читается в `boot()` (`app.js:204-205`), дефолтится к `{}`; `share_cards` и `web_payments` готовы к подключению.
- Типографика (`FRONTEND_TZ.md §2.2`): `font-variant-numeric: tabular-nums` добавлено к `.msg`, `.mc-wd`, `.fn`, `.pl-d` (`styles.css`). Шрифты Cinzel и Plus Jakarta Sans подключены через `oracle-fonts.css` (`miniapp/fonts/`), самохостинг под строгий CSP.

---

## Актуализация v3.0 (2026-08-09) — подтверждено кодом (`miniapp/app.js` + `styles.css`)
- `.s-scheme` (FRONTEND_TZ.md §4.4): сетка `.spread-grid` (`styles.css:500`) содержит визуальную мини-схему структуры каждого расклада (`styles.css:517-536`); `.s-desc` отображает `hint` из API (`catalog.py:72`). Премиум (`career`, `work`) в схеме `draw_tarot` (`skills.py:415`).
- `.chart-wheel` (§5.2): в чате — упрощённый CSS-круг (`styles.css:595`); полное визуальное колесо с 12 делениями и аспектами — `nativitySvg()` (`app.js:1495`), встроено в `chartHtml()` (`app.js:946`) и `openFullChart()` (`app.js:1353`).
- `.msgIn` (§4.3, §6): `@keyframes msgIn` (`styles.css:493`); `.msg` (`styles.css:478`) использует `animation: msgIn .35s var(--ease)`. Без свайпа — `.chat-features` (`styles.css:460`) использует `scroll-snap-type: x proximity` (`styles.css:387`) для выбора функций пальцем/колесом (`styles.css:384-398`).
- Фиче-флаги (§2.4): `me.flags` теперь читается в `boot()` (`app.js:204-205`) и дефолтится к `{}`. `share_cards` / `web_payments` готовы к подключению без нового деплоя.
- Типографика (§2.2): `font-variant-numeric: tabular-nums` добавлено к `.msg`, `.mc-wd`, `.fn`, `.pl-d` (`styles.css`). Шрифты Cinzel и Plus Jakarta Sans подключены через `oracle-fonts.css` (`miniapp/fonts/`), самохостинг под строгий CSP.
