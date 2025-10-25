import pytest
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, GeometryCollection, Point
from src.database.db_client import DatabaseClient
from preprocessor.edge_cleaner_sql import EdgeCleanerSQL


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
def setup_mock_edges(db, area, network_type):
    table = f"edges_{area}_{network_type}"
    db.execute(f"DROP TABLE IF EXISTS {table};")

    gdf = gpd.GeoDataFrame({
        "edge_id": [1, 2, 3, 4, 5],
        "access": ["yes", "private", "permissive", "no", None],
        "length_m": [None] * 5,
        "tile_id": [None] * 5,
        "geometry": [
            LineString([(0, 0), (1, 1)]),
            LineString([(1, 1), (2, 2)]),
            MultiLineString([[(2, 2), (3, 3)], [(3, 3), (4, 4)]]),
            GeometryCollection([LineString([(4, 4), (5, 5)]), Point(6, 6)]),
            Point(7, 7)
        ]
    }, geometry="geometry", crs="EPSG:4326")

    gdf.to_postgis(table, db.engine, if_exists="replace", index=False)
    return table


def test_filter_access(db, area, network_type, setup_mock_edges):
    cleaner = EdgeCleanerSQL(db)
    cleaner.filter_access(area, network_type)

    result = db.execute(f"""
        SELECT COUNT(*) FROM {setup_mock_edges}
        WHERE access NOT IN ('yes', 'permissive') AND access IS NOT NULL
    """)
    assert result.scalar() == 0


def test_compute_lengths(db, area, network_type, setup_mock_edges):
    cleaner = EdgeCleanerSQL(db)
    cleaner.compute_lengths(area, network_type)

    result = db.execute(f"""
        SELECT COUNT(*) FROM {setup_mock_edges}
        WHERE length_m IS NOT NULL
    """)
    assert result.scalar() > 0


def test_normalize_geometry(db, area, network_type, setup_mock_edges):
    cleaner = EdgeCleanerSQL(db)
    cleaner.normalize_geometry(area, network_type)

    result = db.execute(f"""
        SELECT COUNT(*) FROM {setup_mock_edges}
        WHERE GeometryType(geometry) NOT IN ('LINESTRING')
    """)
    assert result.scalar() == 0


def test_drop_invalid_geometries(db, area, network_type):
    table = f"edges_{area}_{network_type}"
    db.execute(f"DROP TABLE IF EXISTS {table};")
    db.execute(f"""
        CREATE TABLE {table} AS
        SELECT 1 AS edge_id, NULL::geometry AS geometry
        UNION ALL
        SELECT 2, ST_GeomFromText('LINESTRING(0 0, 1 1)')
    """)

    cleaner = EdgeCleanerSQL(db)
    cleaner.drop_invalid_geometries(area, network_type)

    result = db.execute(f"SELECT COUNT(*) FROM {table}")
    assert result.scalar() == 1
