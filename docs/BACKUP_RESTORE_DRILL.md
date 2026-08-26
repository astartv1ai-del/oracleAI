# Backup and restore drill

**Дата:** 26 августа 2026

The local drill is reproducible with:

```bash
python3 scripts/check_backup_restore_drill.py
```

It creates a disposable database using the real OracleAI schema, inserts two synthetic users and report snapshots, uses Python SQLite backup/restore, runs `PRAGMA integrity_check` on both snapshots, verifies both owner records survive, and checks that report bodies remain associated with the correct owner. The latest run passed with `integrity_check=ok`, `restored_integrity_check=ok`, one report per owner and `owner_isolation=true`.

This does not certify production recovery. Before public launch, run the existing encrypted backup/restore scripts with production storage permissions, key custody, retention, checksum verification, a stopped-writer restore, rollback rehearsal, restore-time measurement, alerting and a post-restore privacy audit. Those steps require the deployment environment and are intentionally retained as external P0 gates.
