# Astrology visualization research

## Decision

Не добавлять новую библиотеку расчёта в текущем pass. OracleAI уже использует Kerykeion и получает через него планеты, дома, ASC, MC, аспекты и узлы. Калькуляции лучше оставить в существующем backend source of truth, а улучшить payload/interpretation/UI.

Для будущего отдельного SVG-рендера можно рассмотреть AstroDraw/AstroChart: это TypeScript/MIT библиотека генерации SVG, но она не рассчитывает положения планет, поэтому подходит только как presentation layer поверх серверных координат.

Kerykeion официально умеет natal/synastry/transit/composite charts, houses, aspects, lunar nodes и SVG rendering. Его GitHub-репозиторий указан под AGPL-3.0. Для коммерческого закрытого продукта нужно отдельно проверить текущую лицензионную стратегию до использования новых chart-rendering классов; текущий проект уже использует установленный движок, поэтому не меняем dependency без необходимости.

Swiss Ephemeris даёт высокоточную основу, но официальная страница указывает dual licensing: AGPL либо коммерческая Swiss Ephemeris Professional License. Поэтому прямое расширение зависимости без legal review нецелесообразно.

## Sources

- https://github.com/g-battaglia/kerykeion — Kerykeion capabilities, SVG chart generation, AGPL-3.0 metadata.
- https://github.com/AstroDraw/AstroChart — TypeScript SVG presentation library, MIT; explicitly does not calculate planetary positions.
- https://www.astro.com/swisseph/swephinfo_e.htm — Swiss Ephemeris precision and dual licensing.
