import redis
import json
import logging
from ..config.settings import RedisConfig

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, host=None, port=None, db=None, default_expire=None):
        """
        Initialize connection to Redis

        Args:
            host: Redis host. Defaults to config settings.
            port: Redis port. Defaults to config settings.
            db: Redis database number. Defaults to config settings.
            default_expire: Default expiration time in seconds. Defaults to config settings.
        """
        config = RedisConfig()
        
        host = host or config.host
        port = port or config.port
        db = db or config.db
        self.default_expire = default_expire or config.default_expire

        try:
            self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.client.ping()
            logger.info(f"Connected to redis at {host}:{port}")
        
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to redis: {e}")
            self.client = None
        
        
        
    def set(self, key, value, expire=None):
        """
        Set a value in the cache

        Args:
            key: The key to set.
            value: The value to set.
            expire: The expiration time in seconds. Defaults to None.
        """
        if not self.client: 
            logger.warning("Redis is not connected. Cannot set value.")
            return False
        
        try:
            expire_time = expire if expire is not None else self.default_expire
            self.client.set(key, json.dumps(value), ex=expire_time)
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to set cache key '{key}': {e}")
            return False


    def get(self,key):
        """
        Get a value from the cache
        """
        if not self.client:
            return None
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get cache key '{key}': {e}")
            return None
    
    
    def delete(self, key):
        """
        Delete a value from the cache
        """
        if not self.client:
            logger.warning("Redis is not connected. Cannot delete key.")
            return False
        try:
            result = self.client.delete(key)
            return result > 0
        except redis.RedisError as e:
            logger.error(f"Failed to delete cache key '{key}': {e}")
            return False

    def clear(self):
        """
        WARNING!: Clear the entire cache
        """
        if not self.client:
            logger.warning("Redis is not connected. Cannot clear cache.")
            return False
        try:
            self.client.flushdb()
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


