import pytest
import geopandas as gpd
import fakeredis
from shapely.geometry import LineString
import pandas as pd
import json
from src.services.redis_service import RedisService
from src.services.redis_cache import RedisCache


class FakeAreaConfig:
    def __init__(self):
        self.area = "testarea"
        self.crs = "EPSG:25833"


class TestRedisService:

    @pytest.fixture
    def fake_area(self):
        return FakeAreaConfig()

    @pytest.fixture
    def fake_redis(self):
        """Creates a fake redis that is used for testing."""
        fake_redis = RedisCache()
        fake_redis.client = fakeredis.FakeRedis(decode_responses=True)

        def set_direct(key, value, ttl):
            fake_redis.client.set(key, value)
            return True

        def get_geojson(key):
            val = fake_redis.client.get(key)
            if val is None:
                return None
            return json.loads(val)

        def exists(key):
            return fake_redis.client.exists(key)

        fake_redis.set_direct = set_direct
        fake_redis.get_geojson = get_geojson
        fake_redis.exists = exists
        return fake_redis

    @pytest.fixture
    def sample_gdf(self):
        lines = [
            LineString([(0, 0), (1, 1)]),
            LineString([(1, 1), (2, 2)]),
            LineString([(2, 2), (3, 3)]),
            LineString([(3, 3), (4, 4)]),
            LineString([(4, 4), (5, 5)])
        ]

        gdf = gpd.GeoDataFrame({
            "geometry": lines,
            "length_m": [1.414] * 5,
            "tile_id": ["r0_c2", "r1_c2", "r0_c2", "r2_c2", "r1_c2"],
            "test_id": [0, 1, 2, 3, 4]
        }, crs="EPSG:25833")
        return gdf

    def test_group_gdf_by_tile(self, sample_gdf):
        result = RedisService.group_gdf_by_tile(sample_gdf)
        expected_mapping = {
            "r0_c2": [0, 2],
            "r1_c2": [1, 4],
            "r2_c2": [3]
        }

        for tile_id, expected_ids in expected_mapping.items():
            group = result[tile_id]
            actual_ids = group["test_id"].tolist()
            assert sorted(actual_ids) == sorted(expected_ids)

    def test_save_gdf_and_fetch_as_gdf(self, sample_gdf, fake_redis, fake_area):
        success = RedisService.save_gdf(sample_gdf, fake_redis, fake_area)
        assert success is True

        expected_tile_ids = sample_gdf["tile_id"].unique()

        for tile_id in expected_tile_ids:
            prefixed_key = f"{fake_area.area}_{tile_id}"
            assert fake_redis.exists(prefixed_key)

        for tile_id in expected_tile_ids:
            stored_value, _ = RedisService.get_gdf_by_list_of_keys(
                [tile_id], fake_redis, fake_area)
