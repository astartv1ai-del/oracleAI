# OracleAI — changelog

Все заметные изменения пользовательского продукта, API и эксплуатационных контрактов фиксируются здесь. Временные аудиты и машинные snapshots в changelog не перечисляются как ссылки на файлы.

## Unreleased

### Added

- Добавлены versioned JSON-контракты для natal, synastry, transit, composite и solar returns product paths.
- Добавлены owner-scoped маршруты `POST /api/synastry`, `POST /api/transits`, `POST /api/composite` и `POST /api/returns` с явными precision-gates.
- Mini App получил отдельные journeys «Полная синастрия», «Транзиты», «Композит пары» и «Солнечный возврат»; Astrologer agent получает deterministic evidence для всех путей.
- Реализованы circular midpoints для composite и bounded UTC ephemeris search с локальным timestamp для solar return; extended planets, houses, wheels and prediction semantics остаются отдельными gates.
- Репозиторий очищен от исторических audit snapshots, AI handoff-файлов, generated inventories и одноразовых research artifacts.
- Добавлены `FULL_PRODUCT_SURFACE.md`, `TASKS.md`, `BASELINE.md`, `DOMAIN_METHODS.md`, `AGENT_ARCHITECTURE.md`, `MEMORY.md`, `PDF_SYSTEM.md`, `TESTING.md`, `COMPETITOR_MATRIX.md` и `TRACEABILITY_MATRIX.md` как рабочие контракты завершения.
- Добавлен owner-scoped `GET /api/history`: единый мета-архив отчётов, Tarot, palm readings и chat sessions с actionable deep links без выдачи содержимого личных записей.
- Список памяти теперь отдаёт только inspectable поля; embedding BLOB и имя embedding-модели остаются внутренними. Recall-cache сбрасывается после ручного/AI сохранения, усиления и удаления факта.
- Tarot finalization повторно проверяет владельца и не позволяет перезаписать уже сохранённую интерпретацию; malformed upload size headers для palm получают явный 400.


### Changed

- Полная exact natal карта сохранена как canonical path: 10 традиционных планет, 12 домов, ASC/MC, Rahu/Ketu, Lilith, Chiron/Juno/Ceres/Vesta/Pallas, мажорные аспекты и precision-aware ограничения.
- Натальный визуал остаётся в Mode P: серверный Kerykeion → transient SVG → raster PNG/WebP; raw SVG не покидает серверный render pipeline.
- Документация сокращена до текущих product, architecture, API, design, security, deployment, agent, chart-contract и launch-governance источников правды.

### Security

- Синастрия использует только owner-scoped `partner_id`; birth data не принимаются через GET URL и не появляются в публичных cache keys.
- Unknown-time natal charts не получают выдуманные дома, ASC, MC или колесо.
- Transit day snapshots явно маркируются как дневные и не выдаются за точный момент Луны.
- Отчёты переведены на append-only history: `?refresh=true` создаёт новую версию и сохраняет deterministic source/evidence limitations, не удаляя предыдущую.
- Repository hygiene больше не ошибочно блокирует активную `TRACEABILITY_MATRIX.md`; проверка отделяет рабочие контракты от одноразовых audit dumps.

## 2.0.0 — 2026-08-12

### Added

- Ежедневный микро-ритуал, age-gate 16+, RU/EN Mini App, opt-in memory, дневник, Tarot, Matrix, palm evidence flow, аналитика и controlled-beta documentation.

### Changed

- Mini App перестроен вокруг чата с отдельными проводниками, explicit tool actions, accessibility states и responsive dark visual system.

### Security

- Server-side privacy and memory-off boundaries, safety routing and high-stakes disclaimers стали частью общего runtime-контракта.

## Release policy

Перед каждым release необходимо обновить этот файл, соответствующие canonical docs и тесты. Public launch не считается готовым только на основании локальных тестов: остаются внешние проверки production deployment, real Telegram devices, live LLM/provider quality, privacy/legal review, payments и Kerykeion/Swiss Ephemeris licensing.
