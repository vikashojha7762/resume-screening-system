import redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Redis client singleton
_redis_client: redis.Redis = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client instance"""
    global _redis_client
    if _redis_client is None:
        try:
            # Redis Labs typically requires SSL
            # Try with SSL first, fallback to non-SSL if needed
            try:
                _redis_client = redis.from_url(
                    settings.REDIS_URL.replace("redis://", "rediss://"),  # Use rediss:// for SSL
                    decode_responses=True,
                    socket_connect_timeout=10,
                    socket_timeout=10,
                    retry_on_timeout=True,
                    ssl_cert_reqs=None  # Redis Labs uses self-signed certs
                )
                _redis_client.ping()
                logger.info("Redis client connected successfully with SSL")
            except Exception as ssl_error:
                logger.info(f"SSL connection failed, trying without SSL: {str(ssl_error)}")
                # Fallback to non-SSL
                _redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=10,
                    socket_timeout=10,
                    retry_on_timeout=True
                )
                _redis_client.ping()
                logger.info("Redis client connected successfully without SSL")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    return _redis_client


def close_redis_client():
    """Close Redis client connection"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")


# Cache utility functions
def cache_get(key: str) -> str:
    """Get value from cache"""
    try:
        client = get_redis_client()
        return client.get(key)
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {str(e)}")
        return None


def cache_set(key: str, value: str, ttl: int = None):
    """Set value in cache with optional TTL"""
    try:
        client = get_redis_client()
        if ttl:
            client.setex(key, ttl, value)
        else:
            client.set(key, value)
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {str(e)}")


def cache_delete(key: str):
    """Delete key from cache"""
    try:
        client = get_redis_client()
        client.delete(key)
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {str(e)}")


def cache_exists(key: str) -> bool:
    """Check if key exists in cache"""
    try:
        client = get_redis_client()
        return client.exists(key) > 0
    except Exception as e:
        logger.error(f"Cache exists error for key {key}: {str(e)}")
        return False

