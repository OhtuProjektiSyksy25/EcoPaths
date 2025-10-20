"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""
import geopandas as gpd
from shapely.geometry import LineString, Polygon
from core.edge_enricher import EdgeEnricher
from core.route_algorithm import RouteAlgorithm
from config.settings import AreaConfig
from services.redis_cache import RedisCache
from services.geo_transformer import GeoTransformer
from utils.route_summary import summarize_route
from utils.redis_utils import RedisUtils


class RouteService:
    """
    Service for computing optimal routes and returning them as GeoJSON Features.
    """

    def __init__(self, edges: gpd.GeoDataFrame, redis=None):
        """
        Initialize the RouteService.

        Args:
            edges (gpd.GeoDataFrame): GeoDataFrame containing road network edges.
            redis (RedisCache, optional): Redis cache instance for caching routes.
        """
        self.edges = edges
        self.redis = redis or RedisCache()

    def get_route(self, origin_gdf: gpd.GeoDataFrame, destination_gdf: gpd.GeoDataFrame) -> dict:
        """Gets route to destination from origin.

        Args:
            origin_gdf (gpd.GeoDataFrame): GeoDataFrame containing the origin point.
            destination_gdf (gpd.GeoDataFrame): GeoDataFrame containing the destination point.

        Returns:
            dict: GeoJSON Feature representing the computed route.
        """

        buffer = self._create_buffer(
            origin_gdf, destination_gdf, buffer_m=500)

        # unique tile_id inside bufferzone
        tile_ids = self.edges[self.edges.intersects(
            buffer)]["tile_id"].unique()

        # PLACEHOLDER when cached + new tiles is ready in redis/redis handler layer
        edges_subset = self._get_tile_edges(tile_ids)
        # algorithm = RouteAlgorithm(edges_subset)

        # Filter edges based on buffer
        # edges_subset = self.edges[self.edges.intersects(buffer)].copy()
        algorithm = RouteAlgorithm(edges_subset)

        # example for balanced route
        edges_subset["combined_score"] = (
            0.3 * edges_subset["length_m"] + 0.7 * edges_subset["aqi"]
        )

        # mode: weight column
        route_modes = {
            "fastest": "length_m",
            "best_aq": "aqi",
            "balanced": "combined_score"
        }

        routes = {}
        summaries = {}

        for mode, weight in route_modes.items():
            route_gdf = algorithm.calculate_path(
                origin_gdf, destination_gdf, weight=weight)
            route_gdf["mode"] = mode

            summaries[mode] = summarize_route(route_gdf)

            props = [col for col in route_gdf.columns if col != "geometry"]
            routes[mode] = GeoTransformer.gdf_to_feature_collection(
                route_gdf, property_keys=props
            )

        response = {
            "routes": routes,
            "summaries": summaries
        }

        return response

    def _create_buffer(self, origin_gdf: gpd.GeoDataFrame, destination_gdf: gpd.GeoDataFrame,
                       buffer_m: float = 400) -> Polygon:
        """
        Creates a buffer polygon around a straight line between origin and destination points.

        Args:
            origin_gdf (GeoDataFrame): GeoDataFrame with a single Point geometry (start).
            destination_gdf (GeoDataFrame): GeoDataFrame with a single Point geometry (end).
            buffer_m (float, optional): Buffer radius in meters around the line. Defaults to 400.

        Returns:
            Polygon: A polygon representing the buffered area around the route line.
        """

        origin_point = origin_gdf.geometry.iloc[0]
        destination_point = destination_gdf.geometry.iloc[0]

        line = LineString([origin_point, destination_point])
        return line.buffer(buffer_m)

    def _get_tile_edges(self, tile_ids: list):  # rename function?
        """Checks redis for tile_id hits according to tile_ids. Saves enriched tiles/edges to redis
       that were not already present in redis.
           Creates and returns a GeoDataFrame of all the edges
           contained in tiles specified in tile_ids

        Args:
            tile_ids (list): List of tile_id that are used to pick edges for returned GeoDataFrame

        Returns:
            GeoDataFrame: GeoDataFrame
        """
        non_existing_tile_ids = RedisUtils.prune_found_ids(
            tile_ids, self.redis)
        if RedisUtils.edge_enricher_to_redis_handler(
            non_existing_tile_ids,
            self.redis
        ):
            route_ready_gdf = RedisUtils.get_gdf_by_list_of_keys(
                tile_ids, self.redis)
            return route_ready_gdf
        # error handling needed

        return None


class RouteServiceFactory:
    """
    Factory class for creating RouteService instances based on area name.

    This class loads the appropriate road network data for the given area
    and returns a configured RouteService instance.
    """
    @staticmethod
    def from_area(area: str) -> tuple[RouteService, AreaConfig]:
        """
        Create a RouteService instance for a specific area.

        Args:
            area (str): Name of the area (e.g., "berlin").

        Returns:
            RouteService: A service instance initialized with the area's road network.
        """
        try:
            model = EdgeEnricher(area)
            edges = model.load_all_edges()
            # tiles = model.get_tiles()
            area_config = model.area_config
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"\nRouteServiceFactory failed: edges file for area '{area}' not found.\n"
                f"Expected file: {e.filename}\n"
                f"Please run the preprocessing step to generate the required file.\n"
                f"Example: `invoke preprocess-osm --area={area}`\n"
            ) from e

        return RouteService(edges), area_config

