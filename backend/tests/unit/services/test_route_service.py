# tests/test_route_service.py
import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.services.route_service import RouteService


@pytest.fixture
def sample_edges():
    """Create sample edges with correct columns."""
    lines = [
        LineString([(0, 0), (1, 1)]),
        LineString([(1, 1), (2, 2)]),
        LineString([(2, 2), (3, 3)])
    ]
    return gpd.GeoDataFrame({
        "geometry": lines,
        "edge_id": ["e1", "e2", "e3"],
        "length_m": [141.4, 141.4, 141.4],
        "aqi": [10, 20, 30],
        "tile_id": ["r1_c1", "r1_c1", "r2_c2"]
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


# def test_get_route():
#     routeservice2, _ = RouteServiceFactory.from_area("berlin")
#     origin = gpd.GeoDataFrame(
#         geometry=[Point(388150.1200319922, 5816784.541973761)], crs="EPSG:25833")
#     destination = gpd.GeoDataFrame(
#         geometry=[Point(388623.8279341213, 5819672.614198001)], crs="EPSG:25833")
#     result = routeservice2.get_route(origin, destination)
#     assert "routes" in result
#     assert "summaries" in result
#     assert all(mode in result["routes"]
#                for mode in ["fastest", "best_aq", "balanced"])


def test_route_service_initialization(sample_edges):
    """Test RouteService initializes correctly."""
    service = RouteService(sample_edges)

    assert service.edges is not None
    assert len(service.edges) == 3
    assert service.redis is not None
    assert "tile_id" in service.edges.columns


def test_route_service_has_required_columns(sample_edges):
    """Test that edges have all required columns."""
    service = RouteService(sample_edges)

    required_columns = ["geometry", "edge_id", "length_m", "aqi", "tile_id"]
    for col in required_columns:
        assert col in service.edges.columns
