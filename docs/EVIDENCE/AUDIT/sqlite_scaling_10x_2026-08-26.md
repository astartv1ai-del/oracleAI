# SQLite scaling review: 10× user growth

## Scope

This change set hardens the existing single-file SQLite deployment for approximately 10× growth in users and event/message volume. It does not claim that SQLite becomes a horizontally scalable multi-writer database; it reduces avoidable read scans, shortens maintenance write locks, and makes operational tuning explicit.

## Implemented improvements

| Area | Implementation | Benefit |
|---|---|---|
| Chat history | Indexes for `(tg_id, id)`, `(tg_id, thread_id, id)` and `(tg_id, is_question, id)` | Fast bounded history, legacy audit and last-question lookup. |
| Thread listing | Indexes for `(tg_id, agent, archived, id)` and expression `(tg_id, archived, COALESCE(last_at, created_at), id)` | Removes repeated sort work in active thread and per-agent lookup. |
| Analytics | Indexes for event milestones, event time/name, payment status/time, paid orders, acquisition source and promo cleanup | Reduces dashboard and cohort scans as event volume grows. |
| Memory | `(tg_id, weight DESC, id DESC)` | Matches ranking query used for prompt context. |
| Retention | `prune_analytics()` deletes `events` and `llm_usage` in 5,000-row batches by default | Shorter writer lock and resumable cleanup behavior. |
| SQLite lifecycle | `PRAGMA optimize` on connect; configurable busy timeout, WAL checkpoint and cache size | Better planner freshness and deployment-specific tuning. |
| Configuration | `SQLITE_BUSY_TIMEOUT_MS`, `SQLITE_WAL_AUTOCHECKPOINT`, `SQLITE_CACHE_SIZE_KB` in `.env.example` | Operators can tune without code changes. |

## Validation

The complete test suite and lint passed after the changes. The data tests also verify that batch pruning removes old rows in multiple small batches, preserves new rows and rejects an invalid batch size.

A штатный `scripts.seed_load` run created an isolated database with 10,000 users. `db_health_report` returned `integrity_check=ok`, `journal_mode=wal`, 10,000 users, zero freelist pages and a 4.8 MiB database. The schema manifest confirmed all new indexes were created by the normal `connect()` lifecycle.

The 10,000-user fixture contains no messages or events, so it validates startup/schema scale rather than end-to-end message throughput. Query-level performance must still be measured against production-like message/event volume before rollout.

## Operational boundary

At 10× growth, SQLite remains appropriate only while write concurrency and database size stay within the deployment's operational envelope. WAL permits readers alongside a writer, but SQLite still serializes writes. If sustained concurrent writes, cross-process queueing, or backup/restore windows become a bottleneck, the next architectural step is moving high-volume event/LLM logs and possibly the transactional domain to PostgreSQL, while retaining the same repository contracts.

Before production rollout, operators should back up the DB, run the schema/migration lifecycle on a protected copy, run `PRAGMA integrity_check`, compare `EXPLAIN QUERY PLAN` for the real workload, and monitor WAL size, busy timeouts, write latency and database growth.

## Files

- `app/data/schema.py` — new indexes.
- `app/data/session.py` — tunable SQLite PRAGMAs and `PRAGMA optimize`.
- `app/repo/analytics.py` — batch retention cleanup.
- `tests/test_data.py` — index and pruning contracts.
- `.env.example` — operator settings.
