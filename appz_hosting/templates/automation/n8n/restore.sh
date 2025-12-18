#!/bin/bash
# n8n restore script
# Called with: SERVICE_ID, DATA_PATH, BACKUP_PATH

set -e

echo "Restoring n8n: ${SERVICE_ID} from ${BACKUP_PATH}"

# Stop app container (keep db running)
echo "Stopping app container..."
docker stop ${SERVICE_ID}-app || true

# Restore database
echo "Restoring database..."
if [ -f "${BACKUP_PATH}/database.sql.gz" ]; then
    # Drop and recreate database
    docker exec ${SERVICE_ID}-db psql -U n8n -c "DROP DATABASE IF EXISTS n8n_backup;"
    docker exec ${SERVICE_ID}-db psql -U n8n -c "CREATE DATABASE n8n_backup;"
    gunzip -c "${BACKUP_PATH}/database.sql.gz" | docker exec -i ${SERVICE_ID}-db psql -U n8n n8n
elif [ -f "${BACKUP_PATH}/database.sql" ]; then
    docker exec -i ${SERVICE_ID}-db psql -U n8n n8n < "${BACKUP_PATH}/database.sql"
fi

# Restore n8n data
echo "Restoring n8n data..."
if [ -f "${BACKUP_PATH}/n8n-data.tar.gz" ]; then
    rm -rf "${DATA_PATH}/n8n"
    tar -xzf "${BACKUP_PATH}/n8n-data.tar.gz" -C "${DATA_PATH}"
fi

# Restart app
echo "Starting app container..."
docker start ${SERVICE_ID}-app

# Wait for app to be healthy
echo "Waiting for app to be healthy..."
sleep 10

echo "Restore complete"
