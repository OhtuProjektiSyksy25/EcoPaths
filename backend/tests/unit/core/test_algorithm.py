import pytest
import geopandas as gpd
from shapely.geometry import LineString
from src.core.algorithm.route_algorithm import RouteAlgorithm

# --- Fixtures ---


@pytest.fixture
def simple_edges():
    """
    Create a simple GeoDataFrame with two connected LineString edges.

    Returns:
        GeoDataFrame: GeoDataFrame with two LineString edges.
    """
    lines = [
        LineString([(0.0, 0.0), (1.0, 0.0)]),
        LineString([(1.0, 0.0), (2.0, 0.0)])
    ]
    gdf = gpd.GeoDataFrame(
        {
            "geometry": lines,
            "length_m": [line.length for line in lines],
        },
        crs="EPSG:4326"
    )
    return gdf


@pytest.fixture
def square_edges():
    """
    Create a square loop of LineString edges.

    Returns:
        GeoDataFrame: GeoDataFrame with four LineString edges forming a square.
    """
    lines = [
        LineString([(0.0, 0.0), (1.0, 0.0)]),
        LineString([(1.0, 0.0), (1.0, 1.0)]),
        LineString([(1.0, 1.0), (0.0, 1.0)]),
        LineString([(0.0, 1.0), (0.0, 0.0)])
    ]
    gdf = gpd.GeoDataFrame(
        {
            "geometry": lines,
            "length_m": [line.length for line in lines],
        },
        crs="EPSG:4326"
    )
    return gdf


# --- Tests ---

def test_simple_path(simple_edges):
    """
    Test a simple straight path from (0,0) to (2,0).

    Args:
        simple_edges (GeoDataFrame): Fixture with simple edges.
    """
    algo = RouteAlgorithm(simple_edges)
    origin = (0, 0)
    dest = (2, 0)
    gdf = algo.calculate(origin, dest)

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 1
    line = gdf.geometry.iloc[0]

    print("Line coords:", list(line.coords))
    print("Graph nodes:", list(algo.graph.nodes))
    print("Graph edges:", list(algo.graph.edges))

    assert list(line.coords) == [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]


def test_square_path(square_edges):
    """
    Test a path around a square from (0,0) to (1,1).

    Args:
        square_edges (GeoDataFrame): Fixture with square edges.
    """
    algo = RouteAlgorithm(square_edges)
    origin = (0, 0)
    dest = (1, 1)
    gdf = algo.calculate(origin, dest)

    coords = list(gdf.geometry.iloc[0].coords)
    assert coords in [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 1)]
    ]


def test_invalid_origin(square_edges):
    """
    Test handling of an origin point outside the graph.

    Args:
        square_edges (GeoDataFrame): Fixture with square edges.
    """
    algo = RouteAlgorithm(square_edges)

    origin = (100, 100)
    dest = (0, 0)

    gdf = algo.calculate(origin, dest)
    assert not gdf.empty

    coords = list(gdf.geometry.iloc[0].coords)
    assert coords[0] in [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def test_project_point_identity_projection(simple_edges):
    """Test projection with same CRS (EPSG:4326 -> EPSG:4326)."""
    algo = RouteAlgorithm(simple_edges)
    algo.edges_crs = "EPSG:4326"
    point = (12.0, 55.0)
    projected = algo._project_point(point)

    assert pytest.approx(projected[0], rel=1e-9) == 12.0
    assert pytest.approx(projected[1], rel=1e-9) == 55.0


def test_nearest_node_basic(simple_edges):
    """Finds nearest node correctly."""
    algo = RouteAlgorithm(simple_edges)
    nodes = {(0, 0), (10, 10), (5, 5)}
    point = (6, 5)
    nearest = algo._nearest_node(nodes, point)
    assert nearest == (5, 5)
