import pytest
import geopandas as gpd
from shapely.geometry import LineString, Polygon
from src.database.db_client import DatabaseClient
from src.config.settings import AREA_SETTINGS
from preprocessor.green_influence import GreenInfluenceBuilder


class TestGreenInfluenceBuilder:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea_green"
        cls.walk_table = f"edges_{cls.area}_walking"
        cls.green_table = f"green_{cls.area}"

        if cls.area not in AREA_SETTINGS:
            AREA_SETTINGS[cls.area] = AREA_SETTINGS["testarea"]

        for t in [cls.walk_table, cls.green_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

        cls.db.create_tables_for_area(cls.area, "walking")

        walk_gdf = gpd.GeoDataFrame({
            "edge_id": [1],
            "tile_id": ["T1"],
            "length_m": [10.0],
            "from_node": [None],
            "to_node": [None],
            "geometry": [LineString([(0, 0), (1, 1)])]
        }, geometry="geometry", crs="EPSG:25833")
        walk_gdf.to_postgis(cls.walk_table, cls.db.engine,
                            if_exists="append", index=False)

        # Insert green polygon overlapping edge
        green_gdf = gpd.GeoDataFrame({
            "land_id": [1],
            "green_type": ["park"],
            "tile_id": ["T1"],
            "geometry": [Polygon([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])]
        }, geometry="geometry", crs="EPSG:25833")
        green_gdf.to_postgis(cls.green_table, cls.db.engine,
                             if_exists="replace", index=False)

        cls.builder = GreenInfluenceBuilder(cls.db, cls.area)
        cls.builder.run()

    @classmethod
    def teardown_class(cls):
        for t in [cls.walk_table, cls.green_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    def test_column_added(self):
        result = self.db.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{self.walk_table}'
        """)
        columns = [r[0] for r in result.fetchall()]
        assert "green_influence" in columns

    def test_influence_value_updated(self):
        result = self.db.execute(f"""
            SELECT green_influence
            FROM {self.walk_table}
            WHERE edge_id = 1
        """)
        value = result.scalar()
        assert value is not None
        assert 0.0 < value < 1.0, f"Expected between 0 and 1, got {value}"

    def test_far_edge_remains_default(self):
        # Insert far away edge
        far_walk_gdf = gpd.GeoDataFrame({
            "edge_id": [2],
            "tile_id": ["T1"],
            "length_m": [10.0],
            "from_node": [None],
            "to_node": [None],
            "geometry": [LineString([(1000, 1000), (1001, 1001)])]
        }, geometry="geometry", crs="EPSG:25833")
        far_walk_gdf.to_postgis(
            self.walk_table, self.db.engine, if_exists="append", index=False)

        self.builder.run()

        result = self.db.execute(f"""
            SELECT green_influence
            FROM {self.walk_table}
            WHERE edge_id = 2
        """)
        value = result.scalar()
        assert value is None, f"Expected None for far edge, got {value}"

    def test_influence_values_are_bounded(self):
        result = self.db.execute(f"""
            SELECT COUNT(*) FROM {self.walk_table}
            WHERE green_influence < 0.0 OR green_influence > {self.builder.max_benefit + 1.0}
        """)
        count = result.scalar()
        assert count == 0, f"Found {count} edges outside expected bounds"
