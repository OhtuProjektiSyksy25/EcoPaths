# tests/test_route_service.py

import pytest
from shapely.geometry import LineString, mapping

from services.route_service import RouteService


class DummyRedis:
    """Fake RedisCache for testing"""
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


class DummyComputeModel:
    """Fake ComputeModel for testing"""
    def __init__(self, area="berlin"):
        self.area = area

    def get_data_for_algorithm(self):
        return ["dummy_edges"]


@pytest.fixture
def route_service(monkeypatch):
    """RouteService with dummy Redis and ComputeModel"""
    service = RouteService(area="berlin")

    # Patch Redis and ComputeModel
    monkeypatch.setattr(service, "redis", DummyRedis())
    monkeypatch.setattr(service, "compute_model", DummyComputeModel())

    return service


def test_get_route_computes_and_caches(route_service):
    """Test that get_route computes a new route and caches it"""

    origin = (13.40, 52.52)
    destination = (13.41, 52.53)

    route = route_service.get_route(origin, destination)

    assert route["type"] == "Feature"
    assert route["geometry"]["type"] == "LineString"

    # Should contain the origin and destination coordinates
    coords = route["geometry"]["coordinates"]
    assert coords[0] == origin
    assert coords[-1] == destination

    # Cache key must exist
    cache_key = f"route_berlin_{origin[0]}_{origin[1]}_{destination[0]}_{destination[1]}"
    assert cache_key in route_service.redis.store


def test_get_route_returns_cached_result(route_service):
    """Test that get_route returns cached result if available"""

    origin = (13.40, 52.52)
    destination = (13.41, 52.53)
    cache_key = f"route_berlin_{origin[0]}_{origin[1]}_{destination[0]}_{destination[1]}"

    cached_feature = {
        "type": "Feature",
        "geometry": mapping(LineString([origin, destination])),
        "properties": {"cached": True}
    }

    # Pre-populate cache
    route_service.redis.set(cache_key, cached_feature)

    route = route_service.get_route(origin, destination)

    # Should return cached result instead of recomputing
    assert route == cached_feature
    assert route["properties"]["cached"] is True
