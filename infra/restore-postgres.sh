#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 /path/to/oracle-YYYYMMDD-HHMMSS.dump.enc" >&2
  exit 2
fi

encrypted="$1"
key_file="${BACKUP_ENCRYPTION_KEY_FILE:-/etc/oracle/backup.key}"
compose_file="${COMPOSE_FILE:-infra/docker-compose.yml}"

[[ -r "$encrypted" ]] || { echo "backup is not readable: $encrypted" >&2; exit 1; }
[[ -r "$encrypted.sha256" ]] || { echo "checksum is missing: $encrypted.sha256" >&2; exit 1; }
[[ -r "$key_file" ]] || { echo "backup key is not readable: $key_file" >&2; exit 1; }

sha256sum --check "$encrypted.sha256"
tmp="$(mktemp --suffix=.oracle.dump)"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -pass "file:${key_file}" -in "$encrypted" -out "$tmp"

# Stop writers before restoring. The operator must intentionally restart the
# application after reviewing pg_restore output.
docker compose -f "$compose_file" stop api bot worker beat
cat "$tmp" | docker compose -f "$compose_file" exec -T postgres \
  pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname="${POSTGRES_DB:-oracle}"

echo "PostgreSQL restore completed. Review the output, run 'make migrate', then start the stack."
