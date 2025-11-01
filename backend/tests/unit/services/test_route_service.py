import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.services.route_service import RouteService, RouteServiceFactory
from src.config import settings
from unittest.mock import patch


class DummyDBClient:
    def get_tile_ids_by_buffer(self, area, buffer):
        return [101, 102]


class DummyRedisService:
    @staticmethod
    def prune_found_ids(tile_ids, redis):
        return []

    @staticmethod
    def get_gdf_by_list_of_keys(tile_ids, redis, area):
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
    def edge_enricher_to_redis_handler(tile_ids, redis, area):
        lines = [LineString([(3, 3), (4, 4)]), LineString([(4, 4), (5, 52)])]
        gdf = gpd.GeoDataFrame({
            "geometry": lines,
            "edge_id": ["e6", "e7"],
            "length_m": [100, 150],
            "aqi": [20, 40],
            "tile_id": [103, 104]
        }, crs="EPSG:25833")
        return gdf
    
    @staticmethod
    def save_gdf(gdf, redis, area):
        return True
    
def dummy_get_enriched_tiles(self, tile_ids, network_type="walking"):
    gdf = gpd.GeoDataFrame({
        "edge_id": [1, 2],
        "geometry": [
            LineString([(0, 0), (1, 1)]),
            LineString([(1, 1), (2, 2)])
        ],
        "tile_id": ["t101", "t102"],
        "length_m": [10, 10],
        "from_node": [1, 2],
        "to_node": [2, 3],
        "aqi": [20.0, 40.0],
    }, crs="EPSG:25833")
    return gdf


@pytest.fixture
def route_service(monkeypatch):
    monkeypatch.setattr(
        "src.services.route_service.DatabaseClient", lambda: DummyDBClient())
    monkeypatch.setattr(
        "src.services.route_service.RedisService", DummyRedisService)
    monkeypatch.setattr(
        "src.services.route_service.EdgeEnricher.get_enriched_tiles", dummy_get_enriched_tiles)
    return RouteService("testarea")


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


def test_get_tile_edges_no_existing_tiles(route_service):
    with (
        patch("src.services.route_service.RedisService.prune_found_ids", return_value=[]),
        patch("src.services.route_service.RedisService.save_gdf", return_value=True) as mock_save
    ):
        tile_ids = [101, 102, 103, 104]
        edges = route_service._get_tile_edges(tile_ids)

        assert isinstance(edges, gpd.GeoDataFrame)
        assert not edges.empty
        assert "edge_id" in edges.columns
        assert mock_save.call_count == 0


def test_get_tile_edges_with_existing_tiles(route_service):
    with (
        patch("src.services.route_service.RedisService.prune_found_ids", return_value=[101]),
        patch("src.services.route_service.RedisService.save_gdf", return_value=True) as mock_save
    ):
        tile_ids = [101, 102, 103, 104]
        edges = route_service._get_tile_edges(tile_ids)
        assert isinstance(edges, gpd.GeoDataFrame)
        assert not edges.empty
        assert "edge_id" in edges.columns
        assert mock_save.call_count == 1

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
