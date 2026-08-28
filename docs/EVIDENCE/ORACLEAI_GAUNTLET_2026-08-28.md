# OracleAI: итог выполнения производственного плана

**Дата аудита:** 28 августа 2026 года. **Репозиторий:** `astartv1ai-del/oracleAI`. **Ветка:** `master`. **Исходный commit:** `a4a7e5b1e363b77d733f8e54e4a411ef76aa025a`.

## Итоговый вердикт

План выполнен в локальном disposable-контуре, а затем проведён независимый второй проход: код изучен повторно, скрытый риск в deployment defaults найден и исправлен, регрессионные тесты добавлены, а backend, AI/domain, Mini App, billing, jobs, observability, безопасность, backup/restore, dependency hygiene и release gates повторно проверены. **Локальная реализация готова к дальнейшему staging-прогону, но публичный запуск по-прежнему заблокирован внешними подтверждениями.** Это соответствует текущему `docs/RELEASE/CURRENT_STATUS.md`: зелёные локальные тесты не заменяют реальную Telegram-сессию, sandbox-платежи, live LLM-проверку, production-like restore и ручную device QA.

> Результат следует читать как `IMPLEMENTED WITH LIMITATIONS`, а не как production certification.

## Что исправлено

| Область | Изменение | Проверка |
|---|---|---|
| Жизненный цикл аккаунта | Удалённая учётная запись теперь отклоняется на обычных authenticated surfaces с HTTP `410` и не может повторно включить age, memory, push или изменить профиль. Подтверждённое повторное удаление сохраняет идемпотентность. | API-регрессии в `tests/test_api.py`; обновлены `docs/API.md` и `docs/SECURITY.md`. |
| Миграции данных | При ошибке именованной data migration выполняется `rollback()` до продолжения старта. Частичный DML больше не может попасть в последующий несвязанный `commit()`. | Новый тест `test_failed_data_migration_rolls_back_partial_writes` в `tests/test_migrations.py`. |
| Visual QA fixture | Синтетический пользователь visual QA получает явный `sub_until` на 30 дней. Это устраняет ложный `402 Payment Required` в платном домашнем сценарии. | `scripts/seed_visual_user.py`; прямой API smoke для `/api/today` вернул `200`. |
| Selfcheck | VIP limit smoke больше не зависит от переменного `AUTO_TRIAL`: fixture явно получает будущую дату окончания подписки. | `scripts/selfcheck.py`; повторный selfcheck завершился без ошибок, с двумя ожидаемыми предупреждениями об offline/live-конфигурации. |
| Lint | В intentional `sys.path` bootstrap добавлен точечный `# noqa: E402`, чтобы документированный startup checker проходил Ruff. | `ruff check app scripts tests` — pass. |
| Production deployment defaults | Compose больше не подставляет `dev`, `oracle`, `change-me` или иные известные значения для критичных настроек. Обязательны `APP_ENV`, PostgreSQL `DATABASE_URL`, `POSTGRES_PASSWORD` и `GRAFANA_ADMIN_PASSWORD`; release gate также отклоняет небезопасные шаблоны. | Новый `test_compose_requires_non_default_credentials`; `check_p004_infrastructure.py` расширен до 40 проверок; `tests/test_release_gate.py` обновлён. Docker CLI в sandbox отсутствует, поэтому проверка `docker compose config` выполнена статическим контрактом, а не запуском Docker. |

## Проверенная матрица

| Контур | Результат | Доказательство |
|---|---:|---|
| Полный Python suite | **PASS** | `python3 -m pytest -q -p no:cacheprovider` дошёл до `100%`; один тест пропущен по объявленному условию окружения. |
| Backend/API/database/billing | **PASS** | Таргетированные API, resilience, migrations, data, billing, payment monitor, P1/P2 tests прошли. |
| Security/adversarial | **PASS** | Security regressions, safety guardrails, API resilience, limits, flood, provider compatibility, engine paths и architecture boundaries прошли. |
| AI, memory, domain, palm/CV | **PASS WITH ACCURACY GATE** | Контрактные и интеграционные проверки прошли. Semantic palm accuracy не подписана: нет adjudicated golden manifest и human-review report. |
| Frontend static contracts | **PASS** | Build, JS syntax, provenance, static asset references, cache busting, design contract и visual contrast прошли. |
| Axe accessibility | **PASS** | 10 состояний Mini App, 0 axe violations. |
| Lighthouse | **PARTIAL** | Accessibility `100` и SEO `100` наблюдались на audited states. Best-practices score нельзя считать окончательно сертифицированным: в комбинированном запуске axe + Lighthouse общий rate-limit bucket дал один `429`; матрицы нужно запускать на независимых свежих процессах. |
| Bot, Telegram UX, billing, jobs, notifications, observability | **PASS** | Тесты FSM, Mini App actions, notifications, broadcast, log stream, analytics, payment monitor и growth прошли. |
| Backup/restore | **PASS WITH EXTERNAL LIMITATIONS** | Disposable local drill подтвердил integrity и owner isolation. Production key custody, off-site permissions и rollback rehearsal не выполнялись. |
| Release gates | **PASS** | `release_gate.py`, `check_p2_quality.py`, `check_p004_infrastructure.py` (40 checks), documentation links, compileall, Ruff и diff hygiene прошли. |
| Dependency hygiene | **PASS** | `npm audit --omit=dev --audit-level=high` сообщил `0 vulnerabilities`; JS syntax и Python compilation прошли. |

## Производительность

Ниже приведены **локальные направляющие измерения на синтетических данных**, а не production SLO. Для метрик с менее чем 20 запусками p95/p99 нельзя использовать как статистически устойчивую гарантию.

| Метрика | Runs | p50 | Комментарий |
|---|---:|---:|---|
| Chart compute | 5 | 2.52 ms | p95 направляющий, выборка мала. |
| Tarot draw | 20 | 0.06 ms | Направляющее сравнение допустимо. |
| Memory recall | 5 | 0.00 ms | p95 направляющий, выборка мала. |
| PDF/HTML generation | 20 | 739.41 ms | Направляющее сравнение допустимо. |
| Palm line segmentation | 3 | 15,140.05 ms | Тяжёлая CV-операция; необходим staging-профиль и решение по UX/очередям. |

Использованный palm engine — `palm_line_student_fp16.onnx`; raw mask не сохраняется. Контрактный gate считает отсутствие подтверждённых линий безопасным состоянием, но **semantic accuracy** требует независимой разметки и adjudication.

## Оставшиеся блокеры перед публичным запуском

**Telegram и onboarding.** Нужны настоящие подписанные `initData`, device/WebView journey, tampered/invalid cases, age-gate и owner-isolation evidence.

**Платежи.** Нужны sandbox invoice, duplicate webhook, refund, chargeback/error и reconciliation evidence с реальным PSP.

**Live AI.** Нужны approved provider, language/safety/grounding evaluation, latency/cost measurement и подтверждённый fallback при provider failure.

**Operations.** Нужны production-like encrypted off-site backup, проверка storage permissions, migration/rollback rehearsal, alert routing и capacity ceiling.

**External/domain gates.** Нужны независимое сравнение astrology calculations, licensing confirmation, а также ручная проверка accessibility на целевых устройствах: keyboard, screen reader, safe-area, touch targets и reduced motion.

## Воспроизведение

Все команды запускаются из корня репозитория. Для локального offline-прогона:

```bash
export APP_ENV=dev DEV_MODE=1 LLM_PROVIDER=off SELF_CHECK_LIVE=0 EMBED_MODEL=''
npm run build:frontend
python3 scripts/selfcheck.py
python3 scripts/release_gate.py
python3 scripts/check_p2_quality.py
python3 scripts/check_p004_infrastructure.py
python3 scripts/check_backup_restore_drill.py
python3 -m pytest -q -p no:cacheprovider
ruff check app scripts tests
python3 scripts/check_documentation_links.py
```

Для accessibility matrix требуется отдельный свежий сервер и disposable DB; axe и Lighthouse не следует смешивать в одном rate-limit bucket. Синтетический visual user создаётся так:

```bash
python3 scripts/seed_visual_user.py --db /tmp/oracleai-qa.db
```

Итоговый machine-readable результат находится в [`ORACLEAI_GAUNTLET_RESULT_2026-08-28.json`](ORACLEAI_GAUNTLET_RESULT_2026-08-28.json). Канонические контракты — [`API.md`](../API.md) и [`SECURITY.md`](../SECURITY.md); текущий release status — [`RELEASE/CURRENT_STATUS.md`](../RELEASE/CURRENT_STATUS.md).

## Рабочее дерево

После второго независимого прохода изменено 16 исходных, конфигурационных, тестовых и документирующих файлов; два итоговых evidence-файла также входят в рабочее дерево. Отчёт и machine-readable summary подготовлены для включения в комит; commit/push выполняются следующим шагом этого задания.
