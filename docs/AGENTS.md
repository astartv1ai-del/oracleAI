# OracleAI — карта агентов и инструментов

Дата обновления: **2026-08-26**. Документ описывает текущий registry/runtime и активные product-contract boundaries.

## Как выбирается агент сейчас

В checkout добавлен детерминированный `app/core/agents/routing.py`. Он применяется только когда клиент находится в default-чате `oracle`; явный выбор `astro`, `tarot` или `chiromant` всегда имеет приоритет. Роутер нормализует RU/EN/code-switched текст, считает объяснимые domain signals и возвращает `agent`, `confidence`, `candidates`, `reason` и `auto_route`. При двух hard domains (например, palm + tarot) запрос остаётся у `oracle` с причиной clarification вместо безмолвного смешивания инструментов. Сервис `app/services/chat.py` сохраняет requested/final agent и routing metadata, а Mini App показывает локализованный handoff badge и обновляет активный chat header после безопасного auto-route.

Таким образом, текущая система стала **explicit selection + deterministic intent routing + skill narrowing**, без дополнительного LLM-классификатора. Все specialist calls остаются bounded выбранным агентом, а неоднозначные и off-topic вопросы получают default fallback.

## Реестр агентов

| Код | Пользовательское имя | Зона | Тон | Основные skills | Текущее состояние |
|---|---|---|---|---|---|
| `oracle` | **Лилит** | Бережный общий диалог, Матрица, практики, память и мягкий взгляд на карту | Тёплый, личный, рефлексивный и направляющий к действию | `get_chart`, `get_matrix`, `get_placement`, `get_all_placements`, `get_life_path`, `get_chinese_zodiac`, `suggest_practice`, `recall_diary`, `list_partners`, `save_memory`, `recall_memory` | Реестр и rules присутствуют; нужно проверить file-backed profile и voice regression |
| `astro` | **Урания** | Натальная карта, транзиты, синастрия, выбор дат, карьера | Точный профессиональный язык, каждый термин переводится на бытовой; выводы опираются на placement | `get_chart`, `get_placement`, `get_all_placements`, `get_life_path`, `get_chinese_zodiac`, `get_transits`, `get_moon_week`, `get_career_windows`, `get_compatibility`, `list_partners`, `save_memory`, `recall_memory` | Целевой natal flow: canonical chart contract, strict structured output и evidence-grounded follow-up проходят release QA |
| `tarot` | **Мадам Ленорман** | Расклад Таро/RWS и трактовка только выпавших карт | Спокойный, образный и точный; каждая карта раскрывается через позицию расклада и вопрос | `draw_tarot`, `save_memory`, `recall_memory` | Специализация узкая; проверить UI и off-topic fallback |
| `chiromant` | **Мира** | Evidence-first хиромантия по фото ладони | Наблюдательный и evidence-first; выводы строятся по видимым особенностям кадра, медицинские границы обязательны | `palm_scanner`, `palm_photo_guide`, `palm_history` | Vision/evidence ограничения детально описаны; требуется общий routing/UI audit |

## Общий runtime-контракт

Каждый выбранный агент получает профиль пользователя, язык, доступную память, матричную сводку и `astro.chart_brief`, если карта построена. Для agent-specific prompt добавляются file-backed rules и активные skills. Tools выполняются детерминированным кодом через `app/core/skills.py`; модель не должна вычислять карту, Таро или данные ладони самостоятельно. После LLM-ответа применяется общий safety gate, а короткий/опасный/ошибочный ответ заменяется offline-ответом на реальных детерминированных данных.

Для фиксированного натального разбора `app/core/agent.py` уже формирует evidence через `interpretation.chart_evidence`, выполняет coverage/grounding gate и повторяет генерацию при неполном результате. Canonical natal path использует строгую JSON Schema с bounded sections, validation/retry/fallback и backward-compatible rich-text rendering; legacy charts сохраняются на прежнем пути до миграции.

## Инструментальные домены

| Домен | Ключевые инструменты/сервисы | Источник истины | Ограничения |
|---|---|---|---|
| Натал | `get_chart`, `get_placement`, `get_all_placements`, `astro.compute_chart` | Kerykeion 5.12.9 через Swiss Ephemeris | Дома/ASC/MC только при подтверждённых времени, координатах и timezone |
| Прогноз/тайминг | `get_transits`, `get_moon_week`, `get_career_windows` | Детерминированные расчёты текущего неба | Не обещать события и не имитировать отсутствующие периоды |
| Совместимость | `get_compatibility`, `pair_aspects` | Server-side compatibility service и synastry aspects | Число задаёт структурированный ориентир; чувства и намерения партнёра раскрываются только через подтверждённый контекст |
| Матрица | `get_matrix`, `get_life_path` | `core.matrix` и placements | Практичная рефлексия: значение переводится в наблюдение и следующий шаг |
| Таро | `draw_tarot` | Сохранённые выпавшие карты | Нельзя добавлять невыпавшие карты и точные сроки |
| Ладонь | `palm_scanner`, `palm_photo_guide`, `palm_history` | Vision observations с quality/confidence | Нет медицины, возраста, смерти, беременности, точных сроков или гарантий |
| Память/дневник | `recall_memory`, `recall_diary`, `save_memory` | SQLite с consent и bounded context | Записывать только явные долговременные факты; приватность обязательна |
| Практики | `suggest_practice` | Каталог практик и safety rules | Предлагать конкретный безопасный шаг; при high-stakes темах действуют специальные границы и направление к специалисту |

## Текущие product-contract boundaries

Натальный путь использует canonical chart contract и передаёт агенту `astro.chart_brief`. Структурная синастрия доступна через `synastry_schema_version=1` только для двух owner-scoped exact charts. Структурные транзиты доступны через `transit_schema_version=1` с честной маркировкой `day` или `instant`; агент получает те же deterministic evidence данные. Подробные поля и ограничения описаны в [CHART_PRODUCT_CONTRACTS.md](CHART_PRODUCT_CONTRACTS.md).

Composite и planetary returns пока не являются enabled skills или API paths. Их будущие входы, precision-gates, calculations и acceptance tests описаны в [COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md](COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md).
