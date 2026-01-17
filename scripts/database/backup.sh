#!/bin/bash

# Database Backup Script
# Creates automated backups with retention policy

set -e

# Configuration
BACKUP_DIR="/backups/postgres"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-resume_screening}"
DB_HOST="${DB_HOST:-postgres-service}"
DB_USER="${DB_USER:-postgres}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "Starting database backup at $(date)"
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom \
    --file="$BACKUP_DIR/backup_${TIMESTAMP}.dump"

# Compress backup
gzip "$BACKUP_DIR/backup_${TIMESTAMP}.dump"

echo "Backup completed: backup_${TIMESTAMP}.dump.gz"

# Upload to S3 (if configured)
if [ -n "$AWS_S3_BACKUP_BUCKET" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "$BACKUP_DIR/backup_${TIMESTAMP}.dump.gz" \
        "s3://$AWS_S3_BACKUP_BUCKET/postgres/backup_${TIMESTAMP}.dump.gz"
    echo "Backup uploaded to S3"
fi

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "backup_*.dump.gz" -mtime +$RETENTION_DAYS -delete

# Cleanup S3 backups
if [ -n "$AWS_S3_BACKUP_BUCKET" ]; then
    aws s3 ls "s3://$AWS_S3_BACKUP_BUCKET/postgres/" | \
    while read -r line; do
        createDate=$(echo $line | awk '{print $1" "$2}')
        createDate=$(date -d "$createDate" +%s)
        olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
        if [[ $createDate -lt $olderThan ]]; then
            fileName=$(echo $line | awk '{print $4}')
            if [[ $fileName != "" ]]; then
                aws s3 rm "s3://$AWS_S3_BACKUP_BUCKET/postgres/$fileName"
            fi
        fi
    done
fi

echo "Backup process completed at $(date)"

