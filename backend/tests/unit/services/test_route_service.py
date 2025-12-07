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
        "node_id": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "tile_id": [1, 1, 1, 1, 1, 1, 1, 1],
        "geometry": [
            Point(0, 0), Point(2, 2), Point(4, 4),
            Point(0, 2), Point(2, 4), Point(4, 0),
            Point(35, 35), Point(36, 36)
        ]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:25833")


@pytest.fixture
def simple_edges_gdf():
    data = {
        "edge_id": [1, 2, 3, 4, 5, 6, 7],
        "from_node": ["A", "B", "D", "D", "E", "F", "G"],
        "to_node": ["B", "C", "B", "E", "C", "C", "H"],
        "length_m": [2.8, 2.8, 2.8, 2.8, 2.8, 4.0, 1],
        "normalized_aqi": [0.5, 0.2, 0.3, 0.4, 0.1, 0.6, 1],
        "aqi": [20.0, 40.0, 30.0, 44.0, 50.0, 30.0, 1],
        "pm2_5": [10.0, 12.0, 11.0, 13.0, 14.0, 15.0, 1],
        "pm10": [20.0, 22.0, 21.0, 23.0, 24.0, 25.0, 1],
        "geometry": [
            LineString([(0, 0), (2, 2)]),
            LineString([(2, 2), (4, 4)]),
            LineString([(0, 2), (2, 2)]),
            LineString([(0, 2), (2, 4)]),
            LineString([(2, 4), (4, 4)]),
            LineString([(4, 0), (4, 4)]),
            LineString([(35, 35), (36, 36)])
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
    buffer = route_service.create_buffer(origin, destination, buffer_m=100)
    assert buffer.geom_type == "Polygon"
    assert buffer.area > 0


def test_get_tile_edges_returns_expected_data(route_service):
    tile_ids = ["t101", "t102", "t103"]
    result = route_service.get_tile_edges(tile_ids)
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
    edges = route_service.get_tile_edges(tile_ids)
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

    _ = route_service.get_tile_edges(["t104", "t106"])
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

    monkeypatch.setattr(route_service, "get_tile_edges",
                        lambda ids: simple_edges_gdf)
    monkeypatch.setattr(route_service, "get_nodes_from_db",
                        lambda ids: simple_nodes_gdf)

    result = route_service.get_route(origin, destination)
    assert "routes" in result and "summaries" in result
    for mode in ["fastest", "best_aq", "balanced"]:
        assert mode in result["routes"]
        assert result["routes"][mode]["features"]


def test_compute_balanced_route_only_returns_only_one_route(
    monkeypatch, route_service, origin_destination, simple_edges_gdf, simple_nodes_gdf
):
    origin, destination = origin_destination

    monkeypatch.setattr(route_service, "get_tile_edges",
                        lambda ids: simple_edges_gdf)
    monkeypatch.setattr(route_service, "get_nodes_from_db",
                        lambda ids: simple_nodes_gdf)

    route_service.get_route(origin, destination)
    result = route_service.compute_balanced_route_only(0.1)

    assert isinstance(result, dict)
    assert isinstance(result["routes"], dict)
    assert result["routes"]["balanced"].get("type") == "FeatureCollection"


def test_compute_routes_raises_error_with_empty_edges(route_service, origin_destination, simple_nodes_gdf):
    """Test that _compute_routes raises RuntimeError when edges GeoDataFrame is empty."""
    origin, destination = origin_destination
    empty_edges = gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:25833")

    with pytest.raises(RuntimeError, match="Edges GeoDataFrame has no geometry column or is empty"):
        route_service._compute_routes(
            empty_edges, simple_nodes_gdf, origin, destination)


def test_compute_routes_raises_error_with_empty_nodes(route_service, origin_destination, simple_edges_gdf):
    """Test that _compute_routes raises RuntimeError when nodes GeoDataFrame is empty."""
    origin, destination = origin_destination
    empty_nodes = gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:25833")

    with pytest.raises(RuntimeError, match="Nodes GeoDataFrame has no geometry column or is empty"):
        route_service._compute_routes(
            simple_edges_gdf, empty_nodes, origin, destination)


def test_compute_routes_raises_error_without_geometry_column_in_edges(route_service, origin_destination, simple_nodes_gdf):
    """Test that _compute_routes raises RuntimeError when edges has no geometry column."""
    origin, destination = origin_destination
    # Create a regular DataFrame and convert to GeoDataFrame without geometry
    edges_without_geom = gpd.GeoDataFrame(pd.DataFrame({"edge_id": [1, 2]}))

    with pytest.raises(RuntimeError, match="Edges GeoDataFrame has no geometry column or is empty"):
        route_service._compute_routes(
            edges_without_geom, simple_nodes_gdf, origin, destination)


def test_compute_routes_raises_error_without_geometry_column_in_nodes(route_service, origin_destination, simple_edges_gdf):
    """Test that _compute_routes raises RuntimeError when nodes has no geometry column."""
    origin, destination = origin_destination
    # Create a regular DataFrame and convert to GeoDataFrame without geometry
    nodes_without_geom = gpd.GeoDataFrame(
        pd.DataFrame({"node_id": ["A", "B"]}))

    with pytest.raises(RuntimeError, match="Nodes GeoDataFrame has no geometry column or is empty"):
        route_service._compute_routes(
            simple_edges_gdf, nodes_without_geom, origin, destination)


def test_get_tile_edges_returns_empty_gdf_with_crs_when_no_tiles_found(monkeypatch, route_service):
    """Test that get_tile_edges returns empty GeoDataFrame with CRS when no tiles found."""
    monkeypatch.setattr(DummyRedisService, "prune_found_ids",
                        staticmethod(lambda ids, r, a: ids))
    monkeypatch.setattr(DummyRedisService, "get_gdf_by_list_of_keys",
                        staticmethod(lambda ids, r, a: (False, [])))

    def empty_enriched_tiles(self, tile_ids, network_type="walking"):
        return None

    monkeypatch.setattr(
        "src.services.route_service.EdgeEnricher.get_enriched_tiles", empty_enriched_tiles)

    result = route_service.get_tile_edges(["t999"])
    assert isinstance(result, gpd.GeoDataFrame)
    assert result.empty
    assert result.crs is not None
    assert result.crs.to_string() == "EPSG:25833"


def test_get_nodes_from_db_returns_empty_gdf_with_crs_when_no_nodes(monkeypatch, route_service):
    """Test that get_nodes_from_db returns empty GeoDataFrame with CRS when no nodes found."""
    monkeypatch.setattr("src.services.route_service.DatabaseClient.get_nodes_by_tile_ids",
                        lambda self, area, network, ids: None)

    result = route_service.get_nodes_from_db(["t999"])
    assert isinstance(result, gpd.GeoDataFrame)
    assert result.empty
    assert result.crs is not None
    assert result.crs.to_string() == "EPSG:25833"


def test_enrich_missing_edges_returns_empty_gdf_with_crs_on_failure(monkeypatch, route_service):
    """Test that _enrich_missing_edges returns empty GeoDataFrame with CRS when enrichment fails."""

    def failing_enrichment(self, tile_ids, network_type="walking"):
        return None

    monkeypatch.setattr(
        "src.services.route_service.EdgeEnricher.get_enriched_tiles", failing_enrichment)

    result = route_service._enrich_missing_edges(["t999"])
    assert isinstance(result, gpd.GeoDataFrame)
    assert result.empty
    assert result.crs is not None
    assert result.crs.to_string() == "EPSG:25833"


@pytest.mark.filterwarnings("ignore:Couldn't reach some vertices:RuntimeWarning")
def test_get_route_tries_multiple_buffer_sizes(monkeypatch, route_service, origin_destination, simple_edges_gdf, simple_nodes_gdf, caplog):
    """Test that get_route tries multiple buffer sizes (600m, 900m, 1200m) before failing."""
    origin, destination = origin_destination
    destination = gpd.GeoDataFrame(geometry=[Point(33, 33)], crs="EPSG:25833")

    monkeypatch.setattr(route_service, "get_tile_edges",
                        lambda ids: simple_edges_gdf)
    monkeypatch.setattr(route_service, "get_nodes_from_db",
                        lambda ids: simple_nodes_gdf)

    with pytest.raises(RuntimeError, match="No route found"):
        route_service.get_route(origin, destination)

    # Verify all three buffer sizes were attempted
    assert "600m" in caplog.text
    assert "900m" in caplog.text
    assert "1200m" in caplog.text
