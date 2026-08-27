# OracleAI — scale triggers and migration rehearsal

## Current decision

OracleAI поддерживает два backend-пути: SQLite WAL для локальной разработки и обратимого rollback, PostgreSQL для production-использования с SQLAlchemy 2.0, asyncpg и Alembic. Переключение выполняется через `DATABASE_URL`; отсутствие этой переменной сохраняет SQLite fallback.

Переход не является безвозвратным: сначала создаётся read-only snapshot SQLite, затем он импортируется в изолированную PostgreSQL-базу через `scripts/migrate_sqlite_to_postgres.py`, после чего проверяются counts, health, API-контракты и rollback. `pgvector` подключается отдельным DBA/Alembic-шагом; fixed-dimension HNSW/IVFFlat индекс добавляется только после фиксации embedding-модели и размерности.

## Operational measurements

Run the read-only report against an isolated backup or production replica, never against a path uploaded by a user:

```bash
python3 scripts/db_health_report.py --db /srv/oracle/data/oracle.db
python3 scripts/migration_manifest.py --db /srv/oracle/data/oracle.db > /tmp/schema-manifest.json
```

`db_health_report.py` returns only aggregate counts and storage/schema health. It never returns diary text, messages, memory facts, birth data, Telegram IDs, payment details or raw rows. Exit codes are suitable for cron/alerting: `2` integrity failure, `3` DB size threshold, `4` WAL threshold.

## Scale trigger matrix

| Signal | Observe now | Trigger | Response |
|---|---|---|---|
| DB file | bytes, page count, freelist | >2 GiB or backup duration outside RPO | run restore drill, compact/retention review, start migration rehearsal |
| WAL file | bytes and checkpoint duration | >256 MiB for two checks or repeated growth | inspect long readers/write locks; checkpoint only in maintenance window |
| SQLite write contention | lock errors, busy timeout, request p95 | recurring `database is locked` or p95 >400 ms on non-LLM reads | isolate background writes, make jobs idempotent, load-test before schema move |
| Backup | duration, checksum, restore result | restore fails or RTO misses target | stop release, repair backup topology and repeat drill |
| API load | p50/p95, 5xx, active connections | 50 RPS baseline no longer meets error budget | capacity test, worker/queue decision, provider concurrency tuning |
| LLM | p50/p95, fallback rate, tool timeout | fallback or latency regression against scorecard | route to healthy provider, reduce context/tool budget, rollback prompt/model |
| Morning jobs | job duration and overlap | interactive requests contend with forecast jobs | separate deterministic jobs from generation worker before scaling |

A threshold is not an automatic migration command. The owner records the observation window, workload, release, user impact and rollback options in the incident/release note.

## PostgreSQL rollout sequence

1. Подготовить PostgreSQL 16+ и включить `vector` отдельным DBA-шагом.
2. Запустить `DATABASE_URL=... alembic upgrade head` в target database.
3. Создать и проверить SQLite backup; использовать только read-only snapshot.
4. Выполнить `python -m scripts.migrate_sqlite_to_postgres --sqlite ... --database-url ...`.
5. Проверить counts, `messages.thread_id IS NULL`, sequences, `pg_extension`, `alembic_version` и `/api/health`.
6. Запустить API/бот с тем же `DATABASE_URL` на staging и выполнить offline/mock chat POST.
7. При ошибке остановить запись, unset `DATABASE_URL` и вернуться к SQLite backup; не использовать destructive Alembic downgrade.

## Migration rehearsal sequence

1. Freeze the schema contract with `migration_manifest.py` and record `user_version`, object list and SHA-256.
2. Create a backup with `scripts/backup_db.sh`, verify checksum, and restore into an isolated SQLite file with `scripts/restore_db.sh`.
3. Run `PRAGMA integrity_check`, the existing migration suite and aggregate row-count checks on source and restored copies.
4. Build a disposable PostgreSQL schema from the same contract; map SQLite booleans, timestamps, JSON text and integer IDs explicitly.
5. Load a synthetic or approved anonymized fixture only. Compare table counts and deterministic checksums of non-sensitive reference tables; never export production personal text by default.
6. Exercise dual-read in staging with a feature flag, compare response contracts and latency, and keep SQLite as the authoritative rollback source.
7. Rehearse rollback: disable dual-read, return to SQLite, drain new writes safely and document the maximum acceptable loss window.
8. Promote only after a production-like load test, backup/restore drill, payment/webhook replay checks, privacy review and owner sign-off.

## Load test entry points

The existing Locust workload in `load/locustfile.py` represents 1,000 seeded readers and approximately 50 RPS. It uses `DEV_MODE=1` and synthetic `dev_user` IDs only. Do not run it against production or with real Telegram sessions.

```bash
python3 scripts/seed_load.py --count 5000
DEV_MODE=1 python -m uvicorn app.api.main:app --port 8000
locust -f load/locustfile.py --host http://127.0.0.1:8000 -u 1000 -r 25 --run-time 2m
```

The report must include release, DB/WAL sizes before and after, p50/p95/p99 per endpoint, 5xx, lock errors, backup duration and LLM calls. LLM generation is a separate workload; do not infer AI capacity from read-only API traffic.
