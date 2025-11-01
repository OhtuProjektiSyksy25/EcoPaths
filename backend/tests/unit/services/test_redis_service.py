import pytest
import geopandas as gpd
import fakeredis
from src.services.redis_service import RedisService
from src.config.settings import get_settings
from shapely.geometry import LineString
from services.redis_cache import RedisCache
from unittest.mock import patch, MagicMock
import pandas as pd


class TestRedisService:

    @pytest.fixture
    def fake_area(self):
        fake_area = get_settings("berlin")
        return fake_area.area

    @pytest.fixture
    def fake_redis(self):
        """Creates a fake redis that is used for testing."""
        fake_redis = RedisCache()
        fake_redis.client = fakeredis.FakeRedis(decode_responses=True)
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

        lengths = [1.414, 1.414, 1.414, 1.414, 1.414]
        tile_ids = ["r0_c2", "r1_c2", "r0_c2", "r2_c2", "r1_c2"]
        test_ids = [0, 1, 2, 3, 4]

        gdf = gpd.GeoDataFrame({
            "geometry": lines,
            "length_m": lengths,
            "tile_id": tile_ids,
            "test_id": test_ids
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
        """
        Tests if gdf can be saved to redis and fetched while maintaing all information.
        """
        success = RedisService.save_gdf(sample_gdf, fake_redis, fake_area)

        assert success is True

        expected_tile_ids = sample_gdf["tile_id"].unique()

        for tile_id in expected_tile_ids:
            stored_value,_ = RedisService.get_gdf_by_list_of_keys(
                [tile_id], fake_redis, fake_area)
            origin_value = sample_gdf[sample_gdf["tile_id"] == tile_id]
            assert stored_value is not None
            assert pd.testing.assert_frame_equal(
                stored_value, origin_value.reset_index(drop=True)) is None

    def test_prune_found_ids(self, sample_gdf, fake_redis, fake_area):
        """ 
        Test if "RedisService.prune_found_ids" returns a list of tile_ids with tile_ids that appear in redis removed
        """
        success = RedisService.save_gdf(sample_gdf, fake_redis, fake_area)
        assert success is True
        ids_to_check = ["r6_c2", "r1_c3", "r1_c2"]
        pruned_tile_ids = RedisService.prune_found_ids(ids_to_check, fake_redis)
        assert pruned_tile_ids == ["r6_c2", "r1_c3"]

    def test_edge_enricher_to_redis_handler(self, fake_redis, fake_area, sample_gdf):
        """
        Test that RedisService.edge_enricher_to_redis_handler correctly
        calls edge_enricher and handles data correctly.
        """
        tile_ids = ["r0_c2", "r1_c2"]

        with patch("src.services.redis_service.EdgeEnricher") as MockEdgeEnricher:
            instance = MockEdgeEnricher.return_value
            instance.get_enriched_tiles.return_value = sample_gdf
            result = RedisService.edge_enricher_to_redis_handler(tile_ids, fake_redis, fake_area)

            assert isinstance(result, gpd.GeoDataFrame)
            assert pd.testing.assert_frame_equal(
                result.reset_index(drop=True), sample_gdf.reset_index(drop=True)) is None

            MockEdgeEnricher.assert_called_once_with(fake_area.area)
            instance.get_enriched_tiles.assert_called_once_with(tile_ids)

            for tile_id in sample_gdf["tile_id"].unique():
                stored_value, _ = RedisService.get_gdf_by_list_of_keys(
                    [tile_id], fake_redis, fake_area)
                assert not stored_value.empty