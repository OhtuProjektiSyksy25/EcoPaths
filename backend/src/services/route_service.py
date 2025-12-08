"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Polygon
from config.settings import AreaConfig, get_settings
from logger.logger import log
from core.route_algorithm import RouteAlgorithm
from core.edge_enricher import EdgeEnricher
from database.db_client import DatabaseClient
from services.redis_cache import RedisCache
from services.redis_service import RedisService
from utils.route_summary import summarize_route
from utils.geo_transformer import GeoTransformer
from utils.aqi_comparison_utils import calculate_aqi_difference
from utils.exposure_calculator import compute_exposure


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

    def __init__(self, area: str, network_type: str = "walking"):
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
        self.network_type = network_type
        self.current_route_algorithm = None

    def get_route(self, origin_gdf: gpd.GeoDataFrame, destination_gdf: gpd.GeoDataFrame,
                  balanced_value: float = 0.5, buffer_m=600) -> dict:
        """
        Main entrypoint: compute route and return routes + summaries.

            Args:
                origin_gdf (GeoDataFrame): GeoDataFrame with origin point.
                destination_gdf (GeoDataFrame): GeoDataFrame with destination point.
                balanced_weight (float): Weight for balanced route (0.0 = fastest, 1.0 = best AQ).

        Returns:
            dict: GeoJSON FeatureCollection and route summaries.
        """
        for buffer_length in [buffer_m, buffer_m+300, buffer_m+600]:
            try:
                buffer = self.create_buffer(
                    origin_gdf, destination_gdf, buffer_length)
                tile_ids = self.db_client.get_tile_ids_by_buffer(
                    self.area, buffer)
                # Get edges for relevant tiles (Redis + enrich new tiles if needed)
                edges = self.get_tile_edges(tile_ids)
                # Nodes_gdf from database
                nodes = self.get_nodes_from_db(tile_ids)

                if edges is None or edges.empty:
                    log.warning(f"No edges found with buffer {buffer_length}m")
                    continue

                edges_subset = edges[edges.geometry.intersects(buffer)].copy()

                if edges_subset.empty:
                    log.warning(
                        f"No edges intersect buffer with {buffer_length}m")
                    continue

                if nodes is None or nodes.empty:
                    log.warning(f"No nodes found with buffer {buffer_length}m")
                    continue

                return self._compute_routes(
                    edges_subset, nodes, origin_gdf, destination_gdf, balanced_value
                )

            except Exception as e:  # pylint: disable=broad-exception-caught
                log.warning(
                    f"Routing failed with buffer {buffer_length}m: {e}")
                continue

        raise RuntimeError(
            "No route found. Try a different location or larger area.")

    def create_buffer(self, origin_gdf, destination_gdf, buffer_m=600) -> Polygon:
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
        origin_point = origin_gdf.geometry.iloc[0]
        destination_point = destination_gdf.geometry.iloc[0]

        if origin_point == destination_point:
            return origin_point.buffer(buffer_m)

        line = LineString([
            origin_point,
            destination_point
        ])
        return line.buffer(buffer_m)

    def get_tile_edges(self, tile_ids: list) -> gpd.GeoDataFrame:
        """Fetch edges for given tile_ids from Redis or enrich if missing."""
        non_existing_tile_ids = RedisService.prune_found_ids(
            tile_ids, self.redis, self.area_config)
        existing_tile_ids = list(set(tile_ids) - set(non_existing_tile_ids))

        all_gdfs = []
        if existing_tile_ids:
            found_gdf, expired_tiles = RedisService.get_gdf_by_list_of_keys(
                existing_tile_ids, self.redis, self.area_config)
            non_existing_tile_ids = list(
                set(non_existing_tile_ids + expired_tiles))
            if found_gdf is not False:
                all_gdfs.append(found_gdf)

        if non_existing_tile_ids:
            enriched_gdf = self._enrich_missing_edges(non_existing_tile_ids)
            if enriched_gdf is not None and not enriched_gdf.empty:
                all_gdfs.append(enriched_gdf)

        if all_gdfs:
            return pd.concat(all_gdfs, ignore_index=True)

        return gpd.GeoDataFrame(columns=["geometry"], crs=self.area_config.crs)

    def _enrich_missing_edges(self, missing_tile_ids: list) -> gpd.GeoDataFrame:
        """Enrich missing tiles using EdgeEnricher and save to Redis."""
        enricher = EdgeEnricher(area=self.area)
        new_gdf = enricher.get_enriched_tiles(
            missing_tile_ids, network_type=self.network_type)
        if new_gdf is not False and new_gdf is not None and not new_gdf.empty:
            saved = RedisService.save_gdf(
                new_gdf, self.redis, self.area_config)
            if not saved:
                log.warning("Failed to save enriched tiles to Redis.")
            return new_gdf
        log.warning("Enrichment failed or returned empty. Skipping save.")
        return gpd.GeoDataFrame(columns=["geometry"], crs=self.area_config.crs)

    def get_tile_ids_by_buffer(self, buffer):
        """
        Fetch tile IDs that intersect with the given buffer polygon.

        Args:
            buffer (Polygon): Buffer polygon around origin-destination line.

        Returns:
            list: Tile identifiers that intersect with the buffer.
        """
        return self.db_client.get_tile_ids_by_buffer(self.area, buffer)

    def get_nodes_from_db(self, tile_ids: list) -> gpd.GeoDataFrame:
        """
        Fetch nodes for the given tile_ids from the database.

        Args:
            tile_ids (list): List of tile_ids intersecting route buffer.

        Returns:
            GeoDataFrame: Nodes for requested tiles.
        """
        result = self.db_client.get_nodes_by_tile_ids(
            self.area_config.area,
            self.network_type,
            tile_ids
        )
        if result is None or result.empty:
            return gpd.GeoDataFrame(columns=["geometry"], crs=self.area_config.crs)
        return result

    def _compute_routes(self, edges, nodes, origin_gdf, destination_gdf, balanced_value=0.5):
        """Compute multiple route variants and summaries."""

        if 'geometry' not in edges.columns or edges.empty:
            raise RuntimeError(
                "Edges GeoDataFrame has no geometry column or is empty")

        if 'geometry' not in nodes.columns or nodes.empty:
            raise RuntimeError(
                "Nodes GeoDataFrame has no geometry column or is empty")

        modes = {
            "fastest": 1,
            "best_aq": 0,
            "balanced": balanced_value
        }

        self.current_route_algorithm = RouteAlgorithm(edges, nodes)
        results, summaries = {}, {}

        for mode, balance_factor in modes.items():
            gdf = self.current_route_algorithm.calculate_path(
                origin_gdf, destination_gdf, graph=None, balance_factor=balance_factor)
            gdf = compute_exposure(gdf)
            gdf["mode"] = mode
            summaries[mode] = summarize_route(gdf)
            results[mode] = GeoTransformer.gdf_to_feature_collection(
                gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
            )

        aqi_differences = calculate_aqi_difference(summaries)

        return {
            "routes": results,
            "summaries": summaries,
            "aqi_differences": aqi_differences
        }

    def compute_balanced_route_only(self, origin_gdf: gpd.GeoDataFrame,
                                    destination_gdf: gpd.GeoDataFrame,
                                    balanced_value: float) -> dict:
        """
        Computes only the "balanced route" for the given balanced_value.
        Works statelessly by rebuilding the graph from scratch each time.

        Args:
            origin_gdf (GeoDataFrame): Origin point.
            destination_gdf (GeoDataFrame): Destination point.
            balanced_value (float): Weight for balanced route (0.0 = fastest, 1.0 = best AQ).

        Returns:
            dict: Contains routes, summaries, and aqi_differences keys.
        """
        buffer = self.create_buffer(origin_gdf, destination_gdf)
        tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)

        edges = self.get_tile_edges(tile_ids)
        nodes = self.get_nodes_from_db(tile_ids)

        if edges is None or edges.empty:
            raise RuntimeError("No edges found for requested route area.")

        edges_subset = edges[edges.geometry.intersects(buffer)].copy()

        if edges_subset.empty:
            raise RuntimeError("No edges intersect the requested buffer area.")

        route_algorithm = RouteAlgorithm(edges_subset, nodes)

        gdf = route_algorithm.calculate_path(
            origin_gdf,
            destination_gdf,
            graph=None,
            balance_factor=balanced_value
        )

        gdf = compute_exposure(gdf)
        gdf["mode"] = "balanced"

        summary = summarize_route(gdf)
        result = GeoTransformer.gdf_to_feature_collection(
            gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
        )

        results, summaries, aqi_differences = {}, {}, {}
        results["balanced"] = result
        summaries["balanced"] = summary
        aqi_differences["aqi_differences"] = None

        return {"routes": results, "summaries": summaries, "aqi_differences": aqi_differences}
