"""
Utility module for handling, saving and fetching of GeoDataFrame/geojson data to and from redis

"""
import geopandas as gpd
from services.geo_transformer import GeoTransformer
from services.redis_cache import RedisCache
from core.edge_enricher import EdgeEnricher



class RedisUtils:
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
        grouped_by_id = {dict_key: group for dict_key, group in gdf.groupby("tile_id")}
        return grouped_by_id

    @staticmethod
    def save_gdf(gdf: gpd.GeoDataFrame, redis):
        """Groups given gdf by tile_id and saves each group to redis as 
        Key: tile_id, value: FeatureCollecion

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame to be saved to redis
            redis : Redis object that is being saved to

        Returns:
            True: Returns True if saving is successful
            False: Returns False if saving is not succesful
        """
        tile_grouped_gdf_dict = RedisUtils.group_gdf_by_tile(gdf)
        failed_to_save = []
        for tile_id, gdf in tile_grouped_gdf_dict.items():
            gdf = gdf.to_crs("EPSG:4326")
            tile_grouped_featurecollection = gdf.to_json()
            attempt = redis.set_direct(tile_id, tile_grouped_featurecollection, 3600)
            if attempt == False:
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
    def get_gdf_by_list_of_keys(tile_ids:list, redis):
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
        for tile_id in tile_ids:
            new_geojson = redis.get_geojson(tile_id)
            if not new_geojson:
                print(f"Error, redis could not find value for key: {tile_id} ")
                #Add function to handle key expiring during other tile_id enriching -> if not found given tile is routed to edgeenritcher(?)
                continue
            features.extend(new_geojson.get("features", []))

        if not features:
            return False
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        return gdf
    
    @staticmethod
    def edge_enricher_to_redis_handler(self, tile_ids:list, redis):
        """Sends tiles to EdgeEnricher and saves returned gdf to redis

        Args:
            tile_ids (list): List of tile_ids to be enritched
            redis (_type_): Redis object

        Returns:
            True: if saving is succesful
            False: if saving is not succesful
        """
        gdf = EdgeEnricher.enrich_tiles(tile_ids)
        #add check when EdgeEnricher is finished
        if RedisUtils.save_gdf(gdf, redis):
            return True
        return False