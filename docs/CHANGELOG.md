# OracleAI — changelog

Все заметные изменения пользовательского продукта, API и эксплуатационных контрактов фиксируются здесь. Временные аудиты и машинные snapshots в changelog не перечисляются как ссылки на файлы.

## Unreleased

### Added

- Добавлены versioned JSON-контракты для полной натальной карты, synastry и transit product paths.
- Добавлены owner-scoped маршруты `POST /api/synastry` и `POST /api/transits` с явными precision-gates.
- Mini App получил отдельные journeys «Полная синастрия» и «Транзиты»; Astrologer agent получает deterministic evidence для этих путей.
- Добавлена спецификация будущих `composite_schema_version=1` и `returns_schema_version=1` без включения этих возможностей в production runtime.
- Репозиторий очищен от исторических audit snapshots, AI handoff-файлов, generated inventories и одноразовых research artifacts.

### Changed

- Полная exact natal карта сохранена как canonical path: 10 традиционных планет, 12 домов, ASC/MC, Rahu/Ketu, Lilith, Chiron/Juno/Ceres/Vesta/Pallas, мажорные аспекты и precision-aware ограничения.
- Натальный визуал остаётся в Mode P: серверный Kerykeion → transient SVG → raster PNG/WebP; raw SVG не покидает серверный render pipeline.
- Документация сокращена до текущих product, architecture, API, design, security, deployment, agent, chart-contract и launch-governance источников правды.

### Security

- Синастрия использует только owner-scoped `partner_id`; birth data не принимаются через GET URL и не появляются в публичных cache keys.
- Unknown-time natal charts не получают выдуманные дома, ASC, MC или колесо.
- Transit day snapshots явно маркируются как дневные и не выдаются за точный момент Луны.

## 2.0.0 — 2026-08-12

### Added

- Ежедневный микро-ритуал, age-gate 16+, RU/EN Mini App, opt-in memory, дневник, Tarot, Matrix, palm evidence flow, аналитика и controlled-beta documentation.

### Changed

- Mini App перестроен вокруг чата с отдельными проводниками, explicit tool actions, accessibility states и responsive dark visual system.

### Security

- Server-side privacy and memory-off boundaries, safety routing and high-stakes disclaimers стали частью общего runtime-контракта.

## Release policy

Перед каждым release необходимо обновить этот файл, соответствующие canonical docs и тесты. Public launch не считается готовым только на основании локальных тестов: остаются внешние проверки production deployment, real Telegram devices, live LLM/provider quality, privacy/legal review, payments и Kerykeion/Swiss Ephemeris licensing.
