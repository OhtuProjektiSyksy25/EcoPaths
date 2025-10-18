import pytest
from unittest.mock import Mock, patch, MagicMock
import redis
import json
from src.services.redis_cache import RedisCache


class TestRedisCache:
    """
    Test RedisCache functionality.
    """
    @patch("src.services.redis_cache.redis.Redis")
    def test_connection(self, mock_redis):
        """Test successful connection to Redis."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        cache = RedisCache()

        assert cache.client == mock_client
        mock_client.ping.assert_called_once()

    def test_set_function(self):
        """Test setting a value in Redis."""
        mock_client = MagicMock()
        with patch("src.services.redis_cache.redis.Redis", return_value=mock_client):
            cache = RedisCache()
            result = cache.set("test_key", {"data": 123})

            assert result is True
            mock_client.set.assert_called_once_with(
                "test_key", json.dumps({"data": 123}), ex=3600)

    def test_get_function(self):
        """Test getting a value from Redis."""
        mock_client = MagicMock()
        with patch("src.services.redis_cache.redis.Redis", return_value=mock_client):
            cache = RedisCache()
            mock_client.get.return_value = json.dumps(
                {"data": 123}).encode('utf-8')

            result = cache.get("test_key")

            mock_client.get.assert_called_once_with("test_key")
            assert result == {"data": 123}

    def test_get_not_found(self):
        """Test that get returns None when key doesn't exist."""
        mock_client = MagicMock()
        with patch("src.services.redis_cache.redis.Redis", return_value=mock_client):
            cache = RedisCache()
            mock_client.get.return_value = None

            result = cache.get("missing_key")

            mock_client.get.assert_called_once_with("missing_key")
            assert result is None

    def test_default_expire_value(self):
        """Test default expiration time is set correctly"""
        mock_client = MagicMock()
        with patch("src.services.redis_cache.redis.Redis", return_value=mock_client):
            cache = RedisCache()
            assert cache.default_expire == 3600

    def test_exists_method(self):
        """Test exists method"""
        mock_client = MagicMock()
        mock_client.exists.return_value = True
        with patch("src.services.redis_cache.redis.Redis", return_value=mock_client):
            cache = RedisCache()
            result = cache.exists("test_key")
            assert result is True
            mock_client.exists.assert_called_once_with("test_key")

    def test_delete_method(self):
        """Test delete method"""
        mock_client = MagicMock()
        mock_client.delete.return_value = 1
        with patch("src.services.redis_cache.redis.Redis", return_value=mock_client):
            cache = RedisCache()
            result = cache.delete("test_key")
            assert result == 1
            mock_client.delete.assert_called_once_with("test_key")
