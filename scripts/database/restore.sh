#!/bin/bash

# Database Restore Script
# Restores database from backup file

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.dump.gz>"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="${DB_NAME:-resume_screening}"
DB_HOST="${DB_HOST:-postgres-service}"
DB_USER="${DB_USER:-postgres}"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE not found"
    exit 1
fi

# Confirm restore
read -p "WARNING: This will overwrite the current database. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo "Starting database restore from $BACKUP_FILE"

# Decompress if needed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing backup file..."
    gunzip -c "$BACKUP_FILE" > /tmp/restore.dump
    RESTORE_FILE="/tmp/restore.dump"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Drop existing database connections
echo "Terminating existing connections..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();
EOF

# Drop and recreate database
echo "Dropping and recreating database..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d postgres <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;
EOF

# Restore from backup
echo "Restoring database..."
PGPASSWORD="$DB_PASSWORD" pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --verbose \
    --no-owner \
    --no-acl \
    "$RESTORE_FILE"

# Cleanup
if [ -f "/tmp/restore.dump" ]; then
    rm /tmp/restore.dump
fi

echo "Database restore completed successfully"

