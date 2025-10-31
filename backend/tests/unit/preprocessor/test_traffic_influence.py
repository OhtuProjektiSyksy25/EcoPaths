import pytest
import geopandas as gpd
from shapely.geometry import LineString
from src.database.db_client import DatabaseClient
from src.config.settings import AREA_SETTINGS
from preprocessor.traffic_influence import TrafficInfluenceBuilder


class TestTrafficInfluenceBuilder:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea_traffic"
        cls.walk_table = f"edges_{cls.area}_walking"
        cls.drive_table = f"edges_{cls.area}_driving"

        if cls.area not in AREA_SETTINGS:
            AREA_SETTINGS[cls.area] = AREA_SETTINGS["testarea"]

        for table in [cls.walk_table, cls.drive_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

        # Create tables
        cls.db.create_tables_for_area(cls.area, "walking")
        cls.db.create_tables_for_area(cls.area, "driving")

        # Insert walking edge
        walk_gdf = gpd.GeoDataFrame({
            "edge_id": [1],
            "tile_id": ["A"],
            "length_m": [10.0],
            "from_node": [None],
            "to_node": [None],
            "geometry": [LineString([(0, 0), (1, 1)])]
        }, geometry="geometry", crs="EPSG:25833")

        walk_gdf.to_postgis(cls.walk_table, cls.db.engine,
                            if_exists="append", index=False)

        # Insert nearby driving edge
        drive_gdf = gpd.GeoDataFrame({
            "edge_id": [100],
            "tile_id": ["A"],
            "length_m": [10.0],
            "geometry": [LineString([(0.5, 0.5), (1.5, 1.5)])],
            "lanes": [2],
            "maxspeed": [50],
            "width": [6],
            "tunnel": [False],
            "covered": [False]
        }, geometry="geometry", crs="EPSG:25833")

        drive_gdf.to_postgis(cls.drive_table, cls.db.engine,
                             if_exists="append", index=False)

        cls.builder = TrafficInfluenceBuilder(cls.db, cls.area)
        cls.builder.compute_cumulative_influence()

    @classmethod
    def teardown_class(cls):
        for t in [cls.walk_table, cls.drive_table]:
            cls.db.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    def test_column_added(self):
        result = self.db.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{self.walk_table}'
        """)
        columns = [r[0] for r in result.fetchall()]
        assert "traffic_influence" in columns

    def test_influence_value_updated(self):
        result = self.db.execute(f"""
            SELECT traffic_influence
            FROM {self.walk_table}
            WHERE edge_id = 1
        """)
        value = result.scalar()
        assert value > 1.0  # influence should be greater than default
