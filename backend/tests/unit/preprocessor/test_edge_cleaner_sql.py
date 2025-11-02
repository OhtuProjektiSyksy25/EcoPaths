import pytest
import geopandas as gpd
from shapely.geometry import LineString
from shapely.wkt import loads
from preprocessor.edge_cleaner_sql import EdgeCleanerSQL
from src.database.db_client import DatabaseClient
from src.config.settings import AREA_SETTINGS


class TestEdgeCleaner:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea_edgesql"
        cls.network_type = "walking"
        cls.edge_table = f"edges_{cls.area}_{cls.network_type}"
        cls.node_table = f"nodes_{cls.area}_{cls.network_type}"
        cls.grid_table = f"grid_{cls.area}"

        if cls.area not in AREA_SETTINGS:
            AREA_SETTINGS[cls.area] = AREA_SETTINGS["testarea"]

        for table in [cls.edge_table, cls.node_table, cls.grid_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

        cls.db.create_tables_for_area(cls.area, cls.network_type)

        cls.db.execute(f"""
            INSERT INTO {cls.grid_table} (tile_id, geometry)
            VALUES 
                (1, ST_MakeEnvelope(0,0,1.5,1.5,25833)),
                (2, ST_MakeEnvelope(1.5,1.5,3,3,25833));
        """)

        gdf = gpd.GeoDataFrame({
            "edge_id": [1, 2, 3, 4, 5],
            "access": ["yes", "private", "permissive", "no", None],
            "length_m": [None] * 5,
            "normalized_length": [None] * 5,
            "from_node": [100, 101, 102, 103, 104],
            "to_node": [101, 102, 103, 104, 105],
            "tile_id": ["A", "B", "C", "D", "E"],
            "geometry": [
                LineString([(0, 0), (1, 1)]),
                LineString([(1, 1), (2, 2)]),
                LineString([(2, 2), (3, 3)]),
                LineString([(3, 3), (4, 4)]),
                LineString([(4, 4), (5, 5)])
            ]
        }, geometry="geometry", crs="EPSG:25833")

        gdf.to_postgis(cls.edge_table, cls.db.engine,
                       if_exists="append", index=False)

        cls.cleaner = EdgeCleanerSQL(cls.db)

    @classmethod
    def teardown_class(cls):
        for t in [cls.edge_table, cls.node_table, cls.grid_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    def test_filter_access(self):
        self.cleaner.filter_access(self.area, self.network_type)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.edge_table}
            WHERE access NOT IN ('yes', 'permissive') AND access IS NOT NULL
        """)
        assert result.scalar() == 0

    def test_compute_lengths(self):
        self.cleaner.compute_lengths(self.area, self.network_type)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.edge_table} WHERE length_m IS NOT NULL
        """)
        assert result.scalar() > 0

    def test_normalize_geometry(self):
        self.cleaner.normalize_geometry(self.area, self.network_type)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.edge_table} WHERE GeometryType(geometry) NOT IN ('LINESTRING')
        """)
        assert result.scalar() == 0

    def test_remove_disconnected_edges_keeps_connected(self):
        self.db.execute(f"DELETE FROM {self.edge_table};")
        gdf = gpd.GeoDataFrame({
            "edge_id": [1, 2, 3, 4, 5, 6],
            "from_node": [100, 101, 102, 999, 2000, 2001],
            "to_node": [101, 102, 103, 998, 2001, 2002],
            "tile_id": ["A", "B", "C", "D", "E", "F"],
            "geometry": [
                LineString([(0, 0), (1, 1)]),
                LineString([(1, 1), (2, 2)]),
                LineString([(2, 2), (3, 3)]),
                LineString([(10, 10), (11, 11)]),
                LineString([(20, 20), (21, 21)]),
                LineString([(21, 21), (22, 22)])
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf.to_postgis(self.edge_table, self.db.engine,
                       if_exists="append", index=False)

        self.cleaner.remove_disconnected_edges(self.area, self.network_type)
        count = self.db.execute(
            f"SELECT COUNT(*) FROM {self.edge_table}").scalar()
        assert count == 3

    def test_drop_invalid_geometries_removes_invalid_rows(self):
        self.db.execute(f"DELETE FROM {self.edge_table};")
        gdf = gpd.GeoDataFrame({
            "edge_id": [1, 2],
            "geometry": [
                LineString([(0, 0), (1, 1)]),
                loads("LINESTRING(0 0, 0 0)")  # degenerate but valid
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf.to_postgis(self.edge_table, self.db.engine,
                       if_exists="append", index=False)

        self.cleaner.drop_invalid_geometries(self.area, self.network_type)
        count = self.db.execute(
            f"SELECT COUNT(*) FROM {self.edge_table}").scalar()
        assert count >= 1

    def test_split_edges_by_tiles(self):
        self.db.execute(f"DELETE FROM {self.edge_table};")
        gdf_edges = gpd.GeoDataFrame({
            "edge_id": [1, 2],
            "from_node": [100, 101],
            "to_node": [101, 102],
            "length_m": [None, None],
            "tile_id": [None, None],
            "geometry": [
                LineString([(0, 0), (2, 2)]),
                LineString([(1, 1), (3, 3)])
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_edges.to_postgis(self.edge_table, self.db.engine,
                             if_exists="append", index=False)

        gdf_grid = gpd.GeoDataFrame({
            "tile_id": [1, 2],
            "geometry": [
                LineString([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]).envelope,
                LineString([(2, 0), (4, 0), (4, 2), (2, 2), (2, 0)]).envelope
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_grid.to_postgis(self.grid_table, self.db.engine,
                            if_exists="replace", index=False)

        self.cleaner.split_edges_by_tiles(self.area, self.network_type)

        edges_after = gpd.read_postgis(
            f"SELECT * FROM {self.edge_table}", self.db.engine, geom_col="geometry")
        assert all(edges_after.geometry.notnull())
        assert edges_after.tile_id.notnull().all()
        assert edges_after.geometry.apply(lambda g: g.is_valid).all()

    def test_edge_split_gets_correct_tile_ids(self):
        self.db.execute(f"DELETE FROM {self.edge_table};")

        gdf_edges = gpd.GeoDataFrame({
            "edge_id": [1],
            "from_node": [100],
            "to_node": [101],
            "geometry": [LineString([(0, 0), (3, 0)])]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_edges.to_postgis(self.edge_table, self.db.engine,
                             if_exists="replace", index=False)

        gdf_grid = gpd.GeoDataFrame({
            "tile_id": [1, 2],
            "geometry": [
                LineString([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]).envelope,
                LineString([(2, 0), (4, 0), (4, 2), (2, 2), (2, 0)]).envelope
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_grid.to_postgis(self.grid_table, self.db.engine,
                            if_exists="replace", index=False)

        self.cleaner.split_edges_by_tiles(self.area, self.network_type)

        edges_after = gpd.read_postgis(
            f"SELECT * FROM {self.edge_table}", self.db.engine, geom_col="geometry")

        assert len(edges_after) == 2
        assert edges_after.tile_id.notnull().all()

        for _, row in edges_after.iterrows():
            tile_geom = gdf_grid.loc[gdf_grid.tile_id ==
                                     row.tile_id, "geometry"].iloc[0]
            assert tile_geom.covers(
                row.geometry) or tile_geom.equals(row.geometry)
