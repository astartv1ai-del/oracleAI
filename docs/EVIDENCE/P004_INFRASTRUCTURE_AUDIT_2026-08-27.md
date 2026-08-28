> STATUS: HISTORICAL
> SUPERSEDED BY: `../RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md and ../OPERATIONS.md`
> This dated evidence is retained for audit context; it is not a current source of truth.

# P0-004 Infrastructure Readiness Audit

**Дата:** 2026-08-27
**Ветка:** `p0-004-infrastructure`
**Кандидат base:** актуальный `origin/master` (`6729ebf` на момент создания ветки)
**Scope:** encrypted PostgreSQL backup, off-site copy, isolated restore, monitoring, rollback ergonomics and CI wiring.

## Executive verdict

**Local implementation: PASS for static and disposable checks. Production-like execution: EXTERNAL GATE.**

The sandbox does not have Docker, a PostgreSQL server, an S3-compatible bucket, production-like storage, host key custody or a deployment target. Therefore this audit does not claim a real encrypted PostgreSQL restore or off-site delivery. It closes the repository-level gaps that can be closed without those resources and leaves the operational evidence requirements explicit.

## Initial findings

| Area | Initial state | Risk |
|---|---|---|
| Backup artifact | Encrypted custom-format dump and checksum existed | Local artifact alone did not prove off-site recoverability |
| Off-site copy | Production env exposed `BACKUP_S3_*`, but helper never uploaded artifacts | A successful local dump could be mistaken for a recoverable backup |
| Monitoring | `ops_alerts.py` watched SQLite `.db` patterns only | PostgreSQL backup freshness and off-site failure could remain invisible |
| Restore safety | Helper restored directly into the configured live database | Operator error could overwrite the source before isolated validation |
| CI | No P0-004-specific static gate or backup drill | Future infrastructure regressions could pass CI unnoticed |
| Operator UX | Makefile had backup target but no restore/drill/audit targets | Manual commands increased recovery error surface |
| Runtime availability | Docker CLI absent in sandbox | Compose build, PostgreSQL dump, S3 upload and restore could not be executed here |

## Implemented repository changes

| Change | Implementation | Result |
|---|---|---|
| Dedicated backup image | `infra/backup.Dockerfile` installs PostgreSQL client, OpenSSL and `python3-boto3` | Backup helper has the runtime needed for S3-compatible upload without enlarging the app image |
| Off-site uploader | `scripts/upload_s3_backup.py` uploads encrypted dump and `.sha256` sidecar via boto3; credentials stay in environment and errors are type-only | No off-site configuration is silently treated as success when policy requires it |
| Fail-closed backup policy | `BACKUP_REQUIRE_OFFSITE=1` requires complete S3-compatible config; `BACKUP_REQUIRE_ENCRYPTION` must remain `1` | Production template cannot run an unencrypted or local-only backup successfully |
| Backup status | `backup-status.json` records only UTC attempt, local success and off-site booleans | Monitoring can distinguish stale, local failure and off-site failure without sensitive payloads |
| Explicit storage | `BACKUP_STORAGE_PATH` is host-mounted; local default is `./backups`, production example uses `/srv/oracle/backups` | Operator can inspect, checksum, copy and restore artifacts without opaque volume access |
| Restore guard | `RESTORE_TARGET_DB` is mandatory; identifiers are constrained; live DB restore requires `RESTORE_IN_PLACE=1` plus `RESTORE_CONFIRM=I_UNDERSTAND_IN_PLACE_RESTORE` | Isolated restore is the default and accidental in-place restore is rejected |
| Monitoring | `ops_alerts.py` includes `oracle-*.dump.enc`, validates status JSON and emits `backup_offsite_unavailable`/`backup_job_failed` | PostgreSQL backup path is visible to operations checks |
| CI gate | CI runs static P0-004 contract, shell syntax and disposable backup/restore drill | Repository-level drift is caught before release candidate promotion |
| Operator commands | `make p004-audit`, `make backup`, `make restore`, `make backup-drill` | Repeatable operational entry points are documented |

## Local evidence

| Check | Result |
|---|---|
| `python3 scripts/check_p004_infrastructure.py` | PASS — 36 contract checks |
| `bash -n infra/backup-postgres.sh infra/restore-postgres.sh` | PASS |
| Python compile for uploader and static checker | PASS |
| `python3 scripts/reset_test_database.py` + `alembic upgrade head` | PASS — disposable PostgreSQL rebuild; production restore remains external |
| `pytest -q tests/test_stage0_operations.py` | PASS — 6 tests, including PostgreSQL dump freshness and off-site failure alert |
| Full repository QA | PASS — full pytest, compileall, Ruff, JavaScript syntax, frontend build/reference checks, P0-004 checker, PostgreSQL rebuild, release gate and diff hygiene |
| Docker/Compose availability | NOT AVAILABLE in sandbox (`docker: command not found`) |
| Real PostgreSQL encrypted dump/restore | NOT RUN — requires Docker/PostgreSQL and isolated target |
| Real S3-compatible upload | NOT RUN — requires staging endpoint, bucket and credentials |
| Production backup/restore and rollback | NOT RUN — requires VPS/storage/key custody and approved maintenance window |

## Staging execution checklist

1. Provision an isolated VPS or production-like host with Docker Engine and Compose v2, HTTPS, a staging domain, staging PostgreSQL/Redis, a staging-only `.env` and an encrypted off-site bucket.
2. Create `/etc/oracle/backup.key` with mode `0600`; create `/srv/oracle/backups` with ownership and permissions appropriate for the backup container. Store the off-site endpoint/access key/secret/bucket in the staging secret store, never in Git.
3. Checkout the candidate branch commit and run `make config`, `make p004-audit`, `make up`, `make migrate`, `make selfcheck` and `make backup`.
4. Confirm `oracle-*.dump.enc`, the checksum sidecar, `backup-status.json` with `local_backup_ok=true` and `offsite_ok=true`, and the corresponding object/checksum in the off-site bucket.
5. Use `make restore BACKUP=/srv/oracle/backups/oracle-<timestamp>.dump.enc RESTORE_TARGET_DB=oracle_restore` to restore into a fresh database. Run `pg_restore --list`, schema checks, foreign-key checks, owner-isolation checks, report-history checks and deletion/anonymization checks before connecting application writers.
6. Rehearse migration from the restored target and rollback to the previous schema-compatible release. Measure backup age, restore duration, RPO and RTO against thresholds approved by SRE/Product.
7. For an emergency in-place restore only, use both explicit confirmations: `RESTORE_IN_PLACE=1 RESTORE_CONFIRM=I_UNDERSTAND_IN_PLACE_RESTORE`. Preserve a forensic copy first and stop writer services before the restore.

## Remaining external acceptance gates

| Gate | Required evidence | Owner |
|---|---|---|
| Host and storage | Docker/Compose, permissions, encrypted host key, isolated staging DB and host-mounted backup path | SRE |
| Off-site durability | Real encrypted bucket object, checksum match, retention and restore from off-site copy | SRE |
| Restore integrity | Fresh target starts, `pg_restore` succeeds, schema/FK/owner/deletion checks pass | SRE + Security |
| Rollback | Previous release starts against compatible schema and serves health/read-only smoke | Release + SRE |
| RPO/RTO | Approved thresholds met and recorded with UTC timings | Product + SRE |
| Privacy | Redacted manifest/logs contain no birth payloads, diary/memory, palm images, tokens or payment secrets | Security + Legal |

## References

[1]: [P0 production execution plan](../RELEASE/P0_PRODUCTION_EXECUTION_PLAN.md) — gate order, acceptance, evidence and rollback.
[2]: [Deployment runbook](../DEPLOYMENT.md) — Compose topology, backup profile and restore operations.
[3]: [Backup/restore drill](../BACKUP_RESTORE_DRILL.md) — disposable local evidence and explicit production limitations.
[4]: [PostgreSQL `pg_dump` docs](https://www.postgresql.org/docs/current/app-pgdump.html) — archive formats and restore relationship.
[5]: [PostgreSQL `pg_restore` docs](https://www.postgresql.org/docs/current/app-pgrestore.html) — restoration of non-plain-text archives.
