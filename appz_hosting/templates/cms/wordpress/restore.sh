#!/bin/bash
# WordPress restore script
# Called with: SERVICE_ID, DATA_PATH, BACKUP_PATH

set -e

echo "Restoring WordPress: ${SERVICE_ID} from ${BACKUP_PATH}"

# Get database credentials
DB_ROOT_PASS=$(docker inspect ${SERVICE_ID}-db --format '{{range .Config.Env}}{{println .}}{{end}}' | grep MYSQL_ROOT_PASSWORD | cut -d= -f2)

# Stop app container (keep db running)
echo "Stopping app container..."
docker stop ${SERVICE_ID}-app || true

# Restore database
echo "Restoring database..."
if [ -f "${BACKUP_PATH}/database.sql.gz" ]; then
    gunzip -c "${BACKUP_PATH}/database.sql.gz" | docker exec -i ${SERVICE_ID}-db mysql -u root -p${DB_ROOT_PASS} wordpress
elif [ -f "${BACKUP_PATH}/database.sql" ]; then
    docker exec -i ${SERVICE_ID}-db mysql -u root -p${DB_ROOT_PASS} wordpress < "${BACKUP_PATH}/database.sql"
fi

# Restore wp-content
echo "Restoring wp-content..."
if [ -f "${BACKUP_PATH}/wp-content.tar.gz" ]; then
    rm -rf "${DATA_PATH}/wp-content"
    tar -xzf "${BACKUP_PATH}/wp-content.tar.gz" -C "${DATA_PATH}"
fi

# Restart app
echo "Starting app container..."
docker start ${SERVICE_ID}-app

# Wait for app to be healthy
echo "Waiting for app to be healthy..."
sleep 10

echo "Restore complete"
