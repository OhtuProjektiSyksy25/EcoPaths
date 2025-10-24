"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Polygon
from config.settings import AreaConfig, get_settings
from core.route_algorithm import RouteAlgorithm
from core.edge_enricher import EdgeEnricher
from database.db_client import DatabaseClient
from services.redis_cache import RedisCache
from services.geo_transformer import GeoTransformer
from utils.route_summary import summarize_route
from utils.redis_utils import RedisUtils


class RouteServiceFactory:
    """
    Factory for creating RouteService instances with area-specific configuration.

    Provides a static method to initialize a routing service and return its AreaConfig.
    """
    @staticmethod
    def from_area(area: str) -> tuple["RouteService", "AreaConfig"]:
        """
        Create a RouteService instance and return it with its corresponding AreaConfig.

        Initializes a RouteService for the specified area using dynamic settings
        loaded via `get_settings(area)`.

        Args:
            area (str): Name of the area (e.g., "berlin", "helsinki").

        Returns:
            tuple: A tuple containing:
                - RouteService: The initialized routing service for the area.
                - AreaConfig: The configuration object for the specified area.
        """
        route_service = RouteService(area)
        return route_service, get_settings(area).area


class RouteService:
    """
    Service for computing optimal routes between two points using spatial edge data.

    This class dynamically loads edge data from Redis or enriches it if missing,
    computes route variants (fastest, cleanest, balanced), and returns results
    as GeoJSON FeatureCollections with summaries.
    """

    def __init__(self, area: str):
        """
        Initialize the RouteService with dynamic tile loading.

        Args:
            area (str): Area name (e.g., 'berlin').
        """
        settings = get_settings(area)

        self.area_config = settings.area
        self.area = area
        self.redis = RedisCache()
        self.db_client = DatabaseClient()
        self.edge_enricher = EdgeEnricher(area)

    def get_route(self, origin_gdf: gpd.GeoDataFrame, destination_gdf: gpd.GeoDataFrame) -> dict:
        """Main entrypoint: compute route and return routes + summaries.

        Args:
            origin_gdf (GeoDataFrame): GeoDataFrame with origin point.
            destination_gdf (GeoDataFrame): GeoDataFrame with destination point.

        Returns:
            dict: GeoJSON FeatureCollection and route summaries.
        """
        buffer = self._create_buffer(origin_gdf, destination_gdf)
        tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)

        # Get edges for relevant tiles (Redis + enrich new tiles if needed)
        edges = self._get_tile_edges(tile_ids)

        if edges is None or edges.empty:
            raise RuntimeError("No edges found for requested route area.")

        return self._compute_routes(edges, origin_gdf, destination_gdf)

    def _create_buffer(self, origin_gdf, destination_gdf, buffer_m=400) -> Polygon:
        """
        Creates a buffer polygon around a straight line between origin and destination points.

        Args:
            origin_gdf (GeoDataFrame): 
                GeoDataFrame containing the origin point geometry.
            destination_gdf (GeoDataFrame): 
                GeoDataFrame containing the destination point geometry.
            buffer_m (float, optional): 
                Buffer radius in coordinate units (typically meters). Defaults to 400.

        Returns:
            Polygon: A Shapely polygon representing the buffered area around 
            the origin-destination line.
        """
        line = LineString([
            origin_gdf.geometry.iloc[0],
            destination_gdf.geometry.iloc[0]
        ])
        return line.buffer(buffer_m)

    def _get_tile_edges(self, tile_ids: list) -> gpd.GeoDataFrame:
        """
        Fetch edges for the given tile_ids, using Redis cache or EdgeEnricher if missing.

        Args:
            tile_ids (list): List of tile_ids intersecting route buffer.

        Returns:
            GeoDataFrame: Edges for requested tiles.
        """
        # Prune tiles already in Redis
        non_existing_tile_ids = RedisUtils.prune_found_ids(
            tile_ids, self.redis)
        existing_tile_ids = list(set(tile_ids) - set(non_existing_tile_ids))

        all_gdfs = []

        # Load existing tiles from Redis
        if existing_tile_ids:
            found_gdf, expired_tiles = RedisUtils.get_gdf_by_list_of_keys(
                existing_tile_ids, self.redis)
            non_existing_tile_ids = list(
                set(non_existing_tile_ids + expired_tiles))
            if found_gdf is not False:
                all_gdfs.append(found_gdf)

        # Enrich and save missing tiles
        if non_existing_tile_ids:
            RedisUtils.edge_enricher_to_redis_handler(
                non_existing_tile_ids, self.redis)
            new_gdf, _ = RedisUtils.get_gdf_by_list_of_keys(
                non_existing_tile_ids, self.redis)
            if new_gdf is not False:
                all_gdfs.append(new_gdf)

        if all_gdfs:
            return pd.concat(all_gdfs, ignore_index=True)

        return None

    def _compute_routes(self, edges, origin_gdf, destination_gdf):
        """Compute multiple route variants and summaries."""
        edges["combined_score"] = 0.5 * edges["length_m"] + 0.5 * edges["aqi"]

        modes = {
            "fastest": "length_m",
            "best_aq": "aqi",
            "balanced": "combined_score"
        }

        algo = RouteAlgorithm(edges)
        results, summaries = {}, {}

        for mode, weight in modes.items():
            gdf = algo.calculate_path(
                origin_gdf, destination_gdf, weight=weight)
            gdf["mode"] = mode
            summaries[mode] = summarize_route(gdf)
            results[mode] = GeoTransformer.gdf_to_feature_collection(
                gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
            )

        return {"routes": results, "summaries": summaries}
