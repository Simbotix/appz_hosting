#!/bin/bash
# Ghost backup script - tested and verified
# Called with: SERVICE_ID, DATA_PATH, BACKUP_PATH

set -e

echo "Backing up Ghost: ${SERVICE_ID}"

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# Get database credentials
DB_ROOT_PASS=$(docker inspect ${SERVICE_ID}-db --format '{{range .Config.Env}}{{println .}}{{end}}' | grep MYSQL_ROOT_PASSWORD | cut -d= -f2)

# Dump database
echo "Dumping database..."
docker exec ${SERVICE_ID}-db mysqldump -u root -p${DB_ROOT_PASS} ghost > "${BACKUP_PATH}/database.sql"

# Compress database dump
gzip "${BACKUP_PATH}/database.sql"

# Backup content directory
echo "Backing up content..."
tar -czf "${BACKUP_PATH}/content.tar.gz" -C "${DATA_PATH}" content

# Create manifest
cat > "${BACKUP_PATH}/manifest.json" << EOF
{
    "service_id": "${SERVICE_ID}",
    "template": "ghost",
    "timestamp": "$(date -Iseconds)",
    "ghost_version": "5",
    "files": ["database.sql.gz", "content.tar.gz"]
}
EOF

echo "Backup complete: ${BACKUP_PATH}"
ls -la "${BACKUP_PATH}"
