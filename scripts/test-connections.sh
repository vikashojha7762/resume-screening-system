#!/bin/bash

# Connection test script
echo "Testing database and Redis connections..."

# Test PostgreSQL
echo ""
echo "Testing PostgreSQL connection..."
docker-compose exec backend python -m app.core.db_connection_test

# Test Redis
echo ""
echo "Testing Redis connection..."
docker-compose exec backend python -c "from app.core.redis_client import get_redis_client; client = get_redis_client(); print('Redis ping:', client.ping())"

