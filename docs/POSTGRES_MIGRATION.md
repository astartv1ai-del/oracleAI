# PostgreSQL migration runbook

OracleAI can now run through `DATABASE_URL` using SQLAlchemy 2.0 with the asyncpg driver. The existing SQLite path remains available when `DATABASE_URL` is empty or when tests pass an explicit SQLite path. This fallback is intentional: it permits a reversible rollout and keeps offline tooling usable.

## Recommended target

Use PostgreSQL 16 or newer with the `vector` extension enabled in the target database. The application role needs normal schema/table privileges, but installing `vector` may require a DBA or provider-specific extension step.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Set the application environment without placing credentials in source control:

```dotenv
DATABASE_URL=postgresql+asyncpg://oracle:password@postgres:5432/oracle
PGVECTOR_ENABLED=1
PG_POOL_SIZE=10
PG_MAX_OVERFLOW=10
PG_POOL_TIMEOUT=30
```

`memories.embedding` is rendered as an unbounded pgvector column for compatibility with the current SQLite BLOB representation. Before creating an HNSW index, freeze the embedding model and dimensionality, backfill only vectors with that dimension, and add a dedicated Alembic revision. Mixed dimensions must not share one fixed `vector(n)` index.

## Migration procedure

First create and verify an encrypted, restorable SQLite backup. Never run the importer against the only copy of the source database; it opens the source in read-only mode and is designed to leave it untouched, but the backup remains a deployment requirement.

Install the vector extension as DBA, run the Alembic baseline as the application role, and import the snapshot in a disposable target database:

```bash
sudo -u postgres psql -d oracle -c 'CREATE EXTENSION IF NOT EXISTS vector;'
DATABASE_URL=postgresql+asyncpg://oracle:password@postgres:5432/oracle \
  PGVECTOR_ENABLED=1 alembic upgrade head

python -m scripts.migrate_sqlite_to_postgres \
  --sqlite /srv/oracle/data/oracle.db \
  --database-url postgresql+asyncpg://oracle:password@postgres:5432/oracle \
  --batch-size 1000
```

The importer copies common columns table by table, converts the current float32 embedding BLOB format into pgvector literals, loads in batches, synchronizes serial sequences, and runs portable data backfills. It also applies the legacy `thread_id IS NULL` migration after the import. It skips the SQLite-only forecasts table rebuild because the PostgreSQL baseline already has the final key.

## Application switch

After import verification, restart bot and API with the same `DATABASE_URL`. Do not run two databases in active-write mode. The API and bot share the PostgreSQL pool-backed repository protocol; seed data is applied idempotently at startup. The production API command remains one worker unless the in-process rate-limit state is moved to a shared service.

```bash
DATABASE_URL=postgresql+asyncpg://oracle:password@postgres:5432/oracle \
  PGVECTOR_ENABLED=1 python -m app.bot.main

DATABASE_URL=postgresql+asyncpg://oracle:password@postgres:5432/oracle \
  PGVECTOR_ENABLED=1 uvicorn app.api.main:app --host 0.0.0.0 --port 8080 --workers 1
```

## Verification checklist

Run `alembic current`, the project lint, and the complete pytest suite. Then check `/api/health`, one profile GET, one chat-history GET, and one offline or mocked chat POST. Compare row counts for users, threads, messages, events, payments and memories between the source snapshot and target. Confirm that `messages.thread_id IS NULL` is zero for migrated users, except intentionally preserved orphan records if the migration policy allows them.

For vector search, verify the extension, vector column type, model name and dimension before adding HNSW or IVFFlat. Measure recall and latency on production-like data; approximate indexes trade recall for speed. Keep `pgvector` index creation in a separate controlled Alembic migration because it can consume substantial memory and build time.

## Rollback

Rollback is a configuration switch, not a destructive database downgrade. Stop writes, restore the SQLite backup if PostgreSQL verification fails, remove or unset `DATABASE_URL`, and restart the prior release. Do not use Alembic downgrade for the baseline: the baseline downgrade intentionally raises an error rather than dropping production data.

## Current local verification

The repository was verified against a local PostgreSQL 16.15 cluster with pgvector 0.6.0. The migration importer loaded an isolated 1,000-user, 2,000-thread, 70,000-message fixture, produced zero remaining NULL-thread messages, and passed API health/profile/history plus an offline chat POST. The full existing pytest suite and lint also pass; these checks are not a substitute for a production copy rehearsal.
