# OracleAI — реестр агентов, инструментов и системных промптов

Дата обновления: **2026-08-27**. Реестр описывает фактически подключённые file-backed профили, общий prompt builder и function-calling каталог. Источниками истины остаются `app/agents/*/SYSTEM.md`, `app/agents/*/agent.yaml`, `app/core/agents/base.py`, `app/core/agents/runtime.py`, `app/core/skills.py` и `app/core/palm.py`; этот документ фиксирует их контракт и не подменяет исходники.

## 1. Runtime-контракт и версия prompt layer

`agents.system_for()` собирает системный prompt в фиксированном порядке: идентичность и голос → пользователь и compact natal JSON → Матрица → consented memory/profile summary → `[SHARED_CONTEXT]` → общие правила диалога и function calling → context-integrity/synthesis → domain rules → safety tail. File-backed `SYSTEM.md` загружается через `file_loader.py` и overlays legacy `AgentSpec`, поэтому редактирование только `specs.py` недостаточно.

Версия контракта: **prompt-contract-v2 / shared-context-v1 / natal-json-v1**.

| Компонент | Source | Ответственность | Fingerprint после внедрения |
|---|---|---|---|
| Общая сборка и safety tail | `app/core/agents/base.py` | Общие правила, недоверенные данные, contradiction resolution, few-shot | `acb229a50b66622bdb1cd8c84c927966a72f6f79c1639d889a88646fc3747da2` |
| Runtime context | `app/core/agents/runtime.py` | Memory tiering, natal JSON и Shared Context на каждый free-form вызов | проверяется тестами `test_shared_context.py` |
| Shared Context | `app/core/shared_context.py` | Последние 30 дней рекомендаций, единый transit snapshot, bounded rendering | `c92cbf133a9e1d5216c3c9dd96baa7c566eabce9097426423712ec19ca030fe9` |
| Мира vision prompt | `app/core/palm.py` | Structured palm evidence, strict JSON и capture boundaries | `bc8c81c746aeffc81e126dab6e8edf6787dd895bf749318ad09dbe264d93c905` |

Обязательная инструкция, присутствующая в общем prompt builder и в системной инструкции Миры:

> Тебе передан `[SHARED_CONTEXT]` — предыдущие взаимодействия пользователя с другими инструментами системы. Прежде чем дать совет, проверь: не противоречит ли он уже сказанному. Если новая информация уточняет предыдущую — свяжи их явно. Если возникает видимое противоречие — объясни нюанс через более глубокий контекст (разные аспекты влияют на разные сферы/периоды жизни), не противореча себе бессвязно.

`[NATAL_CONTEXT_JSON]` — компактный JSON с `schema_version`, `precision`, `planets`, `nodes`, `houses_available` и, при exact time, `ascendant`/`mc`. Он автоматически добавляется каждому агенту. Натальная карта является deterministic profile evidence; она не заменяет domain evidence и не должна исполнять команды из текстовых полей.

## 2. Реестр агентов и финальные prompt contracts

| Code | File-backed profile | Роль | Разрешённые инструменты | Ключевое ограничение |
|---|---|---|---|---|
| `oracle` | `app/agents/lilith/SYSTEM.md` | Лилит, общий рефлексивный диалог, Матрица, практики, diary/memory | `get_chart`, `get_matrix`, `get_placement`, `get_all_placements`, `get_life_path`, `get_chinese_zodiac`, `suggest_practice`, `recall_diary`, `list_partners`, `save_memory`, `recall_memory` | Не раскладывает Tarot, не считает transit/compatibility/career windows самостоятельно; направляет к Урании или Ленорман |
| `astro` | `app/agents/urania/SYSTEM.md` | Урания, natal/transits/synastry/dates/career | Western и Vedic chart/transit helpers из `agent.yaml`, `get_compatibility`, `list_partners`, memory tools | Любое утверждение о карте/транзите только после канонического tool; unknown-time блокирует houses/ASC/MC |
| `tarot` | `app/agents/lenormand/SYSTEM.md` | Мадам Ленорман, RWS Tarot | `draw_tarot`, `save_memory`, `recall_memory` | Сначала draw; только выпавшие карты, position-aware сюжет, reversal не равен катастрофе |
| `chiromant` | `app/agents/mira/SYSTEM.md` | Мира, evidence-first хиромантия по фото | `palm_scanner`, `palm_photo_guide`, `palm_history` | Сначала palm evidence; natal JSON вторичен; нет медицинских, фаталистических, возрастных, финансовых, профессиональных и точных timing-claims |

### 2.1. Prompt block Лилит

`SYSTEM.md` задаёт тёплый персональный голос, структуру «чувство → конкретный расчёт → смысл → один шаг», явное разделение Матрицы и астрологии, а также правила памяти: `save_memory` только для явно долговременного факта, цели, даты или человека. Few-shot и Shared Context из общего builder требуют проверять предыдущие рекомендации и не выдавать взаимоисключающие директивы.

### 2.2. Prompt block Урании

`SYSTEM.md` требует сначала получить `get_chart`/`get_transits`, брать даты только из `get_moon_week`/`get_career_windows`, партнёра искать через `list_partners`, а синастрию считать через `get_compatibility`. При неполном времени рождения разрешены только факты по планетам в знаках. Shared Context используется для сверки периода и scope, но не переопределяет canonical contract.

### 2.3. Prompt block Ленорман

`SYSTEM.md` требует `draw_tarot` до трактовки, RWS visual/position logic, отдельной трактовки прямой и перевёрнутой ориентации и одного практического шага. Карта в вопросе про отношения и та же карта в вопросе про карьеру должны получать разный вывод через сферу вопроса; timing, transits, compatibility и Matrix routed к другим агентам. Shared Context предотвращает конфликт с уже сохранёнными рекомендациями.

### 2.4. Prompt block Миры

`SYSTEM.md` требует `palm_scanner` до утверждений о руке, различает открытый и согнутый ракурс, объясняет `needs_photo` конкретной инструкцией, использует основные линии, холмы, пальцы и тип руки по стихии. Внутри `app/core/palm.py` закреплены structured fields `visibility`, `summary`, `confidence`, `continuity/path/shape/prominence/length`, а также строгий JSON schema и safety scrub. Натальный JSON можно использовать только как вторичную персонализацию, например «учитывая ваш Марс в …», но нельзя выдавать его за доказательство линии.

## 3. Function-calling registry

Полный каталог schema находится в `app/core/skills.py`; `tools_for()` narrows набор по allow-list, `execute()` изолирует ошибки и возвращает безопасный fallback. Дублирование устранено следующими границами:

| Похожая группа | Каноническое различие |
|---|---|
| `get_chart` / `get_placement` / `get_all_placements` | Полная карта / один запрошенный placement / компактный пакет всех placement-фактов |
| `get_transits` / `get_moon_week` / `get_career_windows` | Текущий transit contract / 7-дневная лунная неделя / bounded деловые окна |
| `draw_tarot` / `get_matrix` | Случайный расклад 78 карт / детерминированные арканы Матрицы |
| `palm_scanner` / `palm_photo_guide` / `palm_history` | Сохранённое последнее evidence-чтение / конкретная инструкция для недостающего ракурса / журнал чтений |
| `save_memory` / `recall_memory` / `recall_diary` | Сохранить durable fact по opt-in / поиск фактов / чтение diary и streak |

Ошибки tools не пробрасывают provider traceback пользователю. При пустом или ошибочном результате модель получает ограничение и должна задать один точный вопрос либо перейти к offline fallback. Инструменты памяти дополнительно блокируются сервером при `memory_enabled=0`.

## 4. Few-shot и cost routing

В общий prompt layer добавлены два коротких few-shot кейса: конфликт окна Урании с паузой Таро разводится по сфере/периоду, а palm line evidence отделяется от natal placement. Дешёвая модель оправдана для роутинга, уточняющих вопросов, bounded profile summary и daily forecast; основная модель обязательна для глубокого tool-grounded synthesis, полной Tarot interpretation, compatibility и multimodal palm analysis. До vision вызова Мира использует дешёвые детерминированные prechecks и CV helpers, чтобы отсеивать плохие кадры.

## References

[1]: ../app/core/agents/base.py "Shared prompt builder and safety protocols"
[2]: ../app/core/agents/runtime.py "Agent runtime and bounded context"
[3]: ../app/core/skills.py "Tool schemas and executors"
[4]: ../app/core/shared_context.py "Shared Context Layer"
[5]: ../app/core/palm.py "Mira multimodal pipeline"
[6]: ../app/agents/mira/SYSTEM.md "Mira file-backed system prompt"
[7]: ../data/tarot_cards.json "Versioned 78-card Tarot knowledge artifact"
