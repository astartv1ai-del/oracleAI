#!/usr/bin/env bash
# Восстановление проверенного snapshot SQLite.
# Использовать при остановленных writer-сервисах:
#   BACKUP_ENCRYPTION_KEY_FILE=/srv/oracle/secrets/backup.key \
#   scripts/restore_db.sh /srv/oracle/backups/oracle-20260813-030000.db.enc \
#   /srv/oracle/data/oracle.db
set -euo pipefail

BACKUP="${1:-}"
DEST="${2:-${DB_PATH:-data/oracle.db}}"
KEY_FILE="${BACKUP_ENCRYPTION_KEY_FILE:-}"

fail() { echo "Ошибка: $*" >&2; exit 1; }
[ -f "$BACKUP" ] || fail "backup не найден: $BACKUP"
command -v sqlite3 >/dev/null 2>&1 || fail "sqlite3 не найден"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum не найден"

if [ -f "$BACKUP.sha256" ]; then
    (cd "$(dirname "$BACKUP")" && sha256sum -c "$(basename "$BACKUP.sha256")")
fi

umask 077
mkdir -p "$(dirname "$DEST")"
TMP="$(mktemp "${DEST}.restore.XXXXXX")"
cleanup() { rm -f "$TMP"; }
trap cleanup EXIT

if [[ "$BACKUP" == *.enc ]]; then
    [ -n "$KEY_FILE" ] || fail "для .enc backup нужен BACKUP_ENCRYPTION_KEY_FILE"
    [ -r "$KEY_FILE" ] || fail "ключ backup недоступен для чтения: $KEY_FILE"
    openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
        -pass "file:$KEY_FILE" -in "$BACKUP" -out "$TMP"
else
    cp --reflink=auto "$BACKUP" "$TMP"
fi

[ "$(sqlite3 "$TMP" 'PRAGMA integrity_check;')" = "ok" ] || fail "integrity_check restore не прошёл"
if [ -f "$DEST" ]; then
    cp --reflink=auto "$DEST" "$DEST.before-restore.$(date -u +%Y%m%d-%H%M%S)"
fi
mv "$TMP" "$DEST"
echo "✓ восстановлено: $DEST"
