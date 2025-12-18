#!/bin/bash
# WordPress backup script - tested and verified
# Called with: SERVICE_ID, DATA_PATH, BACKUP_PATH

set -e

echo "Backing up WordPress: ${SERVICE_ID}"

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# Get database credentials from docker environment
DB_ROOT_PASS=$(docker inspect ${SERVICE_ID}-db --format '{{range .Config.Env}}{{println .}}{{end}}' | grep MYSQL_ROOT_PASSWORD | cut -d= -f2)

# Dump database
echo "Dumping database..."
docker exec ${SERVICE_ID}-db mysqldump -u root -p${DB_ROOT_PASS} wordpress > "${BACKUP_PATH}/database.sql"

# Compress database dump
gzip "${BACKUP_PATH}/database.sql"

# Backup wp-content
echo "Backing up wp-content..."
tar -czf "${BACKUP_PATH}/wp-content.tar.gz" -C "${DATA_PATH}" wp-content

# Create manifest
cat > "${BACKUP_PATH}/manifest.json" << EOF
{
    "service_id": "${SERVICE_ID}",
    "template": "wordpress",
    "timestamp": "$(date -Iseconds)",
    "wordpress_version": "6.4",
    "files": ["database.sql.gz", "wp-content.tar.gz"]
}
EOF

echo "Backup complete: ${BACKUP_PATH}"
ls -la "${BACKUP_PATH}"
