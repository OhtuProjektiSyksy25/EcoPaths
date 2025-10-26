import pytest
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, GeometryCollection, Point
from preprocessor.edge_cleaner_sql import EdgeCleanerSQL
from src.database.db_client import DatabaseClient


class TestEdgeCleaner:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea"
        cls.network_type = "walking"
        cls.table = f"edges_{cls.area}_{cls.network_type}"

        # Puhdas testitaulu
        cls.db.execute(f"DROP TABLE IF EXISTS {cls.table} CASCADE;")

        gdf = gpd.GeoDataFrame({
            "edge_id": [1, 2, 3, 4, 5],
            "access": ["yes", "private", "permissive", "no", None],
            "length_m": [None] * 5,
            "tile_id": [None] * 5,
            "geometry": [
                LineString([(0, 0), (1, 1)]),
                LineString([(1, 1), (2, 2)]),
                MultiLineString([[(2, 2), (3, 3)], [(3, 3), (4, 4)]]),
                GeometryCollection(
                    [LineString([(4, 4), (5, 5)]), Point(6, 6)]),
                Point(7, 7)
            ]
        }, geometry="geometry", crs="EPSG:25833")

        # Tallennetaan testitauluun
        gdf.to_postgis(cls.table, cls.db.engine,
                       if_exists="replace", index=False)
        cls.cleaner = EdgeCleanerSQL(cls.db)

    @classmethod
    def teardown_class(cls):
        cls.db.execute(f"DROP TABLE IF EXISTS {cls.table} CASCADE;")

    def test_filter_access(self):
        self.cleaner.filter_access(self.area, self.network_type)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.table}
            WHERE access NOT IN ('yes', 'permissive') AND access IS NOT NULL
        """)
        assert result.scalar() == 0

    def test_compute_lengths(self):
        self.cleaner.compute_lengths(self.area, self.network_type)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.table} WHERE length_m IS NOT NULL
        """)
        assert result.scalar() > 0

    def test_normalize_geometry(self):
        self.cleaner.normalize_geometry(self.area, self.network_type)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.table} WHERE GeometryType(geometry) NOT IN ('LINESTRING')
        """)
        assert result.scalar() == 0

    def test_remove_disconnected_edges_keeps_connected(self):
        self.db.execute(f"DROP TABLE IF EXISTS {self.table} CASCADE;")
        gdf = gpd.GeoDataFrame({
            "edge_id": [1, 2],
            "from_node": [100, 101],
            "to_node": [101, 102],
            "geometry": [
                LineString([(0, 0), (1, 1)]),
                LineString([(1, 1), (2, 2)])
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf.to_postgis(self.table, self.db.engine,
                       if_exists="replace", index=False)

        self.cleaner.remove_disconnected_edges(self.area, self.network_type)
        count = self.db.execute(f"SELECT COUNT(*) FROM {self.table}").scalar()
        assert count == 2

    def test_drop_invalid_geometries_removes_invalid_rows(self):
        self.db.execute(f"DROP TABLE IF EXISTS {self.table} CASCADE;")
        from shapely.wkt import loads
        invalid_geom = loads("POLYGON((0 0, 1 1, 1 0, 0 1, 0 0))")
        gdf = gpd.GeoDataFrame({
            "edge_id": [1, 2, 3],
            "geometry": [
                invalid_geom,
                Point(0, 0),
                LineString([(0, 0), (1, 1)])
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf.to_postgis(self.table, self.db.engine,
                       if_exists="replace", index=False)

        self.cleaner.drop_invalid_geometries(self.area, self.network_type)
        result = self.db.execute(f"SELECT COUNT(*) FROM {self.table}").scalar()
        assert result == 1
        geom_type = self.db.execute(
            f"SELECT GeometryType(geometry) FROM {self.table}").scalar()
        assert geom_type == "LINESTRING"

    def test_split_edges_by_tiles(self):
        self.db.execute(f"DROP TABLE IF EXISTS {self.table} CASCADE;")
        split_table = f"{self.table}_split"

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
        gdf_edges.to_postgis(self.table, self.db.engine,
                             if_exists="replace", index=False)

        gdf_grid = gpd.GeoDataFrame({
            "tile_id": [1, 2, 3, 4],
            "geometry": [
                LineString([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]).envelope,
                LineString([(2, 0), (4, 0), (4, 2), (2, 2), (2, 0)]).envelope,
                LineString([(0, 2), (2, 2), (2, 4), (0, 4), (0, 2)]).envelope,
                LineString([(2, 2), (4, 2), (4, 4), (2, 4), (2, 2)]).envelope
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_grid.to_postgis(
            f"grid_{self.area}", self.db.engine, if_exists="replace", index=False)

        self.cleaner.split_edges_by_tiles(self.area, self.network_type)

        edges_after = gpd.read_postgis(
            f"SELECT * FROM {self.table}", self.db.engine, geom_col="geometry")
        assert all(edges_after.geometry.notnull())
        assert edges_after.tile_id.notnull().all()
        assert edges_after.geometry.apply(lambda g: g.is_valid).all()

        for idx, row in edges_after.iterrows():
            tile_geom = gdf_grid.loc[gdf_grid.tile_id ==
                                     row.tile_id, "geometry"].iloc[0]
            assert tile_geom.covers(
                row.geometry) or tile_geom.equals(row.geometry)

    def test_edge_split_gets_correct_tile_ids(self):

        gdf_edges = gpd.GeoDataFrame({
            "edge_id": [1],
            "from_node": [100],
            "to_node": [101],
            "geometry": [LineString([(0, 0), (3, 0)])]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_edges.to_postgis(self.table, self.db.engine,
                             if_exists="replace", index=False)

        gdf_grid = gpd.GeoDataFrame({
            "tile_id": [1, 2],
            "geometry": [
                LineString([(0, 0), (2, 0)]).envelope,
                LineString([(2, 0), (4, 0)]).envelope
            ]
        }, geometry="geometry", crs="EPSG:25833")
        gdf_grid.to_postgis(
            f"grid_{self.area}", self.db.engine, if_exists="replace", index=False)

        self.cleaner.split_edges_by_tiles(self.area, self.network_type)

        edges_after = gpd.read_postgis(
            f"SELECT * FROM {self.table}", self.db.engine, geom_col="geometry")

        assert len(edges_after) == 2

        assert edges_after.tile_id.notnull().all()

        for idx, row in edges_after.iterrows():
            tile_geom = gdf_grid.loc[gdf_grid.tile_id ==
                                     row.tile_id, "geometry"].iloc[0]
            assert tile_geom.covers(
                row.geometry) or tile_geom.equals(row.geometry)
