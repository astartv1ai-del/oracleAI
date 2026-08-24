# Аудит движка натальной карты OracleAI

## Executive conclusion

OracleAI **уже использует зрелое расчётное ядро**: `kerykeion==5.12.9`, работающее поверх Swiss Ephemeris. Поэтому переход на Kerykeion не является миграцией на другой движок — OracleAI уже находится на этом стеке. На контрольной карте OracleAI, прямой Kerykeion и прямой Swiss Ephemeris дали одинаковые долготы десяти планет и одинаковые ASC, MC и 12 Placidus куспидов до точности benchmark.

Рекомендация: **не заменять Kerykeion и не объединять два независимых production-движка**. Вместо этого оставить Kerykeion как primary calculation backend, сделать conventions явными, сохранить exact precision, добавить normalization/validation layer, а другие проекты использовать как reference engines и источники отдельных функций.

## Что проверено в OracleAI

`app/core/astro.py` выполняет следующие операции:

| Область | Текущее состояние |
|---|---|
| Эфемериды | Kerykeion/Swiss Ephemeris, offline coordinates |
| Планеты | Солнце, Луна, Меркурий, Венера, Марс, Юпитер, Сатурн, Уран, Нептун, Плутон |
| Дома | 12 домов при подтверждённых времени, координатах и timezone |
| Углы | ASC и MC при достаточной точности входных данных |
| Аспекты | Major aspects через Kerykeion `NatalAspects` |
| Дополнительные точки | Северный/Южный узлы и Лилит, если доступны в установленной версии |
| Incomplete data | `date_only`, `time_without_location`, `lite` fallback |
| Async | `compute_chart_async()` через `asyncio.to_thread()` |
| Output | UI-rounded fields плюс exact `*_exact` fields после audit patch |

До audit patch расчет не передавал явно `zodiac_type`, `houses_system_identifier` и `perspective_type`, а наследовал defaults библиотеки. Теперь OracleAI явно задаёт и возвращает:

```text
zodiac_type       = Tropical
house_system      = P (Placidus)
perspective       = Apparent Geocentric
engine             = Swiss Ephemeris via Kerykeion
```

Это небольшое, но важное изменение: при обновлении библиотеки convention не изменится молча.

## Cross-engine benchmark

Контрольная карта: `1990-06-21 14:30`, Казань, `55.79N 49.12E`, `Europe/Moscow`, tropical zodiac, Placidus.

OracleAI, Kerykeion и direct Swiss Ephemeris совпали по десяти планетам на полной precision. Flatlib был сопоставлен по его default traditional subset.

| Движок | Планетные позиции | Дома/углы | Главное ограничение |
|---|---|---|---|
| OracleAI | Совпадает с Kerykeion/Swiss | Совпадает по ASC, MC и 12 Placidus cusps | Это normalizer и product layer, не самостоятельная эфемерида |
| Kerykeion | 10 планет совпали с direct Swiss | ASC, MC и все 12 cusps: `0.0 arcsec` difference в benchmark | AGPL-3.0; conventions надо задавать явно |
| Swiss Ephemeris | Reference values | Placidus совпал с Kerykeion | Низкоуровневый API, больше кода нужно поддерживать самостоятельно |
| flatlib | В этой карте расхождение примерно `0.01–0.98 arcsec` по 7 traditional planets | Не использовался как feature-equivalent comparator | По default нет Uranus, Neptune и Pluto |

Важная деталь: прежние поля `abs_deg` округлялись до `0.1°`, из-за чего внешний benchmark мог показывать искусственное расхождение. Теперь payload сохраняет `deg_exact`, `abs_deg_exact`, `orb_exact`, `deg_exact` для домов и exact values для ASC/MC, а rounded keys остаются для UI и обратной совместимости.

Benchmark script: `scripts/benchmark_natal_engines.py`. Последний результат сохранён в `/home/ubuntu/oracleAI-natal-benchmark.json`.

## Сравнение GitHub-кандидатов

### Kerykeion

Kerykeion — текущая библиотека OracleAI. Официальные материалы описывают natal, synastry, transit, composite и return charts, SVG rendering, structured JSON, AI-ready context, house systems, aspects, sidereal modes, lunar nodes и fixed stars [1] [2]. Исходник фиксирует defaults: tropical zodiac, Placidus houses и apparent geocentric perspective.

**Решение:** оставить как primary backend. Не дублировать его другим high-level engine.

### pyswisseph

`pyswisseph` — Python extension к Swiss Ephemeris с низкоуровневыми операциями вроде Julian day conversion и planetary calculations [5]. Это хороший вариант, если OracleAI понадобится полный контроль над calculation flags, ephemeris files, sidereal modes или custom points.

Но переход на него означает самостоятельную реализацию и тестирование subject model, house normalization, aspect policy, points, timezone boundary logic и JSON contract. Он не даёт выигрыш в precision относительно текущего Kerykeion, потому что Kerykeion уже использует тот же calculation family.

**Решение:** использовать direct pyswisseph как regression oracle для benchmark, а не как замену primary layer.

### flatlib

Flatlib — Python library for Traditional Astrology с простым `Datetime`/`GeoPos`/`Chart` API [4]. Его сильная сторона — традиционная модель и удобные семантические объекты. При локальной проверке default chart содержал Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, nodes, Syzygy и Pars Fortuna, но не возвращал Uranus, Neptune и Pluto.

**Решение:** можно использовать как отдельный traditional-technique reference или future skill backend, но не объединять с Kerykeion на уровне одного chart payload без явной normalization policy.

### Immanuel

Immanuel — более высокоуровневый Python-пакет поверх Swiss Ephemeris/astro.com conventions. Он заявляет natal, solar returns, secondary progressions, composites, synastry, JSON/human-readable serialization, dignities и configurable chart settings [6]. Версия в checked-out repository — `1.5.4`, Python `>=3.10`, AGPL-3.0.

**Решение:** наиболее интересный кандидат для comparison POC по secondary progressions, dignities и готовым report models. Но он не даст независимой astronomical validation: он также опирается на Swiss Ephemeris и добавляет собственные conventions. Интегрировать только избирательно, отдельным adapter, после fixture-by-fixture diff.

### Astrolog

Astrolog 8.00 — mature standalone C/C++ astrology application с bundled ephemeris files и широким legacy/modern chart surface [7]. Он ценен как внешний reference для house systems, aspects и традиционных настроек, но не является Python backend и потребует native/process boundary.

**Решение:** использовать как reference oracle для заранее сохранённых fixtures, не как production dependency.

### sweph-wasm

`sweph-wasm` переносит Swiss Ephemeris в WebAssembly для browser/Node и заявляет offline JSON API, planets, houses, nodes, aspects и много house systems [8]. Он может быть полезен для client-side preview, но добавит второй runtime и риск различий в timezone/serialization conventions.

**Решение:** не использовать для server natal source of truth; рассмотреть только при необходимости offline frontend calculator после cross-engine fixtures.

## Licensing risk

Swiss Ephemeris официально предлагает dual licensing: AGPL либо Swiss Ephemeris Professional License. Astrodienst прямо указывает, что разработчик должен выбрать модель до распространения software или активации public service [3]. Kerykeion и pyswisseph также распространяются под AGPL-3.0 [1] [2] [5]. Immanuel также использует AGPL-3.0 [6].

Это не означает, что текущий расчёт неправильный. Это означает, что перед коммерческим closed-source SaaS нужно отдельно получить юридическую позицию: соблюдать AGPL obligations либо рассмотреть professional license/API route. Это не следует решать технической заменой Kerykeion на pyswisseph, поскольку лицензированная основа остаётся Swiss Ephemeris.

## Что стоит переработать в OracleAI

Нужна **не смена движка, а небольшая calculation contract refactor**:

1. Хранить conventions в одном `CalculationConfig`: zodiac, house system, perspective, ephemeris mode, active points и aspect policy.
2. Передавать этот config явно в Kerykeion и возвращать его в `chart.metadata`.
3. Хранить exact numeric values и rounded presentation values раздельно.
4. Добавить date-only uncertainty window для быстрых тел, прежде всего Луны: без времени рождения нельзя всегда считать знак/градус Луны абсолютно определённым.
5. Валидировать IANA timezone и координаты до запуска расчёта; invalid timezone должен быть явной ошибкой, а не тихим lite fallback.
6. Сохранить legacy payload keys и добавить versioned `chart_schema` для дальнейших клиентов.
7. Создать fixture matrix минимум для UTC offsets, DST transitions, полярных широт, границ знаков, неизвестного времени, invalid input, sidereal/tropical и всех поддерживаемых house systems.
8. Использовать direct Swiss Ephemeris и, по возможности, Immanuel/flatlib/Astrolog только как независимые reference checks для отдельных conventions.

Пункты 2, 3 и 5 уже реализованы в текущем integration spike; остальное следует выполнять отдельными небольшими PR, не смешивая с заменой движка.

## Final recommendation

**Не объединять два full chart engines в один production calculation path.** Оставить Kerykeion/Swiss Ephemeris как единственный source of truth, а архитектуру разделить на:

```text
Input validation
    ↓
CalculationConfig
    ↓
Kerykeion / Swiss Ephemeris adapter
    ↓
Canonical ChartModel with exact values + conventions
    ↓
Reference-engine regression checks
    ↓
Urania skills / interpretation / UI / PDF
```

Так OracleAI получает точность и зрелость готового engine, но сохраняет собственные сильные стороны: incomplete-data modes, safety, evidence grounding, Russian product contract и skill-first interpretation. Полная миграция на flatlib, pyswisseph или Immanuel сейчас увеличит surface area и число conventions, но не даст измеримого выигрыша по точности на natal core.

## References

[1]: https://github.com/g-battaglia/kerykeion "Kerykeion GitHub repository"

[2]: https://pypi.org/project/kerykeion/ "Kerykeion on PyPI"

[3]: https://www.astro.com/swisseph/sweph_e.htm "Swiss Ephemeris official documentation and licensing"

[4]: https://github.com/flatangle/flatlib "flatlib GitHub repository"

[5]: https://github.com/astrorigin/pyswisseph "pyswisseph GitHub repository"

[6]: https://github.com/theriftlab/immanuel-python "Immanuel Python GitHub repository"

[7]: https://github.com/CruiserOne/Astrolog "Astrolog GitHub repository"

[8]: https://github.com/astroahava/astro-sweph "astro-sweph / sweph-wasm GitHub repository"
