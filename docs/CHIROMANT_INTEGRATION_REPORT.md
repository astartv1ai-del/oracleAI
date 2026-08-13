# Отчёт интеграционного тестирования Миры и расширенных калькуляторов

**Проект:** OracleAI Telegram Mini App  
**Дата проверки:** 13 августа 2026 года  
**QA-окружение:** локальный FastAPI/Uvicorn на `127.0.0.1:8080`, `APP_ENV=dev`, `DEV_MODE=1`, QA-пользователь `tg_id=1001`  
**Финальный статус до push:** все локальные тесты зелёные; подготовлен дополнительный GPT-5 vision compatibility fix

## 1. Цель и границы проверки

Проверка охватывала самостоятельного четвёртого агента **Миру — Проводника ладони**, его отдельную skill-модель, vision pipeline, API CRUD-контур, Mini App surfaces и новый каталог placement-калькуляторов. Особое внимание уделялось тому, чтобы Мира не получала Tarot/Astro/Matrix-инструменты по fallback-маршруту, не сохраняла исходные изображения и не превращала наблюдения по ладони в медицинские или гарантированные предсказания.

В ходе проверки дополнительно обнаружена и исправлена совместимость с актуальным OpenAI-compatible LLM proxy: для GPT-5-моделей параметр бюджета видимого ответа должен передаваться как `max_completion_tokens`, а не как legacy `max_tokens`. Исправление сделано в общем OpenAI path для streaming chat и vision calls и покрыто отдельным regression test. См. [реализацию LLM token routing][1] и [provider compatibility tests][2].

## 2. Сводка результатов

| Контур | Сценарий | Результат | Статус |
|---|---|---:|---|
| Static UI | Home Mini App с `dev_user=1001` | HTTP 200; 4 карточки агентов | PASS |
| Avatar asset | `/static/img/agents/chiromant.jpg` | HTTP 200, `image/jpeg` | PASS |
| Agent API | `/api/agents?dev_user=1001` | 4 агента; Мира с отдельным code/title/avatar/greeting | PASS |
| Placement catalog | `GET /api/placements` | 19 calculators + palm metadata | PASS |
| Placement calculation | `moon_sign`, дата/время/город | HTTP 200; Swiss Ephemeris result, precision `exact` | PASS |
| Placement validation | Неверный code `moon` | HTTP 400 с ожидаемой ошибкой | PASS |
| Palm history | `GET /api/palm` для нового QA user | HTTP 200, `items: []`, `raw_image_stored: false` | PASS |
| Palm input validation | MIME `application/json` | HTTP 415 | PASS |
| Palm image validation | Повреждённые JPEG bytes | HTTP 400 | PASS |
| Palm ownership | Другой `tg_id` не видит и не удаляет reading | Покрыто E2E тестом | PASS |
| Palm CRUD | upload/list/get/delete | Покрыто mocked-vision E2E на реальном JPEG | PASS |
| Tool isolation | 8 palm tools, без Tarot/Astro/Matrix | Покрыто registry и pre-tool regression tests | PASS |
| Full pytest | Все собранные тесты проекта | 377/377 passed | PASS |
| Live provider upload | Реальный JPEG через configured proxy | Выявлена provider-dependent проблема, описанная ниже | LIMITATION |

## 3. Браузерная проверка Mini App

### 3.1 Home surface

`GET /static/index.html?dev_user=1001` загрузил персонализированный home screen с приветствием `Browser QA`. В извлечённом DOM присутствовали четыре agent cards: Лилит, Урания, Мадам Ленорман и **Мира — Проводник ладони**. Для Миры использовались отдельные avatar path `/static/img/agents/chiromant.jpg`, accent `#e2a45e` и teal/terracotta-oriented visual identity, отличающаяся от космического Astro и Tarot оформления.

До создания QA-пользователя API корректно возвращал HTTP 404 с сообщением о необходимости открыть бота и нажать `/start`. Это подтверждает, что dev query parameter не создаёт пользователя автоматически и не обходит user existence guard. После seed пользователя `1001` браузерный `/api/agents` вернул полноценный JSON-контракт.

### 3.2 Вкладка «Диалоги»

Переход по нижней вкладке «Диалоги» был подтверждён browser snapshot. На hub surface присутствовала отдельная карточка Миры со следующими элементами:

| Элемент | Подтверждённое содержимое |
|---|---|
| Имя и роль | `Мира` / `Проводник ладони` |
| Intro | Снимок одной ладони, сначала проверка качества, затем карта видимых зон |
| Avatar | `/static/img/agents/chiromant.jpg` |
| Palm CTA 1 | `Сканер ладони` |
| Palm CTA 2 | `Карта ладони` |
| Palm CTA 3 | `Качество снимка` |
| Palm CTA 4 | `Сравнить чтения` |

Таким образом, визуальная и информационная регистрация самостоятельного четвёртого агента присутствует на home и hub surfaces, а не только в backend registry.

Прямой интерактивный переход из карточки `Начать` в chat shell в этом QA-сеансе не удалось завершить надёжно: после нескольких browser actions automation context сбрасывался на `about:blank`, а старые element indices становились stale. После повторной навигации Mini App восстанавливался без ошибок. Это ограничение browser automation session, а не HTTP/static failure; сам hub DOM и action attributes (`data-act="chat"`, `data-chat="chiromant"`, `data-fn="featurePalm"`) были подтверждены в сохранённом HTML.

## 4. Проверка API и калькуляторов

### 4.1 Список агентов

`GET /api/agents?dev_user=1001` вернул HTTP 200 и четыре объекта. Для Миры зафиксированы следующие значения: `code=chiromant`, `name=Мира`, `title=Проводник ладони`, `emoji=✋`, `accent=#e2a45e`, avatar `/static/img/agents/chiromant.jpg`. Greeting и suggestions также относятся только к palm workflow: проверка качества, карта видимых зон и сравнение двух чтений.

### 4.2 Каталог 17 ориентиров и дополнительных entries

`GET /api/placements` вернул HTTP 200. В каталоге присутствуют 16 западных placement entries из registry плюс `life_path`, `chinese_zodiac` и `natal_chart`, то есть **19 calculator entries**, а также отдельный palm metadata object. Canonical API identifier лунного знака — `moon_sign`; пользовательское слово `moon` намеренно не принимается.

Позитивный расчёт был выполнен запросом:

```json
{
  "placement": "moon_sign",
  "birth_date": "1990-06-15",
  "birth_time": "12:30",
  "birth_city": "Moscow"
}
```

Ответом стал HTTP 200 с `sign=Рыбы`, `degree=13.4`, `precision=exact`, `source=swiss_ephemeris` и interpretation scope `emotions, needs, safety`. Неверный code `moon` вернул HTTP 400 `неизвестный placement-калькулятор`, что подтверждает наличие validation boundary, а не неявного fallback к другому калькулятору. API contract находится в [placement router][3], а deterministic registry — в [placements core module][4].

## 5. Проверка palm pipeline на реальном изображении

### 5.1 Mocked-vision E2E

Интеграционный тест использовал настоящий JPEG-файл `tests/fixtures/palm/palm_hand.jpg` размером 2592×1728. HTTP upload прошёл через MIME validation, Pillow decode, EXIF normalization, JPEG data URL boundary, vision mock, SQLite persistence и tool execution. В тесте подтверждено, что исходные bytes не записываются в `analysis_json`, а сохраняются только SHA-256, размер, hand side, статус и нормализованный анализ.

Для созданного reading были последовательно проверены list/get/delete endpoints и все восемь самостоятельных palm tools: `check_palm_quality`, `get_palm_map`, `get_palm_reading`, `get_palm_focus`, `get_palm_reflection`, `compare_palm_readings`, `list_palm_readings` и `request_better_palm_photo`. Проверка также включает приватность: другой пользователь получает 404 на get/delete чужого reading. Полный сценарий находится в [palm integration tests][5].

### 5.2 Input validation и quality boundaries

`Content-Type: application/json` вернул HTTP 415 с инструкцией отправить JPEG, PNG или WebP. Повреждённые bytes под `image/jpeg` вернули HTTP 400. Маленький реальный JPEG ниже минимальной стороны также покрыт тестом и отклоняется до обращения к vision provider. Для нового QA пользователя после неуспешных upload attempts история оставалась пустой, поэтому provider error не создаёт частичное или неподтверждённое reading.

Нормализатор ограничивает confidence диапазоном 0–1, приводит неизвестные topic/visibility/hand-side к безопасным enum fallback values, обрезает чрезмерный текст и заменяет запрещённые medical/predictive claims. Описание и код boundary находятся в [palm vision pipeline][6].

## 6. Live LLM QA и исправление GPT-5 compatibility

Первый live upload через основной server 8080 достиг provider boundary, однако configured OpenAI-compatible вызов вернул HTTP 200 с пустым `message.content`; API корректно преобразовал это в HTTP 400 `vision-модель вернула невалидный JSON`, не сохранив reading. Диагностический probe подтвердил, что проблема была не в JPEG: прямой запрос к live catalog model `gpt-5-mini` с `max_completion_tokens` вернул валидный JSON, тогда как application path передавал GPT-5-compatible request с `max_tokens`.

Live `/models` catalog сообщил 10 доступных моделей, среди которых `gpt-5-nano`, `gpt-5-mini`, `gpt-5`, `gpt-5.5`, Claude 4.5/4.6/4.7 и Gemini 3 multimodal models; для них заявлены vision и JSON-schema capabilities. В соответствии с catalog contract в `app/core/llm.py` добавлен helper, который для `gpt-5*` использует `max_completion_tokens`, а для legacy/custom models сохраняет `max_tokens` и существующий minimum budget. Этот change применяется и к обычному streaming OpenAI path, и к vision path.

После patch добавлен regression test с fake OpenAI client: GPT-5 получает ровно `max_completion_tokens=1600`, а `max_tokens` отсутствует. Targeted suite и полный suite проходят. Повторный live upload с gpt-5-mini после patch во втором isolated QA process упёрся в upstream timeout/retry chain и завершился HTTP 502 примерно через 223 секунды; это отдельная нестабильность текущего внешнего proxy, а не silent empty-content path. Поэтому финальный статус live provider следует считать **improved and guarded, but not fully green in this sandbox session**. Mocked E2E, schema/safety boundaries и provider token contract зелёные; эксплуатационная рекомендация — включить рабочий provider fallback и наблюдать latency/error rate на deployment environment.

## 7. Тестовая матрица и воспроизводимость

| Набор | Команда | Результат |
|---|---|---:|
| Targeted OpenAI/Palm | `pytest -q tests/test_openai_compat.py tests/test_palm_integration.py` | 8 passed |
| Extended targeted | `pytest -q tests/test_openai_compat.py tests/test_palm_integration.py tests/test_placements_palm.py tests/test_miniapp_actions.py` | 21 passed |
| Full project suite | `pytest -q` | 377 passed |
| Collection count | `pytest --collect-only -q` | 377 collected |
| Diff hygiene | `git diff --check` | clean |

## 8. Итоговая оценка

Функциональная интеграция Миры выполнена как самостоятельного четвёртого агента: registry, skill allow-list, prompt identity, API, persistence, Mini App cards, palm workflow и branded avatar не зависят от Tarot agent. Extended calculators доступны через отдельный deterministic placement layer, а API корректно разделяет canonical codes, validation и result metadata.

На уровне кода и тестов состояние готово к commit/push: полный suite зелёный, GPT-5 token contract исправлен и покрыт. Единственное ограничение отчёта — текущая внешняя multimodal proxy session: после исправления неправильного token parameter один повторный live upload завершился upstream timeout. Это зафиксировано как operational limitation, а не скрыто как успешный palm reading.

## References

[1]: ../app/core/llm.py "OracleAI LLM provider and token routing"
[2]: ../tests/test_openai_compat.py "OpenAI-compatible gateway and GPT-5 vision regression tests"
[3]: ../app/api/routers/placements.py "Placement and palm API router"
[4]: ../app/core/placements.py "Deterministic placement calculator registry"
[5]: ../tests/test_palm_integration.py "Real JPEG palm integration tests"
[6]: ../app/core/palm.py "Palm vision normalization, safety and persistence boundary"
[7]: https://github.com/astartv1ai-del/oracleAI "OracleAI GitHub repository"
