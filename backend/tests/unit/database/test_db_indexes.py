import pytest
import geopandas as gpd
from shapely.geometry import LineString, Polygon, Point
from sqlalchemy import text
from src.database.db_client import DatabaseClient
from src.config.settings import AREA_SETTINGS
from src.database.db_indexes import (
    create_edge_indexes,
    create_grid_indexes,
    create_node_indexes,
    create_green_indexes,
)


class TestDatabaseIndexes:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea_idx"
        cls.edge_table = f"edges_{cls.area}_walking"
        cls.grid_table = f"grid_{cls.area}"
        cls.node_table = f"nodes_{cls.area}_walking"
        cls.green_table = f"green_{cls.area}"

        if cls.area not in AREA_SETTINGS:
            AREA_SETTINGS[cls.area] = AREA_SETTINGS["testarea"]

        # Drop old tables
        for t in [cls.edge_table, cls.grid_table, cls.node_table, cls.green_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

        # Create minimal tables with geometry columns
        gdf_edges = gpd.GeoDataFrame({
            "edge_id": [1],
            "from_node": [100],
            "to_node": [101],
            "tile_id": ["T1"],
            "geometry": [LineString([(0, 0), (1, 1)])]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_edges.to_postgis(cls.edge_table, cls.db.engine,
                             if_exists="replace", index=False)

        gdf_grid = gpd.GeoDataFrame({
            "tile_id": [1],
            "geometry": [Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_grid.to_postgis(cls.grid_table, cls.db.engine,
                            if_exists="replace", index=False)

        gdf_nodes = gpd.GeoDataFrame({
            "node_id": [100],
            "tile_id": ["T1"],
            "geometry": [Point(0, 0)]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_nodes.to_postgis(cls.node_table, cls.db.engine,
                             if_exists="replace", index=False)

        gdf_green = gpd.GeoDataFrame({
            "land_id": [1],
            "green_type": ["park"],
            "tile_id": ["T1"],
            "geometry": [Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_green.to_postgis(cls.green_table, cls.db.engine,
                             if_exists="replace", index=False)

    @classmethod
    def teardown_class(cls):
        for t in [cls.edge_table, cls.grid_table, cls.node_table, cls.green_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    def _get_indexes(self, table):
        result = self.db.execute(
            f"SELECT indexname FROM pg_indexes WHERE tablename = '{table}'"
        )
        return [r[0] for r in result.fetchall()]

    def test_edge_indexes_created(self):
        with self.db.engine.begin() as conn:
            create_edge_indexes(conn, self.area, "walking")
        indexes = self._get_indexes(self.edge_table)
        assert any("edge_id" in idx for idx in indexes)
        assert any("tile_id" in idx for idx in indexes)
        assert any("geometry" in idx for idx in indexes)

    def test_grid_indexes_created(self):
        with self.db.engine.begin() as conn:
            create_grid_indexes(conn, self.area)
        indexes = self._get_indexes(self.grid_table)
        assert any("tile_id" in idx for idx in indexes)
        assert any("geometry" in idx for idx in indexes)

    def test_node_indexes_created(self):
        with self.db.engine.begin() as conn:
            create_node_indexes(conn, self.area, "walking")
        indexes = self._get_indexes(self.node_table)
        assert any("node_id" in idx for idx in indexes)
        assert any("tile_id" in idx for idx in indexes)
        assert any("geometry" in idx for idx in indexes)

    def test_green_indexes_created(self):
        with self.db.engine.begin() as conn:
            create_green_indexes(conn, self.area)
        indexes = self._get_indexes(self.green_table)
        assert any("tile_id" in idx for idx in indexes)
        assert any("geometry" in idx for idx in indexes)
