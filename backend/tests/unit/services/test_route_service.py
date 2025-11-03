import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.services.route_service import RouteService, RouteServiceFactory


class DummyRedisService:
    @staticmethod
    def prune_found_ids(tile_ids, redis):
        return [t for t in tile_ids if t.endswith("2")]

    @staticmethod
    def get_gdf_by_list_of_keys(tile_ids, redis, area_config):
        gdf = gpd.GeoDataFrame({
            "edge_id": [1] * len(tile_ids),
            "geometry": [LineString([(0, 0), (1, 1)])] * len(tile_ids),
            "tile_id": tile_ids,
            "length_m": [10] * len(tile_ids),
            "from_node": [1] * len(tile_ids),
            "to_node": [2] * len(tile_ids),
            "aqi": [25.0] * len(tile_ids),
        }, crs="EPSG:25833")
        return gdf, []

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
        "src.services.route_service.RedisService", DummyRedisService)
    monkeypatch.setattr(
        "src.services.route_service.EdgeEnricher.get_enriched_tiles", dummy_get_enriched_tiles)
    monkeypatch.setattr("src.services.route_service.DatabaseClient.get_tile_ids_by_buffer",
                        lambda self, area, buffer: ["t101", "t102"])
    return RouteService("testarea")


@pytest.fixture
def origin_destination():
    origin = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:25833")
    destination = gpd.GeoDataFrame(geometry=[Point(2, 2)], crs="EPSG:25833")
    return origin, destination


def test_factory_creates_service_and_config():
    service, config = RouteServiceFactory.from_area("testarea")
    assert isinstance(service, RouteService)
    assert config.area == "testarea"


def test_create_buffer_returns_polygon(route_service, origin_destination):
    origin, destination = origin_destination
    buffer = route_service._create_buffer(origin, destination, buffer_m=100)
    assert buffer.geom_type == "Polygon"
    assert buffer.area > 0


def test_get_tile_edges_returns_expected_data(route_service):
    tile_ids = ["t101", "t102", "t103"]
    result = route_service._get_tile_edges(tile_ids)
    assert isinstance(result, gpd.GeoDataFrame)
    assert not result.empty
    assert "aqi" in result.columns
    assert all(tid in tile_ids for tid in result["tile_id"])
    assert result.crs.to_string() == "EPSG:25833"


def test_prune_and_fetch_combines_correctly(monkeypatch, route_service):
    monkeypatch.setattr(DummyRedisService, "prune_found_ids",
                        staticmethod(lambda ids, r: ["t102", "t103"]))
    tile_ids = ["t101", "t102", "t103"]
    edges = route_service._get_tile_edges(tile_ids)
    assert not edges.empty
    assert set(edges["tile_id"]).issubset(set(tile_ids))


def test_save_to_redis_is_triggered(monkeypatch, route_service):
    called = {}

    def fake_save_gdf(gdf, redis, area):
        called["was_called"] = True
        return True

    monkeypatch.setattr(DummyRedisService, "prune_found_ids",
                        staticmethod(lambda ids, r: ids))
    monkeypatch.setattr(DummyRedisService, "save_gdf",
                        staticmethod(fake_save_gdf))

    _ = route_service._get_tile_edges(["t104", "t106"])
    assert called.get("was_called", False)


def test_compute_routes_returns_all_modes(route_service, origin_destination):
    origin, destination = origin_destination
    edges = gpd.GeoDataFrame({

        "geometry": [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])],
        "edge_id": [1, 2],
        "length_m": [100, 150],
        "aqi": [20, 40],
        "tile_id": ["t101", "t102"]
    }, crs="EPSG:25833")

    result = route_service._compute_routes(edges, origin, destination)
    assert "routes" in result and "summaries" in result
    for mode in ["fastest", "best_aq", "balanced"]:
        assert mode in result["routes"]


def test_compute_routes_single_edge(route_service, origin_destination):
    origin, destination = origin_destination
    edge = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "edge_id": [1],
        "length_m": [100],
        "aqi": [20],
        "tile_id": ["t101"]
    }, crs="EPSG:25833")

    result = route_service._compute_routes(edge, origin, destination)
    assert "routes" in result and "summaries" in result


def test_get_route_returns_expected_structure(monkeypatch, route_service, origin_destination):
    origin, destination = origin_destination

    monkeypatch.setattr(route_service, "_get_tile_edges", lambda ids: gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])],
        "edge_id": [1, 2],
        "length_m": [100, 150],
        "aqi": [20, 40],
        "tile_id": ["t101", "t102"]
    }, crs="EPSG:25833"))

    result = route_service.get_route(origin, destination)
    assert "routes" in result and "summaries" in result
    for mode in ["fastest", "best_aq", "balanced"]:
        assert mode in result["routes"]
        assert result["routes"][mode]["features"]
