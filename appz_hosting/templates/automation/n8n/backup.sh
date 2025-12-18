#!/bin/bash
# n8n backup script - tested and verified
# Called with: SERVICE_ID, DATA_PATH, BACKUP_PATH

set -e

echo "Backing up n8n: ${SERVICE_ID}"

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# Dump PostgreSQL database
echo "Dumping database..."
docker exec ${SERVICE_ID}-db pg_dump -U n8n n8n > "${BACKUP_PATH}/database.sql"

# Compress database dump
gzip "${BACKUP_PATH}/database.sql"

# Backup n8n data directory
echo "Backing up n8n data..."
tar -czf "${BACKUP_PATH}/n8n-data.tar.gz" -C "${DATA_PATH}" n8n

# Create manifest
cat > "${BACKUP_PATH}/manifest.json" << EOF
{
    "service_id": "${SERVICE_ID}",
    "template": "n8n",
    "timestamp": "$(date -Iseconds)",
    "files": ["database.sql.gz", "n8n-data.tar.gz"]
}
EOF

echo "Backup complete: ${BACKUP_PATH}"
ls -la "${BACKUP_PATH}"
