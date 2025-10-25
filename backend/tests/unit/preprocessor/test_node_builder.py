import pytest
import geopandas as gpd
from shapely.geometry import LineString

from preprocessor.node_builder import NodeBuilder
from src.database.db_client import DatabaseClient


@pytest.fixture
def db():
    return DatabaseClient()


@pytest.fixture
def area():
    return "testarea"


@pytest.fixture
def network_type():
    return "walking"


@pytest.fixture
def mock_edges(db, area, network_type):
    edge_table = f"edges_{area}_{network_type}"
    db.execute(f"DROP TABLE IF EXISTS {edge_table};")

    gdf = gpd.GeoDataFrame({
        "edge_id": [1, 2],
        "tile_id": ["A", "B"],
        "length_m": [1.41, 1.41],
        "from_node": [None, None],
        "to_node": [None, None],
        "geometry": [
            LineString([(0, 0), (1, 1)]),
            LineString([(1, 1), (2, 2)])
        ]
    }, geometry="geometry", crs="EPSG:4326")

    gdf.to_postgis(edge_table, db.engine, if_exists="replace", index=False)

    return edge_table


def test_node_table_created(db, area, network_type, mock_edges):
    builder = NodeBuilder(db, area, network_type)
    builder.build_nodes_and_attach_to_edges()

    assert db.table_exists(f"nodes_{area}_{network_type}")


def test_edge_table_has_node_columns(db, area, network_type, mock_edges):
    builder = NodeBuilder(db, area, network_type)
    builder.build_nodes_and_attach_to_edges()

    result = db.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'edges_{area}_{network_type}'
    """)
    columns = [row[0] for row in result.fetchall()]
    assert "from_node" in columns
    assert "to_node" in columns


def test_node_ids_are_assigned(db, area, network_type, mock_edges):
    builder = NodeBuilder(db, area, network_type)
    builder.build_nodes_and_attach_to_edges()

    result = db.execute(f"""
        SELECT COUNT(*) FROM edges_{area}_{network_type}
        WHERE from_node IS NOT NULL AND to_node IS NOT NULL
    """)
    count = result.scalar()
    assert count > 0


def test_node_count_matches_endpoints(db, area, network_type, mock_edges):
    builder = NodeBuilder(db, area, network_type)
    builder.build_nodes_and_attach_to_edges()

    result = db.execute(f"SELECT COUNT(*) FROM nodes_{area}_{network_type}")
    node_count = result.scalar()

    assert node_count == 3


def test_node_geometry_is_unique(db, area, network_type, mock_edges):
    builder = NodeBuilder(db, area, network_type)
    builder.build_nodes_and_attach_to_edges()

    result = db.execute(f"""
        SELECT COUNT(*) - COUNT(DISTINCT geometry)
        FROM nodes_{area}_{network_type}
    """)
    duplicates = result.scalar()
    assert duplicates == 0


def test_edge_geometry_preserved(db, area, network_type, mock_edges):
    builder = NodeBuilder(db, area, network_type)

    # Tallenna alkuperäinen geometria
    original = db.execute(f"""
        SELECT ST_AsText(geometry) FROM edges_{area}_{network_type}
        ORDER BY edge_id
    """).fetchall()

    builder.build_nodes_and_attach_to_edges()

    updated = db.execute(f"""
        SELECT ST_AsText(geometry) FROM edges_{area}_{network_type}
        ORDER BY edge_id
    """).fetchall()

    assert original == updated


def test_edge_row_count_unchanged(db, area, network_type, mock_edges):
    before = db.execute(
        f"SELECT COUNT(*) FROM edges_{area}_{network_type}").scalar()

    builder = NodeBuilder(db, area, network_type)
    builder.build_nodes_and_attach_to_edges()

    after = db.execute(
        f"SELECT COUNT(*) FROM edges_{area}_{network_type}").scalar()
    assert before == after
