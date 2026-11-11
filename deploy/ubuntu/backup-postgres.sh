#!/bin/sh
# Backup diário do PostgreSQL com retenção de 30 dias. Rodado pelo siga-backup.timer.
# Teste de restauração: veja docs/OPERACAO.md.
set -eu
DESTINO=${SIGA_BACKUP_DIR:-/var/backups/siga}
mkdir -p "$DESTINO"
ARQUIVO="$DESTINO/siga-$(date +%Y%m%d-%H%M).dump"
pg_dump --format=custom --no-owner --dbname="${POSTGRES_DB:-siga_coop}" --file="$ARQUIVO"
pg_restore --list "$ARQUIVO" > /dev/null   # falha se o arquivo estiver corrompido
find "$DESTINO" -name 'siga-*.dump' -mtime +30 -delete
