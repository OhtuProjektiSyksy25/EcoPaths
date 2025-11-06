import pytest
from unittest.mock import MagicMock, patch, Mock
import json
from src.services.redis_cache import RedisCache


@pytest.fixture
def mock_cache():
    """Fixture providing a RedisCache with mocked Redis client."""
    with patch("src.services.redis_cache.redis.Redis") as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        cache = RedisCache()
        yield cache, mock_client


@pytest.mark.parametrize(
    "key,value,method",
    [
        ("test_key", {"foo": "bar"}, "regular"),
        ("geo_key", {"type": "FeatureCollection", "features": []}, "geojson"),
    ],
)
def test_set_and_get(mock_cache, key, value, method):
    cache, mock_client = mock_cache

    if method == "regular":
        # set/get
        assert cache.set(key, value) is True
        expected_value = json.dumps(value, separators=(',', ':'))
        mock_client.set.assert_called_once_with(
            key, expected_value, ex=cache.default_expire)
        mock_client.get.return_value = expected_value
        assert cache.get(key) == value

    elif method == "geojson":
        assert cache.set_geojson(key, value) is True
        expected_value = json.dumps(value, separators=(',', ':'))
        mock_client.set.assert_called_once_with(
            key, expected_value, ex=cache.default_expire)
        mock_client.get.return_value = expected_value
        assert cache.get_geojson(key) == value


def test_get_geojson_invalid(mock_cache, caplog):
    cache, mock_client = mock_cache
    mock_client.get.return_value = json.dumps({"foo": "bar"})
    with caplog.at_level("WARNING"):
        result = cache.get_geojson("geo_key")
        assert result is None
        assert "is not valid GeoJSON" in caplog.text


def test_set_geojson_invalid():
    cache = RedisCache()
    result = cache.set_geojson("key", {"wrong": "data"})
    assert result is False


def test_exists_method(mock_cache):
    cache, mock_client = mock_cache
    mock_client.exists.return_value = 1
    assert cache.exists("test_key") is True
    mock_client.exists.assert_called_once_with("test_key")


def test_delete_method(mock_cache):
    cache, mock_client = mock_cache
    mock_client.delete.return_value = 1
    assert cache.delete("test_key") is True
    mock_client.delete.assert_called_once_with("test_key")


def test_ensure_client_warning(caplog):
    cache = RedisCache()
    cache.client = None
    with caplog.at_level("WARNING"):
        assert cache._ensure_client() is False
        assert "Redis is not connected" in caplog.text


def test_internal_set_get_paths(mock_cache):
    cache, mock_client = mock_cache
    # _set stores JSON by default
    assert cache._set("key", {"a": 1}) is True
    expected_value = json.dumps({"a": 1}, separators=(',', ':'))
    mock_client.set.assert_called_with(
        "key", expected_value, ex=cache.default_expire)

    # _get retrieves it
    mock_client.get.return_value = expected_value
    result = cache._get("key")
    assert result == {"a": 1}


def test_set_direct_method(mock_cache):
    cache, mock_client = mock_cache
    # simple string value
    assert cache.set_direct("key", "raw_value") is True
    mock_client.set.assert_called_with(
        "key", "raw_value", ex=cache.default_expire)


def test_get_returns_none_when_client_missing():
    cache = RedisCache()
    cache.client = None
    assert cache._get("key") is None
    assert cache._set("key", "value") is False
    assert cache.set_direct("key", "value") is False


def test_delete_exists_with_client_missing():
    cache = RedisCache()
    cache.client = None
    assert cache.delete("key") is False
    assert cache.exists("key") is False
