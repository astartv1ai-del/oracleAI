# PostgreSQL deployment and migration runbook

## Architecture contract

OracleAI is **PostgreSQL-only**. `DATABASE_URL` is required in every environment and must use the SQLAlchemy asyncpg URL form. There is no SQLite runtime, test backend, fallback, import path or rollback path. Alembic is the sole authority for schema creation and change.

```dotenv
DATABASE_URL=postgresql+asyncpg://oracle:strong-password@postgres:5432/oracle
PGVECTOR_ENABLED=1
PG_POOL_SIZE=10
PG_MAX_OVERFLOW=10
PG_POOL_TIMEOUT=30
```

PostgreSQL 16 or newer is supported. When `PGVECTOR_ENABLED=1`, the `vector` extension must be installed by the DBA or infrastructure role before the baseline migration. The application role needs normal database/schema/table privileges; it must not need superuser privileges during normal startup.

## Clean-slate bootstrap

The project is at a local/test stage with no production data migration requirement. Build a fresh database and apply the canonical migration chain:

```bash
# Infrastructure/DBA step
psql -d oracle -c 'CREATE EXTENSION IF NOT EXISTS vector;'

# Deployment step, before API/bot/worker/Beat start
DATABASE_URL=postgresql+asyncpg://oracle:strong-password@postgres:5432/oracle \
PGVECTOR_ENABLED=1 \
alembic upgrade head
```

The current chain creates the PostgreSQL baseline, durable task-job projection and widened Telegram identifier columns. Application startup only checks that an Alembic revision exists; it does not create or alter tables.

For an isolated local/test database, use [`scripts/reset_test_database.py`](../scripts/reset_test_database.py). It drops only an explicitly named non-system PostgreSQL database, recreates it with the application role as owner, enables pgvector through the administrator connection and leaves schema creation to Alembic.

```bash
TEST_DATABASE_URL=postgresql+asyncpg://oracle_test:oracle_test@127.0.0.1:5432/oracle_test \
POSTGRES_ADMIN_DATABASE_URL=postgresql://postgres:admin-password@127.0.0.1:5432/postgres \
PGVECTOR_ENABLED=1 \
python scripts/reset_test_database.py

DATABASE_URL=postgresql+asyncpg://oracle_test:oracle_test@127.0.0.1:5432/oracle_test \
PGVECTOR_ENABLED=1 \
alembic upgrade head
```

## Schema and type decisions

The PostgreSQL baseline renders native `BIGINT` identifiers, `DOUBLE PRECISION` coordinates and numeric values, timezone-aware timestamp semantics where declared, JSONB-compatible payload fields and `vector` embeddings when enabled. Telegram identifiers are widened to avoid int32 overflow. Embedding dimension and model metadata must remain compatible; do not create a fixed-dimension vector index until the model and dimension are frozen and measured.

The baseline and follow-up revisions are:

| Revision | Responsibility |
|---|---|
| `0001_pg_baseline` | Creates the canonical PostgreSQL tables, constraints and indexes. |
| `0002_task_jobs` | Adds durable Celery task status and operational indexes. |
| `0003_widen_tg_id_to_bigint` | Widens Telegram and related identifiers safely. |

Do not edit an applied revision. Add a new Alembic revision, test it against an empty database and verify upgrade behavior before deployment.

## Verification checklist

After migration, verify the revision, tables, constraints, indexes and extension:

```sql
SELECT version_num FROM alembic_version;
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';
SELECT COUNT(*) FROM information_schema.table_constraints
 WHERE constraint_schema = 'public';
SELECT extname FROM pg_extension ORDER BY extname;
```

Then run the PostgreSQL test suite and health/smoke checks:

```bash
DATABASE_URL=postgresql+asyncpg://oracle:strong-password@postgres:5432/oracle \
PGVECTOR_ENABLED=1 \
python -m pytest tests/ -q

DATABASE_URL=postgresql+asyncpg://oracle:strong-password@postgres:5432/oracle \
PGVECTOR_ENABLED=1 \
python scripts/selfcheck.py
```

At minimum, exercise profile creation, history retrieval, chat persistence, memory consent, report history, billing idempotency, crystal spending, webhook replay and account deletion. Confirm that application logs do not include credentials, Telegram init data, raw palm images or private user content.

## Backup and recovery

Use [`infra/backup-postgres.sh`](../infra/backup-postgres.sh) for encrypted custom-format dumps and [`infra/restore-postgres.sh`](../infra/restore-postgres.sh) for checksum-verified isolated restores. A baseline downgrade is intentionally not a production rollback mechanism. If a release must be reversed, stop unsafe writes, restore a verified PostgreSQL backup or deploy a forward-compatible application revision, then re-run health and smoke checks.

## Celery and Redis rollout

Apply the full Alembic head before enabling Celery. Redis is a broker and queue aid, not the durable source of user-visible job state. Start one Beat instance and the required workers only after PostgreSQL readiness and migration success; keep `task_jobs` as the durable status projection.

## References

[1]: ../alembic/versions/0001_pg_baseline.py "PostgreSQL baseline"
[2]: ../alembic/versions/0002_task_jobs.py "Durable task jobs"
[3]: ../alembic/versions/0003_widen_tg_id_to_bigint.py "BIGINT identifier migration"
[4]: ../scripts/reset_test_database.py "Disposable PostgreSQL reset"
[5]: ../infra/backup-postgres.sh "PostgreSQL backup"
[6]: ../infra/restore-postgres.sh "PostgreSQL restore"
