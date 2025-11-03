import pytest
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.core.route_algorithm import RouteAlgorithm


@pytest.fixture
def simple_nodes_gdf():
    data = {
        "node_id": ["A", "B", "C", "D", "E", "F"],
        "tile_id": [1, 1, 1, 1, 1, 1],
        "geometry": [
            Point(1, 1),   # A
            Point(2, 2),   # B
            Point(3, 3),   # C
            Point(1, 2),   # D
            Point(3, 4),   # E
            Point(5, 5)    # F
        ]
    }

    return gpd.GeoDataFrame(data, crs="EPSG:25833")

@pytest.fixture
def simple_edges_gdf():
    data = {
        "edge_id": [1, 2, 3, 4, 5, 6],
        "from_node": ["A", "B", "D", "D", "E", "F"],
        "to_node": ["B", "C", "B", "E", "C", "C"],
        "length_m": [2.8, 2.8, 2.8, 2.8, 2.8, 4.0],  # approximate distances
        "normalized_aqi": [0.5, 0.2, 0.3, 0.4, 0.1, 0.6],
        "aqi": [20.0, 40.0, 30.0, 44.0, 50.0, 30.0],
        "geometry": [
            LineString([(1,1),(2,2)]),  # A -> B
            LineString([(2,2),(3,4)]),  # B -> E
            LineString([(2,2),(3,3)]),  # B -> C
            LineString([(3,3),(1,2)]),  # 
            LineString([(3,4,),(5,5)]),  # 
            LineString([(3,3),(5,5)])   # 
        ]
    }
    return gpd.GeoDataFrame(data, crs="EPSG:25833")

@pytest.fixture
def origin_destination():
    origin = gpd.GeoDataFrame(geometry=[Point(1, 1)], crs="EPSG:25833")
    destination = gpd.GeoDataFrame(geometry=[Point(5, 5)], crs="EPSG:25833")
    return origin, destination

@pytest.fixture
def algorithm(simple_edges_gdf, simple_nodes_gdf):
    return RouteAlgorithm(simple_edges_gdf, simple_nodes_gdf)


def test_snap_and_split_adds_vertice_and_edges(algorithm):
    point = Point(1.3, 1.3)
    start_vertices = len(algorithm.igraph.vs)
    start_edges = len(algorithm.igraph.es)

    algorithm.init_route_specific()
    snapped_coord = algorithm.snap_and_split(point, "origin")
    end_vertices = len(algorithm.igraph.vs)
    end_edges = len(algorithm.igraph.es)

    assert end_vertices == (start_vertices+1)
    assert end_edges == (start_edges+1)
    


def test_calculate_path_returns_edges(algorithm, origin_destination):
    origin, destination = origin_destination
    route = algorithm.calculate_path(origin, destination)
    print(route)
    assert isinstance(route, gpd.GeoDataFrame)
    assert len(route) == 3
    assert all(route.geometry.geom_type == "LineString")


def test_find_nearest_edge_returns_row(algorithm):
    algorithm.init_route_specific()
    point = Point(1.3, 1.3)
    edge_row = algorithm._find_nearest_edge(point)
    assert edge_row is not None
    assert edge_row.geometry.geom_type == "LineString"


def test_normalize_node_rounds_correctly():
    result = RouteAlgorithm._normalize_node((1.23456, 7.89123))
    assert result == (1.235, 7.891)