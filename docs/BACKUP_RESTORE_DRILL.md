# Backup and restore drill

**Дата:** 26 августа 2026

The local drill is reproducible with:

```bash
python3 scripts/check_backup_restore_drill.py
```

It creates a disposable database using the real OracleAI schema, inserts two synthetic users and report snapshots, uses Python SQLite backup/restore, runs `PRAGMA integrity_check` on both snapshots, verifies both owner records survive, and checks that report bodies remain associated with the correct owner. The latest run passed with `integrity_check=ok`, `restored_integrity_check=ok`, one report per owner and `owner_isolation=true`.

The local drill does not certify production recovery. The repository now also exposes `make p004-audit`, which statically verifies the Compose backup profile, encrypted PostgreSQL dump/checksum contract, S3-compatible uploader, isolated restore guard, PostgreSQL freshness alert and CI wiring. The backup profile writes to the explicit `BACKUP_STORAGE_PATH`, records a redacted `backup-status.json`, requires `BACKUP_REQUIRE_OFFSITE=1` in the production template and retains the encrypted local artifact when off-site upload fails.

Before public launch, run the encrypted backup/restore scripts with production storage permissions, key custody, a real off-site bucket, retention, checksum verification, an isolated-target restore, rollback rehearsal, restore-time measurement, alerting and a post-restore privacy audit. Those steps require the deployment environment and remain external P0 gates.
