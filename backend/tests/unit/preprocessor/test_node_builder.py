import pytest
import geopandas as gpd
from shapely.geometry import LineString
from preprocessor.node_builder import NodeBuilder
from src.database.db_client import DatabaseClient
from src.database.db_connection import Base
from src.config.settings import AREA_SETTINGS


class TestNodeBuilder:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea_node"
        cls.network_type = "walking"
        cls.edge_table = f"edges_{cls.area}_{cls.network_type}"
        cls.node_table = f"nodes_{cls.area}_{cls.network_type}"
        cls.grid_table = f"grid_{cls.area}"

        if cls.area not in AREA_SETTINGS:
            AREA_SETTINGS[cls.area] = AREA_SETTINGS["testarea"]

        cls.db.create_tables_for_area(cls.area, cls.network_type)

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
                       if_exists="append", index=False)

        cls.db.execute(f"""
            INSERT INTO {cls.grid_table} (tile_id, geometry)
            VALUES 
                (1, ST_MakeEnvelope(0,0,1.5,1.5,25833)),
                (2, ST_MakeEnvelope(1.5,1.5,3,3,25833));
        """)

        cls.builder = NodeBuilder(cls.db, cls.area, cls.network_type)
        cls.builder.build_nodes_and_attach_to_edges()

    @classmethod
    def teardown_class(cls):
        for t in [cls.edge_table, cls.node_table, cls.grid_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    def _count(self, table):
        return self.db.execute(f"SELECT COUNT(*) FROM {table}").scalar()

    # Tests

    def test_node_table_created(self):
        assert self.db.table_exists(self.node_table)

    def test_edge_table_has_node_columns(self):
        result = self.db.execute(f"""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_name = '{self.edge_table}'
        """)
        columns = [r[0] for r in result.fetchall()]
        assert "from_node" in columns
        assert "to_node" in columns

    def test_node_ids_are_assigned(self):
        result = self.db.execute(f"""
            SELECT COUNT(*) 
            FROM {self.edge_table}
            WHERE from_node IS NOT NULL AND to_node IS NOT NULL
        """)
        assert result.scalar() == 2

    def test_node_count_matches_endpoints(self):
        assert self._count(self.node_table) == 3

    def test_node_geometry_is_unique(self):
        result = self.db.execute(f"""
            SELECT COUNT(*) - COUNT(DISTINCT geometry)
            FROM {self.node_table}
        """)
        assert result.scalar() == 0

    def test_edge_row_count_unchanged(self):
        assert self._count(self.edge_table) == 2

    def test_remove_unused_nodes(self):
        self.db.execute(f"""
            INSERT INTO {self.node_table} (node_id, geometry, tile_id)
            VALUES (999, ST_SetSRID(ST_MakePoint(10, 10), 25833), NULL);
        """)

        count_before = self._count(self.node_table)

        self.builder.remove_unused_nodes()
        count_after = self._count(self.node_table)

        assert count_after == count_before - 1

        result = self.db.execute(f"""
            SELECT n.node_id
            FROM {self.node_table} n
            LEFT JOIN (
                SELECT from_node AS node_id FROM {self.edge_table}
                UNION
                SELECT to_node AS node_id FROM {self.edge_table}
            ) used_nodes
            ON n.node_id = used_nodes.node_id
            WHERE used_nodes.node_id IS NULL;
        """)
        assert len(result.fetchall()) == 0

    def test_assign_tile_ids(self):
        self.builder.assign_tile_ids()

        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.node_table}
            WHERE tile_id IS NOT NULL;
        """)
        count_with_tile = result.scalar()

        assert count_with_tile == self._count(self.node_table)
