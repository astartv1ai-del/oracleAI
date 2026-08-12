#!/usr/bin/env bash
# Консистентный SQLite backup с integrity check, retention и шифрованием.
#
# Примеры:
#   scripts/backup_db.sh
#   DB_PATH=/srv/oracle/data/oracle.db BACKUP_DIR=/srv/oracle/backups \
#   BACKUP_ENCRYPTION_KEY_FILE=/srv/oracle/secrets/backup.key \
#   BACKUP_REQUIRE_ENCRYPTION=1 scripts/backup_db.sh
#
# В production BACKUP_REQUIRE_ENCRYPTION=1 обязателен. Снимок пишется через
# SQLite .backup, поэтому живые writer-процессы не останавливаются. Расширение
# .db.enc означает AES-256-CBC + PBKDF2 + salt; рядом лежит SHA-256 checksum.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${DB_PATH:-$ROOT/data/oracle.db}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
KEEP="${BACKUP_KEEP:-7}"
KEY_FILE="${BACKUP_ENCRYPTION_KEY_FILE:-}"
REQUIRE_ENCRYPTION="${BACKUP_REQUIRE_ENCRYPTION:-0}"

fail() { echo "Ошибка: $*" >&2; exit 1; }

command -v sqlite3 >/dev/null 2>&1 || fail "sqlite3 не найден"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum не найден"
[ -f "$DB" ] || fail "база не найдена: $DB"
[[ "$KEEP" =~ ^[0-9]+$ ]] || fail "BACKUP_KEEP должен быть неотрицательным числом"

if [ "$REQUIRE_ENCRYPTION" = "1" ]; then
    [ -n "$KEY_FILE" ] || fail "BACKUP_ENCRYPTION_KEY_FILE обязателен при BACKUP_REQUIRE_ENCRYPTION=1"
fi
if [ -n "$KEY_FILE" ]; then
    command -v openssl >/dev/null 2>&1 || fail "openssl не найден для шифрования"
    [ -r "$KEY_FILE" ] || fail "ключ backup недоступен для чтения: $KEY_FILE"
fi

umask 077
mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
TMP="$BACKUP_DIR/.oracle-$STAMP.db.tmp"
if [ -n "$KEY_FILE" ]; then
    DEST="$BACKUP_DIR/oracle-$STAMP.db.enc"
else
    DEST="$BACKUP_DIR/oracle-$STAMP.db"
fi
CHECKSUM="$DEST.sha256"
cleanup() { rm -f "$TMP"; }
trap cleanup EXIT

# SQLite .backup — консистентный snapshot на живой WAL-базе.
echo "→ snapshot: $DB"
sqlite3 -cmd ".timeout 10000" "$DB" ".backup '$TMP'"
[ -s "$TMP" ] || fail "SQLite backup пуст"
[ "$(sqlite3 "$TMP" 'PRAGMA integrity_check;')" = "ok" ] || fail "integrity_check исходного snapshot не прошёл"

if [ -n "$KEY_FILE" ]; then
    echo "→ шифрование: $DEST"
    # Ключ читается из файла, не появляется в argv и не пишется в лог.
    openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
        -pass "file:$KEY_FILE" -in "$TMP" -out "$DEST"
else
    mv "$TMP" "$DEST"
fi

sha256sum "$DEST" > "$CHECKSUM"
chmod 600 "$DEST" "$CHECKSUM"

# Retention учитывает и зашифрованные, и legacy raw snapshots.
echo "→ уборка старых копий (оставляю $KEEP)"
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'oracle-*.db' -o -name 'oracle-*.db.enc' \) \
    -printf '%T@ %p\n' | sort -nr | tail -n +$((KEEP + 1)) | cut -d' ' -f2- |
    while IFS= read -r old; do
        [ -n "$old" ] || continue
        rm -f "$old" "$old.sha256"
        echo "  удалено: $old"
    done

echo "✓ готово: $DEST"
