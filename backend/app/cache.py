import aioredis
from typing import Optional
from .config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None

async def get_redis_client() -> aioredis.Redis:
    """Get or create Redis client instance"""
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            await _redis_client.ping()
            logger.info("Redis client connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    return _redis_client

async def close_redis_client():
    """Close Redis client connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client connection closed")