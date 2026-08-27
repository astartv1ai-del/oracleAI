> STATUS: HISTORICAL
> SUPERSEDED BY: `../DOMAIN/ACCURACY_MATRIX.md and ../DOMAIN/CONTRACTS.md`
> This dated evidence is retained for audit context; it is not a current source of truth.

# P1-004: Astronomy Reference QA

**Дата прогона:** 2026-08-27  
**Статус:** local cross-implementation verification passed; independent external authority comparison remains open.

## Вывод

Для критического набора из восьми кейсов canonical OracleAI chart path и независимый direct-calculation path дали одинаковые долготы десяти планет в пределах установленного порога **0.02°**. Exact-time comparisons также дали 0.000000° для 12 Placidus cusps и ASC/MC там, где direct `houses_ex` доступен. Восемь case-level контрактов прошли: пять обычных exact-time случаев, один летний DST-кейс, историческая timezone, date-only truth state, fail-closed поведение для неоднозначного времени при переходе на зимнее время и planetary-only verification для polar edge. Для Longyearbyen прямой `houses_ex` reference path вернул upstream error, поэтому houses/ASC/MC помечены как **unverified**, а не как подтверждённые.

Эта проверка является **независимым сравнением реализаций**, но не сравнением независимых эфемеридных источников: canonical путь использует Kerykeion поверх Swiss Ephemeris, а reference path вызывает `pyswisseph.calc_ut` напрямую. Поэтому результат подтверждает согласованность адаптера, преобразования локального времени и контрактов точности, но не заменяет ручную или автоматизированную сверку с Astro.com, Astro-Seek либо другим независимым authoritative calculator.

## Методика и настройки

Harness находится в [`scripts/domain_qa.py`](../../scripts/domain_qa.py). Для каждого кейса он подаёт одинаковые дату, локальное время, timezone, широту и долготу в canonical `app.core.astro.compute_chart`, затем конвертирует локальное время в UTC через `zoneinfo` и вычисляет положения планет direct `swisseph.calc_ut` с `FLG_SWIEPH`. Сравниваются Солнце, Луна, Меркурий, Венера, Марс, Юпитер, Сатурн, Уран, Нептун и Плутон. Разность нормализуется по кругу 360°.

Для exact-time кейсов проверяются `mode=full`, `precision=exact`, наличие angular data и десять планет. Для date-only проверяется `precision=date_only`, наличие эфемеридных планет и отсутствие angular data. Для ambiguous DST local time проверяется безопасный переход в `mode=lite`/`precision=sun_only`, без попытки выдать неподтверждённые дома, ASC и MC.

```text
python3 scripts/domain_qa.py
```

## Результаты

| Case | Сценарий | Ожидаемый контракт | Результат | Максимальная разность планет |
|---|---|---|---|---:|
| `normal_exact` | Казань, точное время | full / exact / angular data | Pass | 0.000000° |
| `dst_summer` | New York, летнее время | full / exact / angular data | Pass | 0.000000° |
| `dst_fall_back_ambiguous` | New York, 01:30 в переходе DST | fail-closed lite / sun-only | Pass | N/A |
| `historical_timezone` | Berlin, 1945 | full / exact / angular data | Pass | 0.000000° |
| `unknown_time` | London, дата без времени | full / date-only / no angular data | Pass | 0.000000° |
| `edge_longitude` | Fiji, долгота около +180° | full / exact / angular data | Pass | 0.000000° |
| `high_latitude` | Longyearbyen, 78° с.ш. | Planetary exact; Placidus reference behavior explained | Pass for planets; houses/ASC/MC unverified because direct `houses_ex` errors | 0.000000° planets; N/A houses |
| `midnight_boundary` | Kiritimati, 23:59 | full / exact / angular data | Pass | 0.000000° |

Итог harness: **8/8 case-level checks pass**, `threshold_deg=0.02`, `external_vendor_comparison=open`. Дополнительное поле `unverified_comparisons` содержит `high_latitude: houses, ASC, MC`.

## Что доказано и что не доказано

Проверка подтверждает, что для выбранных входов canonical adapter не расходится с прямым вызовом того же Swiss Ephemeris kernel по десяти planetary longitudes; что exact Placidus houses/ASC/MC совпадают там, где direct `houses_ex` работает; что date-only режим не раскрывает углы; и что неоднозначное локальное время не превращается в ложную exact карту. Она также покрывает timezone conversion, историческую timezone, границы долготы, высокую широту и границу полуночи. Для polar Placidus остаётся отдельное unverified поле, так как direct reference engine завершается ошибкой.

Проверка **не** доказывает независимое согласие с другим ephemeris engine, официальную production validation, корректность каждого из 19 calculator products или визуальную корректность PDF. Она также не превращает точность эфемерид в астрологическую истинность интерпретации. P1-004 закрывается только частично: следующим внешним шагом нужен manual/public reference comparison с сохранёнными обезличенными reference values, настройками tropical/Placidus и объяснением всех различий. До этого в backlog сохраняется `External/partially open`.

## Evidence и rollback

Воспроизводимое числовое evidence создаётся stdout harness и не содержит Telegram ID, вопросы, birth-data пользователя или chart payload. Результаты CI должны храниться как redacted artifact. Если будущая версия Kerykeion, Swiss Ephemeris, timezone data или canonical contract меняет любой результат выше порога, релиз блокируется, fixture и причину изменения добавляют в review, а откат выполняется на предыдущий dependency lock и кодовый commit до повторной domain QA.
