#!/bin/bash

# Database Optimization Script
# Performs maintenance and optimization tasks

set -e

DB_NAME="${DB_NAME:-resume_screening}"
DB_HOST="${DB_HOST:-postgres-service}"
DB_USER="${DB_USER:-postgres}"

echo "Starting database optimization at $(date)"

# Vacuum and analyze
echo "Running VACUUM ANALYZE..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<EOF
VACUUM ANALYZE;
EOF

# Reindex
echo "Reindexing database..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<EOF
REINDEX DATABASE $DB_NAME;
EOF

# Update statistics
echo "Updating query planner statistics..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<EOF
ANALYZE;
EOF

# Check for bloat
echo "Checking for table bloat..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<EOF
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS bloat
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
EOF

# Check connection pool
echo "Checking connection pool status..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" <<EOF
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active_connections,
    count(*) FILTER (WHERE state = 'idle') as idle_connections,
    max_conn as max_connections
FROM pg_stat_activity, 
     (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') mc
GROUP BY max_conn;
EOF

echo "Database optimization completed at $(date)"

