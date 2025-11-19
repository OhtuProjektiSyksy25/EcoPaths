import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.wkt import loads
from src.database.db_client import DatabaseClient
from src.config.settings import AREA_SETTINGS
from preprocessor.green_cleaner_sql import GreenCleanerSQL


class TestGreenCleanerSQL:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea_green"
        cls.green_table = f"green_{cls.area}"
        cls.grid_table = f"grid_{cls.area}"

        if cls.area not in AREA_SETTINGS:
            AREA_SETTINGS[cls.area] = AREA_SETTINGS["testarea"]

        for t in [cls.green_table, cls.grid_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

        grid_gdf = gpd.GeoDataFrame({
            "tile_id": [1, 2],
            "geometry": [
                Polygon([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]),
                Polygon([(2, 0), (2, 2), (4, 2), (4, 0), (2, 0)])
            ]
        }, geometry="geometry", crs="EPSG:25833")
        grid_gdf.to_postgis(cls.grid_table, cls.db.engine,
                            if_exists="replace", index=False)

        green_gdf = gpd.GeoDataFrame({
            "land_id": [1, 2, 3, 4],
            "green_type": ["park", "forest", "grass", "park"],
            "geometry": [
                MultiPolygon(
                    [Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])]),
                Point(0.5, 0.5),
                LineString([(3, 0), (3, 1)]),
                loads("POLYGON((0 0, 0 0, 0 0, 0 0))")
            ]
        }, geometry="geometry", crs="EPSG:25833")
        green_gdf.to_postgis(cls.green_table, cls.db.engine,
                             if_exists="replace", index=False)

        cls.cleaner = GreenCleanerSQL(cls.db)

    @classmethod
    def teardown_class(cls):
        for t in [cls.green_table, cls.grid_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    def test_full_pipeline_run(self):
        self.cleaner.run(self.area)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.green_table}
            WHERE GeometryType(geometry) NOT IN ('POLYGON','MULTIPOLYGON')
        """)
        assert result.scalar() == 0

    def test_buffer_points_and_lines(self):
        self.cleaner.buffer_points_and_lines(self.area)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.green_table}
            WHERE GeometryType(geometry) IN ('POINT','LINESTRING')
        """)
        assert result.scalar() == 0

    def test_make_valid_and_drop_invalid(self):
        self.cleaner.make_valid(self.area)
        self.cleaner.drop_invalid_geometries(self.area)
        count = self.db.execute(
            f"SELECT COUNT(*) FROM {self.green_table}").scalar()
        assert count >= 1

    def test_invalid_geometry_removed(self):
        self.cleaner.make_valid(self.area)
        self.cleaner.drop_invalid_geometries(self.area)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.green_table}
            WHERE NOT ST_IsValid(geometry)
        """)
        assert result.scalar() == 0

    def test_merge_overlaps(self):
        self.cleaner.merge_overlaps(self.area)
        result = self.db.execute(
            f"SELECT COUNT(DISTINCT green_type) FROM {self.green_table}")
        assert result.scalar() >= 1

    def test_merge_reduces_row_count(self):
        before = self.db.execute(
            f"SELECT COUNT(*) FROM {self.green_table}").scalar()
        self.cleaner.merge_overlaps(self.area)
        after = self.db.execute(
            f"SELECT COUNT(*) FROM {self.green_table}").scalar()
        assert after <= before

    def test_split_green_by_tiles(self):
        self.cleaner.split_green_by_tiles(self.area)
        result = self.db.execute(f"SELECT COUNT(*) FROM {self.green_table}")
        assert result.scalar() > 0
        tile_ids = [r[0] for r in self.db.execute(
            f"SELECT DISTINCT tile_id FROM {self.green_table}").fetchall()]
        assert all(t is not None for t in tile_ids)

    def test_split_assigns_tile_ids(self):
        self.cleaner.split_green_by_tiles(self.area)
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.green_table}
            WHERE tile_id IS NULL
        """)
        assert result.scalar() == 0
