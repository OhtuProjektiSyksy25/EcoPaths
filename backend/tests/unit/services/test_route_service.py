# tests/test_route_service.py

import pytest
import geopandas as gpd
from shapely.geometry import LineString, mapping

from src.services.route_service import RouteService


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
        # CRS must match the origin/destination CRS (EPSG:4326)
        return gpd.GeoDataFrame(
            [{"geometry": LineString([(13.40, 52.52), (13.41, 52.53)]), "length_m": 100}],
            geometry="geometry",
            crs="EPSG:4326"
        )




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


def test_calculate_time_estimate_formats_correctly(route_service):
    """Test that _calculate_time_estimate formats time correctly for different distances"""
    
    # Test short distance (less than 1 hour)
    # 300 meters at 5 m/s = 60 seconds = 1 minute
    result = route_service._calculate_time_estimate(300.0)
    assert result == "1 min 0 s"
    
    # Test medium distance
    # 1500 meters at 5 m/s = 300 seconds = 5 minutes
    result = route_service._calculate_time_estimate(1500.0)
    assert result == "5 min 0 s"
    
    # Test long distance (over 1 hour)
    # 20000 meters at 5 m/s = 4000 seconds = 1 hour 6 minutes 40 seconds
    result = route_service._calculate_time_estimate(20000.0)
    assert result == "1h 6 min"
    
    # Test very long distance (multiple hours)
    # 54000 meters at 5 m/s = 10800 seconds = 3 hours exactly
    result = route_service._calculate_time_estimate(54000.0)
    assert result == "3h 0 min"


def test_calculate_time_estimate_edge_cases(route_service):
    """Test edge cases for time estimation"""
    
    # Test zero distance
    result = route_service._calculate_time_estimate(0.0)
    assert result == "0 min 0 s"
    
    # Test very small distance (1 meter)
    result = route_service._calculate_time_estimate(1.0)
    assert result == "0 min 0 s"  # Should round down to 0
    
    # Test exactly 1 hour (18000 meters at 5 m/s)
    result = route_service._calculate_time_estimate(18000.0)
    assert result == "1h 0 min"


def test_calculate_time_estimate_uses_correct_speed(route_service):
    """Test that the method uses the expected walking speed: 5m per second"""
    
    # 5 meters at 5 m/s should be exactly 1 second
    result = route_service._calculate_time_estimate(5.0)
    assert result == "0 min 1 s"
    
    # 25 meters at 5 m/s should be exactly 5 seconds
    result = route_service._calculate_time_estimate(25.0)
    assert result == "0 min 5 s"
