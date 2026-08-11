#!/usr/bin/env bash
# Бэкап SQLite-базы «Оракула» (по умолчанию data/oracle.db, режим WAL).
#
# Что делает:
#   1. PRAGMA wal_checkpoint(TRUNCATE) — вливает WAL-журнал в основную базу и
#      ужимает его. Без этого снимок был бы неполным: свежие транзакции живут
#      ещё в отдельном файле -wal.
#   2. sqlite3 .backup — консистентная копия через API бэкапа SQLite. Снимок
#      самодостаточен (читается без WAL-файлов) и безопасен на живом сервере:
#      бот и API продолжают писать в базу во время бэкапа.
#   3. PRAGMA integrity_check свежей копии — битый снимок удаляется.
#   4. Retention: храним BACKUP_KEEP последних копий, старые удаляем.
#
# Использование:
#   scripts/backup_db.sh
#   DB_PATH=/srv/oracle/data/oracle.db BACKUP_DIR=/srv/oracle/backups BACKUP_KEEP=14 \
#       scripts/backup_db.sh
#
# Cron (ежедневно в 03:00; DB_PATH/BACKUP_DIR задайте выше как export):
#   0 3 * * * /srv/oracle/scripts/backup_db.sh >> /var/log/oracle-backup.log 2>&1
#
# Восстановление: остановить бот и API, затем
#   sqlite3 /srv/oracle/data/oracle.db ".restore '/srv/oracle/backups/oracle-<дата>.db'"
# (или просто заменить файл и удалить -wal/-shm рядом).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${DB_PATH:-$ROOT/data/oracle.db}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
KEEP="${BACKUP_KEEP:-7}"

if ! command -v sqlite3 >/dev/null 2>&1; then
    echo "Ошибка: sqlite3 не найден — поставь его (apt install sqlite3)" >&2
    exit 1
fi
if [ ! -f "$DB" ]; then
    echo "Ошибка: база не найдена: $DB" >&2
    exit 1
fi
[ "${KEEP:-0}" -ge 0 ] 2>/dev/null || { echo "Ошибка: BACKUP_KEEP=$KEEP" >&2; exit 1; }

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_DIR/oracle-$STAMP.db"

echo "→ checkpoint WAL: $DB"
sqlite3 -cmd ".timeout 10000" "$DB" "PRAGMA wal_checkpoint(TRUNCATE);" >/dev/null

echo "→ копия: $DEST"
sqlite3 -cmd ".timeout 10000" "$DB" ".backup '$DEST'"

if [ "$(sqlite3 "$DEST" 'PRAGMA integrity_check;')" != "ok" ]; then
    echo "Ошибка: integrity_check копии не прошёл, удаляю: $DEST" >&2
    rm -f "$DEST"
    exit 1
fi

echo "→ уборка старых копий (оставляю $KEEP)"
ls -1t "$BACKUP_DIR"/oracle-*.db 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r old; do
    rm -f "$old"
    echo "  удалено: $old"
done

echo "✓ готово: $DEST"
