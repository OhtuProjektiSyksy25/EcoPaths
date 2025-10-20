# tests/test_route_service.py
import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.services.route_service import RouteService, RouteServiceFactory


@pytest.fixture
def sample_edges():
    lines = [
        LineString([(0, 0), (1, 1)]),
        LineString([(1, 1), (2, 2)])
    ]
    return gpd.GeoDataFrame({
        "geometry": lines,
        "length_m": [1.414, 1.414],
        "aq_value": [10, 5],
        "tile_id": [1, 1]
    }, crs="EPSG:3067")


@pytest.fixture
def route_service(sample_edges):
    return RouteService(sample_edges)


def test_create_buffer(route_service):
    origin = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:3067")
    destination = gpd.GeoDataFrame(geometry=[Point(2, 2)], crs="EPSG:3067")
    buffer = route_service._create_buffer(origin, destination, buffer_m=100)
    assert buffer.geom_type == "Polygon"
    assert buffer.area > 0


def test_get_route():
    routeservice2, _ = RouteServiceFactory.from_area("berlin")
    origin = gpd.GeoDataFrame(
        geometry=[Point(388150.1200319922, 5816784.541973761)], crs="EPSG:25833")
    destination = gpd.GeoDataFrame(
        geometry=[Point(388623.8279341213, 5819672.614198001)], crs="EPSG:25833")
    result = routeservice2.get_route(origin, destination)
    assert "routes" in result
    assert "summaries" in result
    assert all(mode in result["routes"]
               for mode in ["fastest", "best_aq", "balanced"])
