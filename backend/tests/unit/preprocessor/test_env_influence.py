import pytest
import geopandas as gpd
from shapely.geometry import LineString
from src.database.db_client import DatabaseClient
from preprocessor.env_influence import EnvInfluenceBuilder


class TestEnvInfluenceBuilder:
    @classmethod
    def setup_class(cls):
        cls.db = DatabaseClient()
        cls.area = "testarea_env"
        cls.table = f"edges_{cls.area}_walking"

        cls.db.execute(f"DROP TABLE IF EXISTS {cls.table} CASCADE;")
        cls.db.create_tables_for_area(cls.area, "walking")

        gdf = gpd.GeoDataFrame({
            "edge_id": [1, 2],
            "tile_id": ["A", "B"],
            "length_m": [10.0, 20.0],
            "traffic_influence": [1.5, 2.0],
            "geometry": [
                LineString([(0, 0), (1, 1)]),
                LineString([(1, 1), (2, 2)])
            ]
        }, geometry="geometry", crs="EPSG:25833")

        gdf.to_postgis(cls.table, cls.db.engine,
                       if_exists="append", index=False)

        cls.builder = EnvInfluenceBuilder(cls.db, cls.area)
        cls.builder.run()

    @classmethod
    def teardown_class(cls):
        cls.db.execute(f"DROP TABLE IF EXISTS {cls.table} CASCADE;")

    def test_column_created(self):
        result = self.db.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{self.table}'
        """)
        columns = [r[0] for r in result.fetchall()]
        assert "env_influence" in columns

    def test_values_copied(self):
        result = self.db.execute(f"""
            SELECT traffic_influence, env_influence
            FROM {self.table}
            ORDER BY edge_id
        """)
        rows = result.fetchall()
        for traffic, env in rows:
            assert traffic == env
