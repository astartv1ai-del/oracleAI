# OracleAI — итоговый автономный аудит и выполнение

**Дата:** 26 августа 2026  
**Репозиторий:** [astartv1ai-del/oracleAI](https://github.com/astartv1ai-del/oracleAI)  
**Ветка:** `master`  
**Статус:** изменения реализованы, проверены и опубликованы в `origin/master`.

## Итог

Проект полностью изучен по приложенному master brief, исходному коду, API, Mini App, данным, тестам, CI и текущей документации. Критический найденный риск целостности исторических отчётов исправлен: старый `UNIQUE (tg_id, kind, period)` вместе с `INSERT OR REPLACE` мог удалять предыдущую версию при регенерации. Теперь отчёты сохраняются append-only, миграция переносит существующую legacy-схему без потери строк, а клиент может открыть конкретную версию по owner-scoped `report_id`.

Дополнительно исправлен date-only PDF path: при неизвестном времени рождения fallback больше не формирует placeholder-утверждения вида «Асцендент в —» или «Планеты по домам». Разделы переключаются на sign-based copy, дома/углы исключаются, а колесо заменяется явным precision notice.

## Реализованные изменения

| Область | Что сделано |
|---|---|
| История отчётов | Удалена single-row uniqueness из canonical schema; добавлена idempotent SQLite migration `2026_08_reports_append_only`; `save_report()` использует `INSERT`, возвращает ID; deterministic source и evidence limitations сохраняются в `meta_json`. |
| API | `GET /api/reports/{kind}` возвращает `report_id` и принимает owner-scoped `?report_id=`; обычный POST использует cache; `POST /api/reports/{kind}?refresh=true` создаёт новую версию и списывает entitlement только после успешной сборки. |
| Mini App | Карточки архива передают `data-report-id` и открывают выбранную immutable-версию, а не всегда последнюю. |
| PDF | RU/EN date-only narrative теперь sign-based; запрещены placeholder house/ASC claims; добавлены regression tests. |
| Документация | Добавлены product surface, backlog, baseline, domain methods, agent architecture, memory policy, PDF system, testing contract, competitor matrix и traceability matrix; обновлена навигация и changelog. |

## Проверки

| Проверка | Результат |
|---|---|
| Полный `pytest -q` | PASS |
| Targeted report/API/migration/PDF/security tests | PASS |
| `python3 -m compileall -q app scripts tests` | PASS |
| `node --check` для Mini App и admin JS | PASS |
| `ruff check app scripts tests` | PASS |
| `python3 -m scripts.selfcheck` | PASS; только ожидаемые skips live LLM и production credentials |
| `python3 -m scripts.release_gate` | PASS |
| `pip-audit -r requirements.txt` | PASS; known vulnerabilities не обнаружены |
| HTTP smoke | PASS: `/`, landing variants, privacy/terms, `/api/health`, OpenAPI и static assets вернули 200 |
| HTTP security headers | PASS: `x-frame-options`, `x-content-type-options`, `referrer-policy`, `cache-control` присутствуют |
| PDF RU/EN exact-time | A4, 9 страниц, визуально проверены |
| PDF RU/EN date-only | A4, 8 страниц; truth-state визуально и текстово проверен |
| Git state | Clean; `master` совпадает с `origin/master` |

## Опубликованные коммиты

| Commit | Назначение |
|---|---|
| `0e616fb` | `feat: preserve immutable report history` |
| `db09c43` | `fix: enforce date-only report truth state` |
| `cef2bc0` | `docs: finalize audit baseline` |

## Остаточные gates

Локальная реализация не подменяет внешнее доказательство production readiness. Перед публичным запуском остаются реальные Telegram signed-initData/device E2E, live LLM grounding/safety evaluation, sandbox/live payment settlement/refund/reconciliation, production deployment, backup/restore drill, independent astrology-calculator comparison, лицензирование Swiss Ephemeris/Kerykeion, legal/privacy review и полный screenshot-based browser/PDF golden-case matrix.

These are recorded as explicit open items in [`docs/TASKS.md`](docs/TASKS.md), not hidden behind a green local test result.

## Основные файлы доказательств

[`docs/BASELINE.md`](docs/BASELINE.md) фиксирует воспроизводимое окружение и команды. [`docs/TRACEABILITY_MATRIX.md`](docs/TRACEABILITY_MATRIX.md) связывает требования с кодом и тестами. [`docs/FULL_PRODUCT_SURFACE.md`](docs/FULL_PRODUCT_SURFACE.md) содержит карту пользовательской поверхности. [`docs/LOCAL_BROWSER_BASELINE.md`](docs/LOCAL_BROWSER_BASELINE.md) содержит browser/PDF evidence и ограничения sandbox screenshot upload.

## Источники доменного benchmark

Официальное описание Swiss Ephemeris, точности, диапазона и dual licensing находится у Astrodienst [1]. Kerykeion описывает open-source engine, structured data, SVG chart types и AGPL-3.0 [2] [3]. Сводка конкурентных product mechanics и ссылки на first-party surfaces сохранена в [`docs/COMPETITOR_MATRIX.md`](docs/COMPETITOR_MATRIX.md).

## References

[1]: https://www.astro.com/swisseph/swephinfo_e.htm "Astrodienst — Swiss Ephemeris official documentation"  
[2]: https://kerykeion.net/ "Kerykeion official product and engine description"  
[3]: https://github.com/g-battaglia/kerykeion "Kerykeion source repository and license"  
[4]: https://github.com/astartv1ai-del/oracleAI "OracleAI GitHub repository"
