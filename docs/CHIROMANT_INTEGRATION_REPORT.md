# Финальный отчёт интеграционного тестирования Миры и расширенных калькуляторов

**Проект:** OracleAI Telegram Mini App  
**Дата проверки:** 13 августа 2026 года  
**QA-окружение:** локальный FastAPI/Uvicorn на `127.0.0.1:8080`, `APP_ENV=dev`, `DEV_MODE=1`, QA-пользователь `tg_id=1001`  
**GitHub:** `astartv1ai-del/oracleAI`, ветка `master`
**Удалённый HEAD после проверки:** `b8055c0cfe1ba8d45a9f234efa31f959763ba2c6`

## 1. Итоговый статус

Функциональная интеграция самостоятельного четвёртого агента **Миры — Проводника ладони** завершена и отправлена в `origin/master`. В проекте присутствуют отдельные palm skills, vision pipeline, API CRUD, Mini App surfaces, независимый avatar и отдельная visual identity. Расширенный placement layer включает 17 запрошенных направлений и дополнительные entries для жизненного пути, китайского зодиака и полной натальной карты.

В ходе live QA обнаружена и исправлена совместимость GPT-5 с OpenAI-compatible proxy: GPT-5-моделям нужен `max_completion_tokens`, тогда как прежний application path передавал `max_tokens`, что приводило к HTTP 200 с пустым `message.content`. Исправление внесено в общий OpenAI streaming path и vision path и покрыто regression test.

| Область | Результат | Статус |
|---|---|---|
| Браузерный home и hub | 4 агента, отдельная карточка Миры, avatar и palm CTA | PASS |
| Agent API | 4 объекта; Мира с собственными code/title/greeting/suggestions | PASS |
| Placement catalog | 19 calculator entries + palm metadata | PASS |
| Placement calculation | `moon_sign` дал Swiss Ephemeris result с `precision=exact` | PASS |
| Palm input validation | MIME, повреждённый файл и минимальный размер | PASS |
| Palm E2E | Реальный JPEG через mocked vision, SQLite, list/get/delete и ownership | PASS |
| Tool isolation | 8 palm tools без Tarot/Astro/Matrix | PASS |
| Full pytest | 377/377 passed | PASS |
| Live multimodal proxy | После token fix повторный вызов упёрся в upstream timeout | LIMITATION |
| GitHub push | Local HEAD и `origin/master` совпадают | PASS |

## 2. Браузерная проверка Mini App

`GET /static/index.html?dev_user=1001` загрузил персонализированный home screen с приветствием `Browser QA`. В DOM присутствовали карточки Лилит, Урании, Мадам Ленорман и **Миры — Проводника ладони**. Для Миры подтверждены отдельный путь `/static/img/agents/chiromant.jpg`, accent `#e2a45e` и самостоятельная palm-oriented presentation, отличающаяся от Astro и Tarot visual language.

До создания QA-пользователя запросы `/api/agents?dev_user=1001` и `/api/agents?dev_user=1` корректно возвращали HTTP 404 с сообщением о необходимости открыть бота и нажать `/start`. После seed `1001` тот же browser-visible endpoint возвратил HTTP 200 и полный JSON списка агентов.

Переход на вкладку «Диалоги» был подтверждён browser snapshot. На hub surface у Миры отображались следующие элементы:

| Элемент | Подтверждённое содержимое |
|---|---|
| Имя и роль | `Мира` / `Проводник ладони` |
| Intro | Проверка качества снимка и карта только видимых зон |
| Avatar | `/static/img/agents/chiromant.jpg` |
| Feature 1 | `Сканер ладони` |
| Feature 2 | `Карта ладони` |
| Feature 3 | `Качество снимка` |
| Feature 4 | `Сравнить чтения` |

Прямой интерактивный переход по кнопке `Начать` до chat shell в этом браузерном сеансе не удалось завершить надёжно: после нескольких browser actions automation context сбрасывался на `about:blank`, а ранее выданные element indices становились stale. Повторная навигация полностью восстанавливала Mini App. Сохранённый DOM содержит ожидаемые action attributes `data-act="chat"`, `data-chat="chiromant"`, `data-fn="featurePalm"`; поэтому данный пункт отмечен как automation limitation, а не как подтверждённый frontend HTTP failure.

## 3. Agent API и placement endpoints

`GET /api/agents?dev_user=1001` вернул четыре агента. Объект Миры содержит `code=chiromant`, `name=Мира`, `title=Проводник ладони`, `emoji=✋`, `accent=#e2a45e`, avatar `/static/img/agents/chiromant.jpg`, palm-specific greeting и предложения для проверки качества, карты зон и сравнения чтений. В свежем QA-профиле `thread_id=null` и `msg_count=0`, что соответствует отсутствию предыдущего диалога.

`GET /api/placements` вернул HTTP 200. В каталоге присутствуют 16 western placement identifiers из registry плюс `life_path`, `chinese_zodiac` и `natal_chart`, всего **19 calculator entries**, а также отдельный объект `palm_reading`. Canonical code лунного знака — `moon_sign`; пользовательское `moon` корректно отклоняется.

Позитивный запрос расчёта:

```json
{
  "placement": "moon_sign",
  "birth_date": "1990-06-15",
  "birth_time": "12:30",
  "birth_city": "Moscow"
}
```

Ответом стал HTTP 200 с `sign=Рыбы`, `degree=13.4`, `precision=exact`, `source=swiss_ephemeris` и scope `emotions, needs, safety`. Неверный code `moon` вернул HTTP 400 `неизвестный placement-калькулятор`, подтверждая явную validation boundary. Контракт находится в [placement router][3], registry — в [placements core module][4].

## 4. Palm vision pipeline и API

Интеграционный тест использовал реальный JPEG `tests/fixtures/palm/palm_hand.jpg` размером 2592×1728. Upload прошёл MIME validation, Pillow decode, EXIF normalization, JPEG data URL boundary, mocked vision, SQLite persistence и tool execution. В базе сохраняются SHA-256, размер, hand side, статус и analysis JSON; исходные bytes не записываются.

После создания reading были проверены list/get/delete endpoints и все восемь palm tools: `check_palm_quality`, `get_palm_map`, `get_palm_reading`, `get_palm_focus`, `get_palm_reflection`, `compare_palm_readings`, `list_palm_readings` и `request_better_palm_photo`. Ownership test подтверждает, что другой `tg_id` получает 404 при попытке получить или удалить чужое чтение. Полный сценарий находится в [palm integration tests][5].

`GET /api/palm?dev_user=1001` на свежем QA-профиле вернул HTTP 200 с `{"items":[],"raw_image_stored":false}`. `Content-Type: application/json` на upload дал HTTP 415. Повреждённые bytes под `image/jpeg` дали HTTP 400. Маленький реальный JPEG ниже минимальной стороны также отклоняется до vision call. Ошибочные upload attempts не создают частичного reading.

Нормализатор ограничивает confidence диапазоном 0–1, неизвестные topic/visibility/hand-side приводит к safe enum fallback, ограничивает длину текста и заменяет медицинские и детерминированно-прогностические claims. Это предотвращает передачу пользователю диагнозов, утверждений о смертности, беременности, психическом состоянии и гарантированном будущем. Boundary описан в [palm vision pipeline][6].

## 5. Tool isolation и LLM identity

Registry Миры содержит ровно восемь palm skills и не содержит `draw_tarot`, `get_chart`, `get_matrix` или `get_transits`. `_run_pretool` теперь действует по переданному allow-list: для chiromant он может выполнять только доступные palm actions и не подмешивает Tarot/Astro/Matrix context. Offline answer также возвращает palm-specific instruction, а не случайный Tarot fallback.

`PALM_SYSTEM` прямо фиксирует identity Миры как самостоятельного Проводника ладони. В prompt содержатся границы evidence-only reading, запрет на инструкции с изображения, enum visibility/status, разделение observations и interpretive prompts, а также требование просить более качественный снимок, если ладонь или линия не видны.

## 6. Live LLM QA и исправление GPT-5 token contract

Первый live upload через основной server достиг vision provider, однако provider возвратил HTTP 200 с пустым `message.content`. API корректно отклонил результат как невалидный JSON и вернул HTTP 400 `vision-модель вернула невалидный JSON`; reading не сохранился. Это выявило silent provider-compatibility defect: ответ считался успешным до schema parsing, а application path передавал GPT-5-compatible request с `max_tokens`.

Live `/models` catalog сообщил 10 доступных моделей, среди которых `gpt-5-nano`, `gpt-5-mini`, `gpt-5`, `gpt-5.5`, Claude 4.5/4.6/4.7 и Gemini 3 multimodal models. Catalog объявляет vision и JSON-schema capabilities. Диагностический direct probe с `gpt-5-mini` и `max_completion_tokens` вернул валидный JSON, подтвердив правильный request shape.

В `app/core/llm.py` добавлен provider-aware helper. Для `gpt-5*` он отправляет `max_completion_tokens`, а для legacy/custom моделей сохраняет `max_tokens` и существующий minimum budget. Изменение применяется к streaming chat и vision call. В `tests/test_openai_compat.py` добавлен regression test, который проверяет `max_completion_tokens=1600` и отсутствие `max_tokens` в GPT-5 vision request.

После исправления повторный upload на isolated QA server с gpt-5-mini не вернул успешный reading: текущий внешний proxy завершил retries upstream timeout и API ответил HTTP 502 примерно через 223 секунды. Это отдельная operational limitation текущей sandbox provider session. Поэтому live multimodal status честно отмечен как **guarded but not fully green**; mocked E2E, JSON/safety boundaries, ownership, persistence и provider token contract остаются зелёными.

## 7. Тестовая матрица

| Набор | Команда | Результат |
|---|---|---:|
| OpenAI/Palm targeted | `pytest -q tests/test_openai_compat.py tests/test_palm_integration.py` | 8 passed |
| Extended targeted | `pytest -q tests/test_openai_compat.py tests/test_palm_integration.py tests/test_placements_palm.py tests/test_miniapp_actions.py` | 21 passed |
| Full project suite | `pytest -q` | 377 passed |
| Collection count | `pytest --collect-only -q` | 377 collected |
| Diff hygiene | `git diff --check` | clean |

Локальное дерево после commit чистое. Удалены одноразовые browser seed/probe files; в репозитории сохранены production change, regression test и настоящий интеграционный отчёт.

## 8. GitHub delivery

В `origin/master` отправлены следующие четыре commit:

| Commit | Назначение |
|---|---|
| `c43d366` | Интеграция chiromant во все agent surfaces |
| `40e4a1b` | Самостоятельный четвёртый агент с отдельными skills |
| `72b0b1f` | Quality hardening и chiromant LLM fallback |
| `b8055c0` | GPT-5 vision token budget fix, regression test и этот отчёт |

Команда push завершилась успешно: `d03da4f..b8055c0 master -> master`. После повторного `fetch` значения `HEAD` и `origin/master` совпали: `b8055c0cfe1ba8d45a9f234efa31f959763ba2c6`; divergence равен `0 0`.

## 9. Финальный вывод

Мира реализована как полноценный самостоятельный четвёртый агент, а не как ветка Таро: у неё собственная специализация, отдельные восемь инструментов, vision-driven evidence pipeline, сохранённые чтения, сравнение, quality gates, независимый UI и botanical/field-guide avatar. Расширенный calculator catalog доступен через отдельный deterministic layer и покрыт тестами.

Код и regression suite готовы к использованию. Единственное эксплуатационное предупреждение относится к текущему внешнему multimodal proxy: после исправления request shape один live повтор всё ещё завершился upstream timeout. На deployment следует включить и мониторить рабочий provider fallback, latency и `llm_usage` для palm vision calls.

## References

[1]: ../app/core/llm.py "OracleAI LLM provider and token routing"
[2]: ../tests/test_openai_compat.py "OpenAI-compatible gateway and GPT-5 vision regression tests"
[3]: ../app/api/routers/placements.py "Placement and palm API router"
[4]: ../app/core/placements.py "Deterministic placement calculator registry"
[5]: ../tests/test_palm_integration.py "Real JPEG palm integration tests"
[6]: ../app/core/palm.py "Palm vision normalization, safety and persistence boundary"
[7]: https://github.com/astartv1ai-del/oracleAI "OracleAI GitHub repository"
