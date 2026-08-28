# Backup / Restore Drill

**Дата:** 28 августа 2026

## Локальная проверка инфраструктурного контракта

Статический локальный gate запускается из корня репозитория:

```bash
python3 scripts/check_p004_infrastructure.py
make p004-audit
```

Он проверяет PostgreSQL backup image, custom-format dump, checksum sidecar, encrypted artifact contract, S3-compatible uploader, isolated restore guard, freshness/off-site monitoring и CI wiring. В текущем Compose backup profile контейнер использует `BACKUP_STORAGE_PATH`, host-mounted `BACKUP_ENCRYPTION_KEY_HOST_PATH` и redacted `backup-status.json`.

## Операционный backup и restore

Backup profile запускается только после создания host key и заполнения production secrets:

```bash
install -d -m 700 /etc/oracle
openssl rand -base64 48 > /etc/oracle/backup.key
chmod 600 /etc/oracle/backup.key

docker compose --profile backup -f infra/docker-compose.yml up -d --build backup
```

Restore выполняется только в изолированную PostgreSQL database:

```bash
make restore \
  BACKUP=/srv/oracle/backups/oracle-<timestamp>.dump.enc \
  RESTORE_TARGET_DB=oracle_restore
```

`infra/restore-postgres.sh` требует checksum verification и явное имя target database. In-place restore дополнительно требует `RESTORE_IN_PLACE=1` и `RESTORE_CONFIRM=I_UNDERSTAND_IN_PLACE_RESTORE`; без обоих флагов операция завершается отказом.

## Ограничения доказательства

Локальный static gate не сертифицирует production recovery. Перед публичным запуском необходимы реальные storage permissions, key custody, off-site bucket, retention, checksum verification, isolated-target restore, rollback rehearsal, restore-time measurement, alert routing и post-restore privacy audit. Эти шаги остаются внешним P0 gate и не заменяются unit-тестами.
