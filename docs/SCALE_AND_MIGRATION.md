# Scale and Migration

## Current decision

OracleAI uses PostgreSQL 16+ with `pgvector` as its durable data plane. Alembic owns ordered schema changes, `app/data/session.py` owns the async connection boundary, and Redis/Celery handles asynchronous jobs in the production-like Compose topology. SQLite migration and fallback scripts are not part of the supported runtime.

The deployment contract is explicit: set `APP_ENV`, `DATABASE_URL`, `POSTGRES_PASSWORD` and `GRAFANA_ADMIN_PASSWORD` before starting Compose. The Compose file and production release gate fail closed when these values are missing or match known template credentials.

## Operational measurements

Run health and application checks against an isolated staging or production replica, never against a path uploaded by a user. The supported operational checks are:

```bash
python3 scripts/healthcheck.py
python3 scripts/check_p004_infrastructure.py
make p004-audit
```

The health and infrastructure checks must expose aggregate status only. They must not print diary text, messages, memory facts, birth data, Telegram IDs, payment details, credentials or raw rows.

## Scale trigger matrix

| Signal | Observe now | Trigger | Response |
|---|---|---|---|
| PostgreSQL | query latency, pool usage, locks, table/index growth | pool exhaustion, lock growth or read p95 above the error budget | inspect slow queries/indexes, tune pool and transaction scope, repeat load test |
| pgvector | embedding dimension, recall latency, index size | semantic recall exceeds the product latency budget | confirm model dimension, add the approved vector index, benchmark recall/latency |
| Redis/Celery | queue depth, task age, retries, worker utilization | queue age or retries exceed the SLO | scale workers, inspect idempotency and provider backoff, separate interactive and batch queues |
| Backup | duration, checksum, local/off-site status, restore result | restore fails, artifact is stale or RTO misses target | stop release, repair backup topology and repeat the isolated restore drill |
| API load | p50/p95, 5xx, active connections and rate-limit rejects | 50 RPS baseline no longer meets the error budget | capacity test, tune workers/queue, review provider concurrency |
| LLM | p50/p95, fallback rate, tool timeout and cost | latency, fallback or cost regresses against the scorecard | route to a healthy provider, reduce context/tool budget, or roll back the model/prompt |
| Morning jobs | task duration, overlap and retry rate | background work contends with interactive requests | separate deterministic jobs from generation workers and tune Celery concurrency |

A threshold is not an automatic migration command. The owner records the observation window, workload, release, user impact and rollback options in an incident or release note.

## PostgreSQL rollout sequence

1. Provision PostgreSQL 16+ and enable the `vector` extension through an approved DBA step.
2. Create a disposable or staging database and run `DATABASE_URL=... alembic upgrade head`.
3. Run `python3 scripts/check_p004_infrastructure.py` and `make p004-audit`.
4. Start one `migrate` service, then API, bot, worker and Beat from the same release image.
5. Verify `/api/health`, schema version, `pg_extension`, owner-scoped reads, queued jobs and redacted operational logs.
6. Execute the staging backup and isolated restore procedure from `docs/BACKUP_RESTORE_DRILL.md`.
7. Promote only after payment/webhook replay, real Telegram device QA, live provider evaluation, capacity evidence and owner sign-off.

Do not use destructive Alembic downgrades as an emergency rollback. Stop writes, preserve the failed release evidence, restore the approved backup into an isolated target, and follow the documented release rollback procedure.

## Migration rehearsal sequence

1. Review the new schema and migration plan; confirm that every changed table, index and constraint has an Alembic revision.
2. Apply `alembic upgrade head` to an empty PostgreSQL database and verify the expected schema.
3. Apply the same revisions to a disposable copy of the staging snapshot and compare aggregate row counts and non-sensitive reference checksums.
4. Exercise API, bot and queued-job paths against the migrated database, including owner isolation, deletion, consent, billing idempotency and retry behavior.
5. Create an encrypted custom-format backup, verify its checksum and restore into an isolated target database.
6. Measure migration time, restore time, lock behavior and query latency under a representative synthetic load.
7. If a gate fails, stop writes, preserve logs and metrics, and roll back to the prior release using the approved backup/runbook rather than a destructive schema downgrade.
8. Promote only after production-like restore, payment/webhook replay, privacy review and owner sign-off.

## Load-test entry points

The repository provides a Locust API workload and a synthetic bot-flow simulator. Both use synthetic IDs and must never run against production or real Telegram sessions.

```bash
python3 scripts/seed_load.py --count 5000
DEV_MODE=1 python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
locust -f load/locustfile.py --host http://127.0.0.1:8000 -u 1000 -r 25 --run-time 2m
python3 load/simulate.py
python3 load/simulate.py --full
```

The report must include release, PostgreSQL pool usage, p50/p95/p99 per endpoint, 5xx, rate-limit rejects, queue depth, backup duration and LLM calls. LLM generation is a separate workload; do not infer AI capacity from read-only API traffic.
