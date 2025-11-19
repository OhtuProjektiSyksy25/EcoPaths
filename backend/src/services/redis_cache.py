"""
Redis Cache functionality.
Provides methods to interact with a Redis cache.
"""

import json
import redis
from config.settings import RedisConfig
from src.logging.logger import log


class RedisCache:
    """Class for interacting with Redis cache."""

    def __init__(self, host=None, port=None, db=None, default_expire=None):
        """
        Initialize Redis connection.

        Args:
            host (str, optional): Redis host. Defaults to config settings.
            port (int, optional): Redis port. Defaults to config settings.
            db (int, optional): Redis database number. Defaults to config settings.
            default_expire (int, optional): Default expiration time in seconds. 
            Defaults to config settings.
        """
        config = RedisConfig()

        host = host or config.host
        port = port or config.port
        db = db or config.db
        self.default_expire = default_expire or config.default_expire

        try:
            if config.url:
                self.client = redis.from_url(config.url, decode_responses=True)
                self.client.ping()
                url_without_credentials = config.url.split('@')[-1]
                log.info(
                    f"Connected to Redis at  {url_without_credentials}",
                    url=url_without_credentials)
            else:
                self.client = redis.Redis(
                    host=host, port=port, db=db, decode_responses=True)
                self.client.ping()
                log.info(
                    f"Connected to Redis at {host} {port}", host=host, port=port)
        except redis.ConnectionError as e:
            log.error(
                f"Failed to connect to Redis:  {e}", error=str(e))
            self.client = None

    def _ensure_client(self):
        """Check if Redis client is available.

        Returns:
            bool: True if client exists, False otherwise.
        """
        if not self.client:
            log.warning(
                "Redis is not connected.")
            return False
        return True

    def _set(self, key, value, expire=None, as_json=True):
        """Internal method to set a value in Redis.

        Args:
            key (str): Key to set.
            value (Any): Value to store.
            expire (int, optional): Expiration time in seconds. Defaults to None.
            as_json (bool): Whether to store value as JSON. Defaults to True.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self._ensure_client():
            return False

        try:
            expire_time = expire if expire is not None else self.default_expire
            if as_json:
                value = json.dumps(value, separators=(',', ':'))
            self.client.set(key, value, ex=expire_time)
            log.debug(
                f"Cached key '{key}'", key=key)
            return True
        except (redis.RedisError, TypeError, ValueError) as e:
            log.error(
                f"Failed to set cache key '':  {key} {e}", key=key, error=str(e))
            return False

    def _get(self, key, as_json=True):
        """Internal method to get a value from Redis.

        Args:
            key (str): Key to retrieve.
            as_json (bool): Whether to parse as JSON. Defaults to True.

        Returns:
            Any: Retrieved value or None if not found or error occurs.
        """
        if not self._ensure_client():
            return None
        try:
            data = self.client.get(key)
            if not data:
                return None
            return json.loads(data) if as_json else data
        except (redis.RedisError, json.JSONDecodeError) as e:
            log.error(
                f"Failed to get cache key '':  {key} {e}", key=key, error=str(e))
            return None

    # Public methods
    def set_geojson(self, key, geojson_data, expire=None):
        """
        Store GeoJSON data in Redis.

        Args:
            key (str): Key to store the GeoJSON under.
            geojson_data (dict): GeoJSON data.
            expire (int, optional): Expiration in seconds. Defaults to None.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not isinstance(geojson_data, dict) or "type" not in geojson_data:
            log.warning(
                f"Invalid GeoJSON data for key '{key}'", key=key)
            return False
        return self._set(key, geojson_data, expire, as_json=True)

    def get_geojson(self, key):
        """
        Retrieve GeoJSON data from Redis.

        Args:
            key (str): Key of the GeoJSON data.

        Returns:
            dict | None: GeoJSON dict if valid, otherwise None.
        """
        geojson = self._get(key, as_json=True)
        if geojson and isinstance(geojson, dict) and "type" in geojson:
            return geojson
        if geojson:
            log.warning(
                f"Cached data for key {key} is not valid GeoJSON: {key} {geojson}", key=key)
        return None

    def set(self, key, value, expire=None):
        """
        Set a regular value in Redis (stored as JSON).

        Args:
            key (str): Key to store.
            value (Any): Value to store.
            expire (int, optional): Expiration in seconds.

        Returns:
            bool: True if successful, False otherwise.
        """
        return self._set(key, value, expire, as_json=True)

    def get(self, key):
        """
        Get a regular value from Redis (parsed as JSON).

        Args:
            key (str): Key to retrieve.

        Returns:
            Any: Value if exists, otherwise None.
        """
        return self._get(key, as_json=True)

    def delete(self, key):
        """
        Delete a key from Redis.

        Args:
            key (str): Key to delete.

        Returns:
            bool: True if key was deleted, False otherwise.
        """
        if not self._ensure_client():
            return False
        try:
            result = self.client.delete(key)
            return result > 0
        except redis.RedisError as e:
            log.error(
                f"Failed to delete cache key '':  {key} {e}", key=key, error=str(e))
            return False

    def exists(self, key):
        """
        Check if a key exists in Redis.

        Args:
            key (str): Key to check.

        Returns:
            bool: True if key exists, False otherwise.
        """
        if not self._ensure_client():
            return False
        try:
            return self.client.exists(key) == 1
        except redis.RedisError as e:
            log.error(
                f"Failed to check existence of cache key '':  {key} {e}", key=key, error=str(e))
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
            log.warning(
                "Redis is not connected. Cannot set value.")
            log.error(
                "Redis is not connected. Cannot set value.")
            return False

        try:
            expire_time = expire if expire is not None else self.default_expire
            self.client.set(key, value, ex=expire_time)
            log.debug(
                f"Cached value with key '{key}'", key=key)
            return True
        except (redis.RedisError, TypeError, ValueError) as e:
            log.error(
                f"Failed to set cache key '': {key} {e}", key=key, error=str(e))
            return False
