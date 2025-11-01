"""
Utility module for handling, saving and fetching of GeoDataFrame/geojson data to and from redis
"""
import geopandas as gpd
from core.edge_enricher import EdgeEnricher


class RedisService:
    """
    A utility class for interacting with redis,
    """
    @staticmethod
    def group_gdf_by_tile(gdf: gpd.GeoDataFrame):
        """
        Groups GeoDataFrame by 'tile_id' and return dict of key:tile_id, value:geodataframe

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame object

        Returns:
            dictionary: key: tile_id, value: GeoDataFrame

        """
        grouped_by_id = {dict_key: group for dict_key, group in gdf.groupby(  # pylint: disable=unnecessary-comprehension
            "tile_id")}  # pylint: disable=unnecessary-comprehension
        return grouped_by_id

    @staticmethod
    def save_gdf(gdf: gpd.GeoDataFrame, redis, area):
        """Groups given gdf by tile_id and saves each group to redis as 
        Key: tile_id, value: FeatureCollecion

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame to be saved to redis
            redis : Redis object that is being saved to

        Returns:
            True: Returns True if saving is successful
            False: Returns False if saving is not succesful
        """
        tile_grouped_gdf_dict = RedisService.group_gdf_by_tile(gdf)
        failed_to_save = []
        for tile_id, current_gdf in tile_grouped_gdf_dict.items():
            gdf = current_gdf.to_crs(area.crs)
            tile_grouped_featurecollection = gdf.to_json()
            attempt = redis.set_direct(
                tile_id, tile_grouped_featurecollection, 3600)
            if attempt is False:
                failed_to_save.append(tile_id)
        if len(failed_to_save) > 0:
            print(f"following tiles failed to save: {failed_to_save}")
            return False
        return True

    @staticmethod
    def prune_found_ids(tile_ids: list, redis):
        """Returns tile_ids list with tile_ids removed that are already found in redis

        Args:
            tile_ids (list): list of tile_ids
            redis (_type_): redis object

        Returns:
            pruned_tile_ids(list): list of ids that were not found in redis
        """

        pruned_tile_ids = []
        for tile_id in tile_ids:
            if not redis.exists(tile_id):
                pruned_tile_ids.append(tile_id)
        return pruned_tile_ids

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
        expired_tiles = []
        for tile_id in tile_ids:
            new_geojson = redis.get_geojson(tile_id)
            if not new_geojson:
                print(f"Error, redis could not find value for key: {tile_id} ")
                expired_tiles.append(tile_id)
                continue
            features.extend(new_geojson.get("features", []))

        if len(features) == 0:
            return False, expired_tiles
        gdf = gpd.GeoDataFrame.from_features(features, crs=area.crs)
        return gdf, expired_tiles
