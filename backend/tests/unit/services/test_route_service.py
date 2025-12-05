import pytest
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
from src.services.route_service import RouteService, RouteServiceFactory


class DummyRedisService:
    @staticmethod
    def prune_found_ids(tile_ids, redis, area_config):
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
            "pm2_5": [10.0] * len(tile_ids),
            "pm10": [20.0] * len(tile_ids)
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
        "normalized_aqi": [15.0, 42.0],
        "pm2_5": [10.0, 12.0],
        "pm10": [20.0, 22.0]
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
    origin = gpd.GeoDataFrame(geometry=[Point(1, 1)], crs="EPSG:25833")
    destination = gpd.GeoDataFrame(geometry=[Point(5, 5)], crs="EPSG:25833")
    return origin, destination


@pytest.fixture
def simple_nodes_gdf():
    data = {
        "node_id": ["A", "B", "C", "D", "E", "F"],
        "tile_id": [1, 1, 1, 1, 1, 1],
        "geometry": [
            Point(0, 0), Point(2, 2), Point(4, 4),
            Point(0, 2), Point(2, 4), Point(4, 0)
        ]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:25833")


@pytest.fixture
def simple_edges_gdf():
    data = {
        "edge_id": [1, 2, 3, 4, 5, 6],
        "from_node": ["A", "B", "D", "D", "E", "F"],
        "to_node": ["B", "C", "B", "E", "C", "C"],
        "length_m": [2.8, 2.8, 2.8, 2.8, 2.8, 4.0],
        "normalized_aqi": [0.5, 0.2, 0.3, 0.4, 0.1, 0.6],
        "aqi": [20.0, 40.0, 30.0, 44.0, 50.0, 30.0],
        "pm2_5": [10.0, 12.0, 11.0, 13.0, 14.0, 15.0],
        "pm10": [20.0, 22.0, 21.0, 23.0, 24.0, 25.0],
        "geometry": [
            LineString([(0, 0), (2, 2)]),
            LineString([(2, 2), (4, 4)]),
            LineString([(0, 2), (2, 2)]),
            LineString([(0, 2), (2, 4)]),
            LineString([(2, 4), (4, 4)]),
            LineString([(4, 0), (4, 4)])
        ]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:25833")


@pytest.fixture
def simple_edges_gdf_2():
    data = {
        "edge_id": [1, 2, 3, 4, 5, 6],
        "from_node": ["A", "B", "D", "D", "E", "F"],
        "to_node": ["B", "C", "B", "E", "C", "C"],
        "length_m": [2.8, 2.8, 2.8, 2.8, 2.8, 4.0],
        "normalized_aqi": [0.5, 0.2, 0.3, 0.4, 0.1, 0.6],
        "aqi": [20.0, 40.0, 30.0, 44.0, 50.0, 30.0],
        "pm2_5": [10.0, 12.0, 11.0, 13.0, 14.0, 15.0],
        "pm10": [20.0, 22.0, 21.0, 23.0, 24.0, 25.0],
        "tile_id": ["t102", "t102", "t102", "t103", "t103", "t103"],
        "geometry": [
            LineString([(0, 0), (2, 2)]),
            LineString([(2, 2), (4, 4)]),
            LineString([(0, 2), (2, 2)]),
            LineString([(0, 2), (2, 4)]),
            LineString([(2, 4), (4, 4)]),
            LineString([(4, 0), (4, 4)])
        ]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:25833")


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
    assert "pm2_5" in result.columns
    assert "pm10" in result.columns
    assert all(tid in tile_ids for tid in result["tile_id"])
    assert result.crs.to_string() == "EPSG:25833"


def test_prune_and_fetch_combines_correctly(monkeypatch, route_service):
    monkeypatch.setattr(DummyRedisService, "prune_found_ids",
                        staticmethod(lambda ids, r, a: ["t102", "t103"]))
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
                        staticmethod(lambda ids, r, a: ids))
    monkeypatch.setattr(DummyRedisService, "save_gdf",
                        staticmethod(fake_save_gdf))

    _ = route_service._get_tile_edges(["t104", "t106"])
    assert called.get("was_called", False)


def test_compute_routes_returns_all_modes(route_service, origin_destination, simple_edges_gdf, simple_nodes_gdf):
    origin, destination = origin_destination
    result = route_service._compute_routes(
        simple_edges_gdf, simple_nodes_gdf, origin, destination)
    assert "routes" in result and "summaries" in result
    for mode in ["fastest", "best_aq", "balanced"]:
        assert mode in result["routes"]
        assert result["routes"][mode]["features"]


def test_compute_routes_single_edge(route_service, origin_destination, simple_edges_gdf, simple_nodes_gdf):
    origin, destination = origin_destination
    result = route_service._compute_routes(
        simple_edges_gdf, simple_nodes_gdf, origin, destination)
    assert "routes" in result and "summaries" in result


def test_get_route_returns_expected_structure(monkeypatch, route_service, origin_destination, simple_edges_gdf, simple_nodes_gdf):
    origin, destination = origin_destination

    monkeypatch.setattr(route_service, "_get_tile_edges",
                        lambda ids: simple_edges_gdf)
    monkeypatch.setattr(route_service, "_get_nodes_from_db",
                        lambda ids: simple_nodes_gdf)

    result = route_service.get_route(origin, destination)
    assert "routes" in result and "summaries" in result
    for mode in ["fastest", "best_aq", "balanced"]:
        assert mode in result["routes"]
        assert result["routes"][mode]["features"]


def test_get_round_trip_returns_valid_structure(
    monkeypatch, route_service, origin_destination,
    simple_edges_gdf_2, simple_nodes_gdf
):
    origin, _ = origin_destination
    simple_edges_gdf_2["tile_id"] = [
        "r1_c2", "r1_c2", "r1_c2", "r1_c3", "r1_c3", "r1_c3"]

    monkeypatch.setattr(route_service, "_get_tile_edges",
                        lambda tile_ids: simple_edges_gdf_2.copy())
    monkeypatch.setattr(route_service, "_get_nodes_from_db",
                        lambda tile_ids: simple_nodes_gdf)
    monkeypatch.setattr(route_service, "_get_outermost_tiles",
                        lambda tile_ids: tile_ids)
    monkeypatch.setattr(
        route_service, "extract_best_aq_point_from_tile",
        lambda edges, tile_ids: gpd.GeoDataFrame(
            {"geometry": [Point(1.0, 1.0)], "tile_id": ["r1_c2"]},
            crs="EPSG:25833"
        )
    )

    monkeypatch.setattr(route_service, "decode_tile", lambda tile: (1, 2))

    def mock_forward(origin_gdf, best_3):
        return [
            {
                "destination": gpd.GeoDataFrame(geometry=[Point(1.3, 1.4)], crs="EPSG:25833"),
                "route": gpd.GeoDataFrame({
                    "geometry": [LineString([(0.1, 0.2), (1.3, 1.4)])],
                    "edge_id": [1]
                }, crs="EPSG:25833"),
                "summary": {"aq_average": 10},
                "epath_gdf_ids": [1]
            }
        ]

    def mock_back(destination, first_path_data):
        combined_gdf = pd.concat([first_path_data["route"]], ignore_index=True)
        return {
            "routes": {"loop": {"type": "FeatureCollection", "features": []}},
            "summaries": {"loop": {"length_m": 10, "aq_average": 10}},
            "aqi_differences": None
        }

    monkeypatch.setattr(route_service, "get_round_trip_forward", mock_forward)
    monkeypatch.setattr(route_service, "get_round_trip_back", mock_back)

    result = route_service.get_round_trip(origin, distance=1000)

    assert "routes" in result
    assert "summaries" in result
    assert "loop" in result["routes"]
    assert "loop" in result["summaries"]
    assert isinstance(result["routes"]["loop"], dict)
    assert result["summaries"]["loop"]["length_m"] == 10
    assert result["summaries"]["loop"]["aq_average"] == 10


def test_compute_balanced_route_only_returns_only_one_route(
    monkeypatch, route_service, origin_destination, simple_edges_gdf, simple_nodes_gdf
):
    origin, destination = origin_destination

    monkeypatch.setattr(route_service, "_get_tile_edges",
                        lambda ids: simple_edges_gdf)
    monkeypatch.setattr(route_service, "_get_nodes_from_db",
                        lambda ids: simple_nodes_gdf)

    route_service.get_route(origin, destination)
    result = route_service.compute_balanced_route_only(0.1)

    assert isinstance(result, dict)
    assert isinstance(result["routes"], dict)
    assert result["routes"]["balanced"].get("type") == "FeatureCollection"


def test_route_trip_forward_handles_empty_gdf(monkeypatch, route_service, origin_destination, simple_edges_gdf, simple_nodes_gdf):
    origin, destination = origin_destination

    monkeypatch.setattr(route_service, "_get_tile_edges",
                        lambda ids: simple_edges_gdf)
    monkeypatch.setattr(route_service, "_get_nodes_from_db",
                        lambda ids: simple_nodes_gdf)

    empty_gdf = gpd.GeoDataFrame()
    empty_gdf_2 = gpd.GeoDataFrame()

    result = route_service.get_round_trip_forward(
        origin, [empty_gdf, empty_gdf_2, destination],)
    assert len(result) == 1
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert "geometry" in result[0]["destination"]
