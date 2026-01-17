"""
Database and Redis connection test utility
"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.redis_client import get_redis_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        logger.info("Testing PostgreSQL connection...")
        logger.info(f"Database URL: postgresql://{settings.DB_USER}:***@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"✅ PostgreSQL connection successful!")
            logger.info(f"   PostgreSQL version: {version}")
            
            # Test pgvector extension
            try:
                result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector';"))
                ext = result.fetchone()
                if ext:
                    logger.info(f"✅ pgvector extension is installed")
                else:
                    logger.warning("⚠️  pgvector extension not found. Run: CREATE EXTENSION vector;")
            except Exception as e:
                logger.warning(f"⚠️  Could not check pgvector extension: {str(e)}")
            
            return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {str(e)}")
        return False


def test_redis_connection():
    """Test Redis connection"""
    try:
        logger.info("Testing Redis connection...")
        logger.info(f"Redis Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
        redis_client = get_redis_client()
        redis_client.ping()
        logger.info("✅ Redis connection successful!")
        
        # Test set/get
        test_key = "connection_test"
        test_value = "test_value"
        redis_client.set(test_key, test_value, ex=10)
        retrieved = redis_client.get(test_key)
        
        if retrieved == test_value:
            logger.info("✅ Redis read/write test successful!")
            redis_client.delete(test_key)
        else:
            logger.warning("⚠️  Redis read/write test failed")
        
        # Get Redis info
        info = redis_client.info("server")
        logger.info(f"   Redis version: {info.get('redis_version', 'unknown')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {str(e)}")
        return False


def main():
    """Run all connection tests"""
    logger.info("=" * 50)
    logger.info("Connection Test Suite")
    logger.info("=" * 50)
    logger.info("")
    
    pg_success = test_postgres_connection()
    logger.info("")
    redis_success = test_redis_connection()
    
    logger.info("")
    logger.info("=" * 50)
    if pg_success and redis_success:
        logger.info("✅ All connections successful!")
        sys.exit(0)
    else:
        logger.error("❌ Some connections failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

