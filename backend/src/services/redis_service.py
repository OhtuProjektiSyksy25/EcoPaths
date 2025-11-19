"""
Utility module for handling, saving and fetching of GeoDataFrame/geojson data to and from redis
"""
import geopandas as gpd
from logger.logger import log


class RedisService:
    """
    A utility class for interacting with redis,
    """
    @staticmethod
    def group_gdf_by_tile(gdf: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
        """
        Groups GeoDataFrame by 'tile_id' and returns dict of {tile_id: GeoDataFrame}.
        Keys will later be combined with area name when saving to Redis.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame object

        Returns:
            dict: key: tile_id, value: GeoDataFrame
        """
        grouped = gdf.groupby("tile_id")
        grouped_dict = {tile_id: group for tile_id,  # pylint: disable=unnecessary-comprehension
                        group in grouped}  # pylint: disable=unnecessary-comprehension
        return grouped_dict

    @staticmethod
    def save_gdf(gdf: gpd.GeoDataFrame, redis, area):
        """Groups given gdf by tile_id and saves each group to redis
        with key: '{area_name}_{tile_id}' and value: FeatureCollection.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame to be saved to redis
            redis : Redis object that is being saved to

        Returns:
            True: Returns True if saving is successful
            False: Returns False if saving is not succesful
        """
        tile_groups = RedisService.group_gdf_by_tile(gdf)
        failed = []
        for tile_id, current_gdf in tile_groups.items():
            key = f"{area.area}_{tile_id}"
            current_gdf = current_gdf.to_crs(area.crs)
            feature_collection = current_gdf.to_json()
            success = redis.set_direct(key, feature_collection, 10800)
            if not success:
                failed.append(key)
        if failed:
            log.warning(
                f"Following tiles failed to save: {failed}", failed_tiles=failed)
            return False
        return True

    @staticmethod
    def prune_found_ids(tile_ids: list, redis, area):
        """Returns tile_ids list with tile_ids removed that are already found in redis

        Args:
            tile_ids (list): list of tile_ids
            redis (_type_): redis object

        Returns:
            pruned_tile_ids(list): list of ids that were not found in redis
        """

        pruned = []
        for tile_id in tile_ids:
            key = f"{area.area}_{tile_id}"
            if not redis.exists(key):
                pruned.append(tile_id)
        return pruned

    @staticmethod
    def get_gdf_by_list_of_keys(tile_ids: list, redis, area):
        """Returns a GeoDataFrame consisting of edges found in redis
           specified by list of tile_ids that are given as args

        Args:
            tile_ids (list): List of tile_ids that are needed to be made to gdf
            redis (_type_): redis object

        Returns:
            GeoDataFrame or bool:
            : GeoDataFrame consisting of edges with specified tile_ids
            : False if no valid features were found in Redis
        """
        features = []
        expired = []

        for tile_id in tile_ids:
            key = f"{area.area}_{tile_id}"
            geojson = redis.get_geojson(key)
            if not geojson:
                log.warning(
                    f"Redis: missing key {key}", key=key)
                continue
            features.extend(geojson.get("features", []))

        if not features:
            return False, expired
        gdf = gpd.GeoDataFrame.from_features(features, crs=area.crs)
        return gdf, expired
