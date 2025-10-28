import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.services.route_service import RouteService, RouteServiceFactory
from src.config import settings


class DummyDBClient:
    def get_tile_ids_by_buffer(self, area, buffer):
        return [101, 102]


class DummyRedisUtils:
    @staticmethod
    def prune_found_ids(tile_ids, redis):
        return []

    @staticmethod
    def get_gdf_by_list_of_keys(tile_ids, redis):
        lines = [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])]
        gdf = gpd.GeoDataFrame({
            "geometry": lines,
            "edge_id": ["e1", "e2"],
            "length_m": [100, 150],
            "aqi": [20, 40],
            "tile_id": [101, 102]
        }, crs="EPSG:25833")
        return gdf, []

    @staticmethod
    def edge_enricher_to_redis_handler(tile_ids, redis):
        pass


@pytest.fixture
def route_service(monkeypatch):
    monkeypatch.setattr(
        "src.services.route_service.DatabaseClient", lambda: DummyDBClient())
    monkeypatch.setattr(
        "src.services.route_service.RedisUtils", DummyRedisUtils)
    return RouteService(area="berlin")


def test_factory_returns_service_and_config():
    service, config = RouteServiceFactory.from_area("berlin")
    assert isinstance(service, RouteService)
    assert config.area == "berlin"


def test_create_buffer(route_service):
    origin = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:25833")
    destination = gpd.GeoDataFrame(geometry=[Point(2, 2)], crs="EPSG:25833")
    buffer = route_service._create_buffer(origin, destination, buffer_m=100)
    assert buffer.geom_type == "Polygon"
    assert buffer.area > 0


def test_compute_routes_structure(route_service):
    edges = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])],
        "edge_id": ["e1", "e2"],
        "length_m": [100, 150],
        "aqi": [20, 40],
        "tile_id": [101, 102]
    }, crs="EPSG:25833")

    origin = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:25833")
    destination = gpd.GeoDataFrame(geometry=[Point(2, 2)], crs="EPSG:25833")

    result = route_service._compute_routes(edges, origin, destination)
    assert "routes" in result
    assert "summaries" in result
    assert all(mode in result["routes"]
               for mode in ["fastest", "best_aq", "balanced"])


def test_get_route(route_service):
    origin = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:25833")
    destination = gpd.GeoDataFrame(geometry=[Point(2, 2)], crs="EPSG:25833")
    result = route_service.get_route(origin, destination)
    assert "routes" in result
    assert "summaries" in result
    assert all(mode in result["routes"]
               for mode in ["fastest", "best_aq", "balanced"])


def test_get_tile_edges(monkeypatch):
    monkeypatch.setattr(
        "src.services.route_service.RedisUtils", DummyRedisUtils)
    service = RouteService("berlin")
    tile_ids = [101]
    edges = service._get_tile_edges(tile_ids)
    assert isinstance(edges, gpd.GeoDataFrame)
    assert not edges.empty
    assert "edge_id" in edges.columns


def test_compute_routes_single_edge(route_service):
    edge = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "edge_id": ["e1"],
        "length_m": [100],
        "aqi": [20],
        "tile_id": [101]
    }, crs="EPSG:25833")

    origin = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:25833")
    destination = gpd.GeoDataFrame(geometry=[Point(1, 1)], crs="EPSG:25833")

    result = route_service._compute_routes(edge, origin, destination)
    assert "routes" in result
    assert "summaries" in result
