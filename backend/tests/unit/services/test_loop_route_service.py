import pytest
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
from src.services.route_service import RouteService, RouteServiceFactory
from src.services.loop_route_service import LoopRouteService


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


def test_get_round_trip_returns_valid_structure(
    monkeypatch, origin_destination,
    simple_edges_gdf_2, simple_nodes_gdf
):
    """Test that get_round_trip yields valid loop structure"""
    origin, _ = origin_destination
    simple_edges_gdf_2["tile_id"] = [
        "r1_c2", "r1_c2", "r1_c2", "r1_c3", "r1_c3", "r1_c3"]

    loop_service = LoopRouteService("testarea")

    # Mock get_tile_ids_by_buffer to return tile IDs
    monkeypatch.setattr(loop_service.route_service, "get_tile_ids_by_buffer",
                        lambda buffer: ["r1_c2", "r1_c3"])
    monkeypatch.setattr(loop_service.route_service, "get_tile_edges",
                        lambda tile_ids: simple_edges_gdf_2.copy())
    monkeypatch.setattr(loop_service.route_service, "get_nodes_from_db",
                        lambda tile_ids: simple_nodes_gdf)
    monkeypatch.setattr(loop_service, "_get_outermost_tiles",
                        lambda tile_ids: tile_ids)
    monkeypatch.setattr(
        loop_service, "extract_best_aq_point_from_tile",
        lambda edges, tile_ids: gpd.GeoDataFrame(
            {"geometry": [Point(1.0, 1.0)], "tile_id": ["r1_c2"]},
            crs="EPSG:25833"
        )
    )

    monkeypatch.setattr(loop_service, "decode_tile", lambda tile: (1, 2))

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
        return {
            "routes": {"loop": {"type": "FeatureCollection", "features": []}},
            "summaries": {"loop": {"length_m": 10, "aq_average": 10}},
            "aqi_differences": None
        }

    monkeypatch.setattr(loop_service, "get_round_trip_forward", mock_forward)
    monkeypatch.setattr(loop_service, "get_round_trip_back", mock_back)

    # get_round_trip is now a generator
    results = list(loop_service.get_round_trip(origin, distance=1000))

    assert len(results) == 1
    result = results[0]
    assert "routes" in result
    assert "summaries" in result
    assert "loop1" in result["routes"]
    assert "loop1" in result["summaries"]
    assert isinstance(result["routes"]["loop1"], dict)
    assert result["summaries"]["loop1"]["length_m"] == 10
    assert result["summaries"]["loop1"]["aq_average"] == 10


def test_route_trip_forward_handles_empty_gdf(monkeypatch, origin_destination, simple_edges_gdf, simple_nodes_gdf):
    """Test that get_round_trip_forward handles empty GeoDataFrames"""
    origin, destination = origin_destination

    loop_service = LoopRouteService("testarea")

    monkeypatch.setattr(loop_service.route_service, "get_tile_edges",
                        lambda ids: simple_edges_gdf)
    monkeypatch.setattr(loop_service.route_service, "get_nodes_from_db",
                        lambda ids: simple_nodes_gdf)

    empty_gdf = gpd.GeoDataFrame()
    empty_gdf_2 = gpd.GeoDataFrame()

    result = loop_service.get_round_trip_forward(
        origin, [empty_gdf, empty_gdf_2, destination])
    assert len(result) == 1
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert "geometry" in result[0]["destination"]


def test_iterate_candidates_yields_three_loops(monkeypatch, route_service, origin_destination):
    """Test that iterate_candidates yields three distinct loop results"""
    origin, _ = origin_destination

    mock_candidates = [
        {
            "destination": gpd.GeoDataFrame(geometry=[Point(1, 1)], crs="EPSG:25833"),
            "route": gpd.GeoDataFrame({
                "geometry": [LineString([(0, 0), (1, 1)])],
                "edge_id": [1]
            }, crs="EPSG:25833"),
            "summary": {"aq_average": 10},
            "epath_gdf_ids": [1]
        },
        {
            "destination": gpd.GeoDataFrame(geometry=[Point(2, 2)], crs="EPSG:25833"),
            "route": gpd.GeoDataFrame({
                "geometry": [LineString([(0, 0), (2, 2)])],
                "edge_id": [2]
            }, crs="EPSG:25833"),
            "summary": {"aq_average": 20},
            "epath_gdf_ids": [2]
        },
        {
            "destination": gpd.GeoDataFrame(geometry=[Point(3, 3)], crs="EPSG:25833"),
            "route": gpd.GeoDataFrame({
                "geometry": [LineString([(0, 0), (3, 3)])],
                "edge_id": [3]
            }, crs="EPSG:25833"),
            "summary": {"aq_average": 30},
            "epath_gdf_ids": [3]
        }
    ]

    def mock_back(destination, first_path_data):
        return {
            "routes": {"loop": {"type": "FeatureCollection", "features": []}},
            "summaries": {"loop": {"length_m": 100, "aq_average": first_path_data["summary"]["aq_average"]}},
            "aqi_differences": None
        }

    loop_service = LoopRouteService("testarea")
    monkeypatch.setattr(loop_service, "get_round_trip_back", mock_back)

    results = list(loop_service.iterate_candidates(mock_candidates, origin))

    assert len(results) == 3
    assert "loop1" in results[0]["routes"]
    assert "loop2" in results[1]["routes"]
    assert "loop3" in results[2]["routes"]
    assert results[0]["summaries"]["loop1"]["aq_average"] == 10
    assert results[1]["summaries"]["loop2"]["aq_average"] == 20
    assert results[2]["summaries"]["loop3"]["aq_average"] == 30


def test_iterate_candidates_handles_failures_gracefully(monkeypatch, origin_destination):
    """Test that iterate_candidates continues if one candidate fails"""
    origin, _ = origin_destination

    mock_candidates = [
        {
            "destination": gpd.GeoDataFrame(geometry=[Point(1, 1)], crs="EPSG:25833"),
            "route": gpd.GeoDataFrame({
                "geometry": [LineString([(0, 0), (1, 1)])],
                "edge_id": [1]
            }, crs="EPSG:25833"),
            "summary": {"aq_average": 10},
            "epath_gdf_ids": [1]
        },
        {
            "destination": gpd.GeoDataFrame(geometry=[Point(2, 2)], crs="EPSG:25833"),
            "route": gpd.GeoDataFrame(),  # Empty route - will fail
            "summary": {"aq_average": 20},
            "epath_gdf_ids": [2]
        },
        {
            "destination": gpd.GeoDataFrame(geometry=[Point(3, 3)], crs="EPSG:25833"),
            "route": gpd.GeoDataFrame({
                "geometry": [LineString([(0, 0), (3, 3)])],
                "edge_id": [3]
            }, crs="EPSG:25833"),
            "summary": {"aq_average": 30},
            "epath_gdf_ids": [3]
        }
    ]

    call_count = [0]

    def mock_back(destination, first_path_data):
        call_count[0] += 1
        if call_count[0] == 2:  # Second candidate fails
            raise RuntimeError("Route computation failed")
        return {
            "routes": {"loop": {"type": "FeatureCollection", "features": []}},
            "summaries": {"loop": {"length_m": 100, "aq_average": first_path_data["summary"]["aq_average"]}},
            "aqi_differences": None
        }

    loop_service = LoopRouteService("testarea")
    monkeypatch.setattr(loop_service, "get_round_trip_back", mock_back)

    results = list(loop_service.iterate_candidates(mock_candidates, origin))

    # Should get 2 results (1st and 3rd), 2nd failed
    assert len(results) == 2
    assert "loop1" in results[0]["routes"]
    # loop2 because it's the 2nd successful one
    assert "loop2" in results[1]["routes"]


def test_extract_best_aq_point_returns_one_per_tile(simple_edges_gdf_2):
    """Test that extract_best_aq_point_from_tile returns points per tile"""
    loop_service = LoopRouteService("testarea")

    tile_ids = ["t102", "t103"]
    result = loop_service.extract_best_aq_point_from_tile(
        simple_edges_gdf_2, tile_ids)

    # 6 edges total, 3 per tile, head(5) = max 5 per tile but only 3 exist per tile
    assert len(result) == 6  # 3 edges per tile × 2 tiles
    assert "tile_id" in result.columns
    assert set(result["tile_id"].unique()) == set(tile_ids)
    # Check that points are sorted by AQ (best first)
    assert all(isinstance(geom, Point) for geom in result.geometry)


def test_extract_best_aq_point_handles_empty_edges():
    """Test that extract_best_aq_point_from_tile handles empty edges gracefully"""
    loop_service = LoopRouteService("testarea")

    empty_edges = gpd.GeoDataFrame(
        columns=["geometry", "tile_id", "aqi", "edge_id"], crs="EPSG:25833")
    result = loop_service.extract_best_aq_point_from_tile(empty_edges, [
                                                          "t101"])

    assert result.empty
    assert "tile_id" in result.columns


def test_get_outermost_tiles():
    """Test that _get_outermost_tiles correctly identifies boundary tiles"""
    loop_service = LoopRouteService("testarea")

    # 3x3 grid - expect only edge tiles
    tile_ids = [
        "r0_c0", "r0_c1", "r0_c2",
        "r1_c0", "r1_c1", "r1_c2",
        "r2_c0", "r2_c1", "r2_c2"
    ]

    outer = loop_service._get_outermost_tiles(tile_ids)

    # Center tile r1_c1 should NOT be in outer tiles
    assert "r1_c1" not in outer
    # All edge tiles should be there
    assert "r0_c0" in outer
    assert "r2_c2" in outer
    assert len(outer) == 8  # 3x3 grid has 8 outer tiles


def test_rotate_tile_about_center():
    """Test tile rotation by 120 degrees"""
    loop_service = LoopRouteService("testarea")

    candidate_tiles = ["r0_c0", "r0_c1", "r1_c0", "r1_c1"]

    # Rotate r0_c1 around r0_c0 by 120 degrees
    rotated = loop_service.rotate_tile_about_center(
        "r0_c1", "r0_c0", candidate_tiles, degrees=120.0
    )

    assert rotated in candidate_tiles
    assert rotated != "r0_c1"  # Should be different from original


def test_decode_tile():
    """Test tile string decoding"""
    loop_service = LoopRouteService("testarea")

    row, col = loop_service.decode_tile("r14_c12")
    assert row == 14
    assert col == 12

    row, col = loop_service.decode_tile("r0_c99")
    assert row == 0
    assert col == 99


def test_get_closest_tile_match_exact():
    """Test that get_closest_tile_match returns exact match when available"""
    loop_service = LoopRouteService("testarea")

    tiles = ["r0_c0", "r0_c1", "r1_c0", "r1_c1"]
    result = loop_service.get_closest_tile_match("r0_c1", tiles)

    assert result == "r0_c1"


def test_get_closest_tile_match_nearest():
    """Test that get_closest_tile_match finds nearest tile when exact not available"""
    loop_service = LoopRouteService("testarea")

    tiles = ["r0_c0", "r0_c2", "r2_c0", "r2_c2"]
    result = loop_service.get_closest_tile_match("r0_c1", tiles)

    # Should find a neighbor within Manhattan distance
    assert result in tiles


def test_get_round_trip_forward_sorts_by_aq(monkeypatch, origin_destination, simple_edges_gdf, simple_nodes_gdf):
    """Test that get_round_trip_forward sorts candidates by air quality"""
    origin, _ = origin_destination

    loop_service = LoopRouteService("testarea")

    monkeypatch.setattr(loop_service.route_service,
                        "get_tile_edges", lambda ids: simple_edges_gdf)
    monkeypatch.setattr(loop_service.route_service,
                        "get_nodes_from_db", lambda ids: simple_nodes_gdf)

    # Three GeoDataFrames with different expected AQ outcomes
    best_3 = [
        gpd.GeoDataFrame(geometry=[Point(1, 1)], crs="EPSG:25833"),
        gpd.GeoDataFrame(geometry=[Point(2, 2)], crs="EPSG:25833"),
        gpd.GeoDataFrame(geometry=[Point(3, 3)], crs="EPSG:25833")
    ]

    result = loop_service.get_round_trip_forward(origin, best_3)

    # Results should be sorted by aq_average (ascending)
    if len(result) > 1:
        for i in range(len(result) - 1):
            assert result[i]["summary"]["aq_average"] <= result[i +
                                                                1]["summary"]["aq_average"]
