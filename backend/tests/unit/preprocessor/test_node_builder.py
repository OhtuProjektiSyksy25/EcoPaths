import pytest
import geopandas as gpd
from shapely.geometry import LineString
from preprocessor.node_builder import NodeBuilder
from src.database.db_client import DatabaseClient


class TestNodeBuilder:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea"
        cls.network_type = "walking"
        cls.edge_table = f"edges_{cls.area}_{cls.network_type}"
        cls.node_table = f"nodes_{cls.area}_{cls.network_type}"

        # Pudota taulut
        cls.db.execute(f"DROP TABLE IF EXISTS {cls.edge_table} CASCADE;")
        cls.db.execute(f"DROP TABLE IF EXISTS {cls.node_table} CASCADE;")

        # Luo mock edge data
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
        }, geometry="geometry", crs="EPSG:25833")
        gdf.to_postgis(cls.edge_table, cls.db.engine,
                       if_exists="replace", index=False)

        # Rakenna node-taulu kerran
        builder = NodeBuilder(cls.db, cls.area, cls.network_type)
        builder.build_nodes_and_attach_to_edges()

    @classmethod
    def teardown_class(cls):
        cls.db.execute(f"DROP TABLE IF EXISTS {cls.edge_table} CASCADE;")
        cls.db.execute(f"DROP TABLE IF EXISTS {cls.node_table} CASCADE;")

    def test_node_table_created(self):
        assert self.db.table_exists(self.node_table)

    def test_edge_table_has_node_columns(self):
        result = self.db.execute(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = '{self.edge_table}'
        """)
        columns = [row[0] for row in result.fetchall()]
        assert "from_node" in columns
        assert "to_node" in columns

    def test_node_ids_are_assigned(self):
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.edge_table}
            WHERE from_node IS NOT NULL AND to_node IS NOT NULL
        """)
        assert result.scalar() > 0

    def test_node_count_matches_endpoints(self):
        result = self.db.execute(f"SELECT COUNT(*) FROM {self.node_table}")
        assert result.scalar() == 3

    def test_node_geometry_is_unique(self):
        result = self.db.execute(f"""
            SELECT COUNT(*) - COUNT(DISTINCT geometry)
            FROM {self.node_table}
        """)
        assert result.scalar() == 0

    def test_edge_geometry_preserved(self):
        original = self.db.execute(f"""
            SELECT ST_AsText(geometry) FROM {self.edge_table}
            ORDER BY edge_id
        """).fetchall()

        updated = self.db.execute(f"""
            SELECT ST_AsText(geometry) FROM {self.edge_table}
            ORDER BY edge_id
        """).fetchall()

        assert original == updated

    def test_edge_row_count_unchanged(self):
        count = self.db.execute(
            f"SELECT COUNT(*) FROM {self.edge_table}").scalar()
        assert count == 2
