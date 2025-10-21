import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.core.route_algorithm import RouteAlgorithm


@pytest.fixture
def simple_edges():
    lines = [
        LineString([(0, 0), (1, 1)]),
        LineString([(1, 1), (2, 2)])
    ]
    return gpd.GeoDataFrame({
        "geometry": lines,
        "length_m": [1.414, 1.414],
        "edge_id": [0, 1]
    }, crs="EPSG:3067")


@pytest.fixture
def algorithm(simple_edges):
    return RouteAlgorithm(simple_edges)


def test_snap_and_split_returns_two_parts(algorithm):
    point = Point(0.5, 0.5)
    snapped_coord, split_edges = algorithm.snap_and_split(point)
    assert isinstance(snapped_coord, tuple)
    assert len(split_edges) == 2
    for geom in split_edges.geometry:
        assert geom.geom_type == "LineString"


def test_build_graph_has_correct_nodes_and_edges(algorithm):
    G = algorithm.build_graph()
    assert len(G.nodes) == 3
    assert len(G.edges) == 2


def test_calculate_path_returns_edges(algorithm):
    origin = gpd.GeoDataFrame(geometry=[Point(0.1, 0.1)], crs="EPSG:3067")
    destination = gpd.GeoDataFrame(geometry=[Point(1.9, 1.9)], crs="EPSG:3067")
    route = algorithm.calculate_path(origin, destination)
    assert isinstance(route, gpd.GeoDataFrame)
    assert len(route) == 2
    assert all(route.geometry.geom_type == "LineString")


def test_find_nearest_edge_returns_row(algorithm):
    point = Point(0.5, 0.5)
    edge_row = algorithm._find_nearest_edge(point)
    assert edge_row is not None
    assert edge_row.geometry.geom_type == "LineString"


def test_normalize_node_rounds_correctly():
    result = RouteAlgorithm._normalize_node((1.23456, 7.89123))
    assert result == (1.235, 7.891)


def test_euclidean_heuristic_returns_distance():
    dist = RouteAlgorithm.euclidean_heuristic((0, 0), (3, 4))
    assert dist == pytest.approx(5.0)
