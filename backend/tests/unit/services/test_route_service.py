# tests/test_route_service.py

import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from unittest.mock import MagicMock

from src.services.route_service import RouteService


class DummyRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


@pytest.fixture
def route_service(monkeypatch):
    """RouteService with mocked Redis and RouteAlgorithm"""

    # Mock RouteAlgorithm globally
    dummy_route = gpd.GeoDataFrame(
        {"geometry": [LineString([(13.40, 52.52), (13.41, 52.53)])]},
        geometry="geometry",
        crs="EPSG:4326"
    )
    monkeypatch.setattr(
        "src.services.route_service.RouteAlgorithm",
        lambda edges: MagicMock(calculate=lambda o, d: dummy_route)
    )

    # Dummy edges
    dummy_edges = gpd.GeoDataFrame(
        {"geometry": [LineString([(13.40, 52.52), (13.41, 52.53)])]},
        geometry="geometry",
        crs="EPSG:4326"
    )

    # Create service with mocked Redis
    service = RouteService(edges=dummy_edges, redis=DummyRedis())
    return service


def test_get_route_computes_and_caches(route_service):
    """Test that get_route computes a new route and caches it"""

    origin_gdf = gpd.GeoDataFrame(geometry=[Point(13.40, 52.52)], crs="EPSG:4326")
    destination_gdf = gpd.GeoDataFrame(geometry=[Point(13.41, 52.53)], crs="EPSG:4326")

    result = route_service.get_route(origin_gdf, destination_gdf)

    assert "route" in result
    assert "summary" in result
    assert result["route"]["type"] == "FeatureCollection"
    assert len(result["route"]["features"]) == 1

    from pytest import approx
    coords = result["route"]["features"][0]["geometry"]["coordinates"]
    assert coords[0] == approx([13.40, 52.52], abs=1e-4)
    assert coords[-1] == approx([13.41, 52.53], abs=1e-4)

    origin = (round(13.40, 4), round(52.52, 4))
    destination = (round(13.41, 4), round(52.53, 4))
    cache_key = f"route_{origin[0]}_{origin[1]}_{destination[0]}_{destination[1]}"
    assert cache_key in route_service.redis.store



def test_get_route_returns_cached_result(route_service):
    """Test that get_route returns cached result if available"""

    origin_gdf = gpd.GeoDataFrame(geometry=[Point(13.40, 52.52)], crs="EPSG:4326")
    destination_gdf = gpd.GeoDataFrame(geometry=[Point(13.41, 52.53)], crs="EPSG:4326")
    cache_key = "route_13.4_52.52_13.41_52.53"

    expected_result = route_service.get_route(origin_gdf, destination_gdf)

    # Clear and manually set cache
    route_service.redis.store = {}
    route_service.redis.set(cache_key, expected_result)

    result = route_service.get_route(origin_gdf, destination_gdf)

    assert result == expected_result
