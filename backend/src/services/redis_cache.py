"""
Redis Cache functionality.
Provides methods to interact with a Redis cache.
"""

import json
import logging
import redis
from config.settings import RedisConfig

logger = logging.getLogger(__name__)


class RedisCache:
    """Class for methods to interact with Redis cache.
    """

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
            self.client = redis.Redis(
                host=host, port=port, db=db, decode_responses=True)
            self.client.ping()
            logger.info("Connected to redis at %s:%s", host, port)

        except redis.ConnectionError as e:
            logger.error("Failed to connect to redis: %s", e)
            self.client = None

    def set_geojson(self, key, geojson_data, expire=None):
        """
        Set a GeoJSON data in the cache

        Args:
            key: The key to set.
            geojson_data: The GeoJSON data to set.
            expire: The expiration time in seconds. Defaults to None.
        """
        if not self.client:
            logger.warning("Redis is not connected. Cannot set GeoJSON.")
            return False

        try:
            if isinstance(geojson_data, dict):
                if "type" not in geojson_data:
                    logger.warning(
                        "Invalid GeoJSON data: missing 'type' field.")
                    return False

            expire_time = expire if expire is not None else self.default_expire

            json_string = json.dumps(geojson_data, separators=(',', ':'))
            self.client.set(key, json_string, ex=expire_time)

            logger.debug("Cached GeoJSON data with key '%s'", key)
            return True

        except (redis.RedisError, TypeError, ValueError) as e:
            logger.error("Failed to cache GeoJSON data: '%s': %s", key, e)
            return False

    def get_geojson(self, key):
        """
        Get a GeoJSON data from the cache
        """
        if not self.client:
            logger.warning("Redis is not connected. Cannot get GeoJSON.")
            return None
        try:
            data = self.client.get(key)
            if not data:
                return None

            geojson_object = json.loads(data)

            if isinstance(geojson_object, dict) and "type" in geojson_object:
                logger.debug("Retrieved GeoJSON with key '%s'", key)
                return geojson_object

            logger.warning(
                "Cached data for key '%s' is not valid GeoJSON", key)
            return None

        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error("Failed to get cache key '%s': %s", key, e)
            return None

    def set(self, key, value, expire=None):
        """
        Set a regular (non-GeoJSON) value in the cache

        Args:
            key: The key to set.
            value: The value to set.
            expire: The expiration time in seconds.
        """
        if not self.client:
            logger.warning("Redis is not connected. Cannot set value.")
            print("Redis is not connected. Cannot set value.")
            return False

        try:
            expire_time = expire if expire is not None else self.default_expire
            self.client.set(key, json.dumps(value), ex=expire_time)
            print(f"Cached value with key '{key}'")
            return True
        except (redis.RedisError, TypeError, ValueError) as e:
            logger.error("Failed to set cache key '%s': %s", key, e)
            return False

    def get(self, key):
        """
        Get a regular (non-GeoJSON) value from the cache
        """
        if not self.client:
            logger.warning("Redis is not connected. Cannot get value.")
            return None
        try:
            data = self.client.get(key)
            if not data:
                return None
            return json.loads(data)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error("Failed to get cache key '%s': %s", key, e)
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
            logger.error("Failed to delete cache key '%s': %s", key, e)
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
            logger.error("Failed to clear cache: %s", e)
            return False

    def exists(self, key):
        """
        Check if a key exists in the cache
        """
        if not self.client:
            logger.warning(
                "Redis is not connected. Cannot check key existence.")
            return False
        try:
            return self.client.exists(key) == 1
        except redis.RedisError as e:
            logger.error(
                "Failed to check existence of cache key '%s': %s", key, e)
            return False

    def set_direct(self, key, value, expire=None):
        """
        Set a regular (non-GeoJSON) value in the cache directly

        Args:
            key: The key to set.
            value: The value to set.
            expire: The expiration time in seconds.
        """
        if not self.client:
            logger.warning("Redis is not connected. Cannot set value.")
            print("Redis is not connected. Cannot set value.")
            return False

        try:
            expire_time = expire if expire is not None else self.default_expire
            self.client.set(key, value, ex=expire_time)
            print(f"Cached value with key '{key}'")
            return True
        except (redis.RedisError, TypeError, ValueError) as e:
            logger.error("Failed to set cache key '%s': %s", key, e)
            return False
        
# needs generate_route_key method
