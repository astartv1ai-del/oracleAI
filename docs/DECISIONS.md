# OracleAI — актуальные архитектурные решения

Документ содержит только действующие решения. Исторические аудиты, браузерные snapshots, competitor research и промежуточные отчёты в репозитории не хранятся.

## ADR-001 — Единый источник астрологических расчётов

**Статус:** accepted

`app/core/astro.py` на базе закреплённого Kerykeion/Swiss Ephemeris является единственным production source of truth для натальных, synastry и transit calculations. Product contracts нормализуют результаты и явно фиксируют precision; UI и LLM не пересчитывают значения. `pyswisseph`, flatlib, Immanuel, Astrolog и другие engines могут использоваться только как внешние reference tools после отдельного review, но не как второй скрытый production path.

Натальная карта использует Tropical zodiac, Placidus `P`, Apparent Geocentric и True Node. Exact values сохраняются отдельно от округлённых UI values. Unknown-time режим не подставляет дома, ASC или MC.

## ADR-002 — Evidence-first interpretation

**Статус:** accepted

Deterministic calculation and evidence builders остаются отделены от LLM interpretation. Агент получает только факты из canonical chart/product contract, а safety, coverage и grounding checks применяются до возврата ответа. Модель не вычисляет планеты, дома, аспекты, узлы, Lilith, composite midpoints или return moments.

Memory остаётся opt-in; при выключенной памяти backend и agent runtime не передают сохранённые факты в контекст. Медицинские, юридические, финансовые гарантии и deterministic predictions запрещены.

## ADR-003 — Mode P для натального изображения

**Статус:** accepted; commercial release требует legal/licensing review

Натальный визуал строится серверно через Kerykeion `ChartDrawer` во временном SVG в памяти процесса и сразу преобразуется `resvg_py` в PNG/WebP. Raw SVG не сохраняется, не логируется, не возвращается API, не передаётся в Mini App, share flow или PDF.

Клиент получает только authenticated `GET /api/chart/image`. Birth data не помещаются в URL; raster cache использует приватные headers, ETag и HMAC-derived keys. Колесо доступно только для `precision == exact`. Доступность HTML placement list и recovery states не зависит от изображения.

## ADR-004 — Версионированные chart product contracts

**Статус:** accepted for natal/synastry/transit; composite/returns planned

Текущие product contracts описаны в [CHART_PRODUCT_CONTRACTS.md](CHART_PRODUCT_CONTRACTS.md) и capability matrix в [CHART_TYPE_CAPABILITIES.md](CHART_TYPE_CAPABILITIES.md).

- `natal_schema_version = 2` сохраняет полную exact natal карту и честные ограничения unknown-time режима.
- `synastry_schema_version = 1` принимает owner-scoped saved `partner_id`, требует две exact карты и возвращает planetary positions plus major cross-chart aspects.
- `transit_schema_version = 1` принимает explicit ISO date and optional UTC time, маркирует `day` или `instant`, возвращает geocentric transit planets and aspects to natal planets, но не создаёт transit houses или angles.
- `composite_schema_version = 1` и `returns_schema_version = 1` пока не enabled. Их входы, midpoint/search semantics, precision-gates, privacy boundaries and acceptance tests описаны в [COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md](COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md).

Первый релиз новых типов JSON-first. Изображения, PDF, share artifacts, periods/ingresses и автоматические predictions требуют отдельных решений.

## ADR-005 — Production release governance

**Статус:** accepted; public launch не подтверждён

Перед коммерческим запуском требуются внешние проверки, которые нельзя закрыть локальным unit suite: production deployment and Docker image validation, real Telegram iOS/Android device QA, live LLM/provider quality, privacy/legal review, payment/reconciliation testing, backup/restore drill and licensing decision for Kerykeion AGPL-3.0 and Swiss Ephemeris dual licensing.

До закрытия этих gates продукт считается controlled-beta candidate, а не public-launch-ready.

## References

[1]: https://kerykeion.net/content/docs "Kerykeion official documentation"
[2]: https://github.com/g-battaglia/kerykeion "Kerykeion source repository"
[3]: https://www.astro.com/swisseph/ "Swiss Ephemeris licensing"
[4]: ../app/core/astro.py "OracleAI canonical calculations"
[5]: ../app/core/chart_rendering.py "OracleAI Mode P raster adapter"
[6]: CHART_PRODUCT_CONTRACTS.md "OracleAI current chart product contracts"
[7]: COMPOSITE_AND_RETURNS_PRODUCT_SPEC.md "OracleAI planned composite and returns specification"
