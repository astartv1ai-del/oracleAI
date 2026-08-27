#!/usr/bin/env bash
set -Eeuo pipefail

: "${BACKUP_ENCRYPTION_KEY_FILE:?BACKUP_ENCRYPTION_KEY_FILE is required}"
: "${BACKUP_KEEP:=14}"

if [[ ! -r "$BACKUP_ENCRYPTION_KEY_FILE" ]]; then
  echo "backup key is missing or unreadable: $BACKUP_ENCRYPTION_KEY_FILE" >&2
  exit 1
fi

mkdir -p /backups

while true; do
  ts="$(date -u +%Y%m%d-%H%M%S)"
  tmp="/backups/.oracle-${ts}.dump.tmp"
  encrypted="/backups/oracle-${ts}.dump.enc"

  if pg_dump --format=custom --no-owner --no-privileges --file="$tmp"; then
    # A custom-format dump can be listed without restoring it. This catches
    # truncated/corrupt output before encryption and retention are applied.
    pg_restore --list "$tmp" >/dev/null
    openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
      -pass "file:${BACKUP_ENCRYPTION_KEY_FILE}" \
      -in "$tmp" -out "$encrypted"
    rm -f "$tmp"
    sha256sum "$encrypted" > "${encrypted}.sha256"
    echo "encrypted PostgreSQL backup created: $(basename "$encrypted")"
  else
    echo "pg_dump failed; retaining previous backups" >&2
    rm -f "$tmp"
  fi

  find /backups -maxdepth 1 -type f -name 'oracle-*.dump.enc' \
    -mtime +"$BACKUP_KEEP" -delete
  find /backups -maxdepth 1 -type f -name 'oracle-*.dump.enc.sha256' \
    -mtime +"$BACKUP_KEEP" -delete
  sleep 86400
done
