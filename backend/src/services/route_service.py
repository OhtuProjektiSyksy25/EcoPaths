"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""
import geopandas as gpd
from shapely.geometry import LineString, Polygon
from core.edge_enricher import EdgeEnricher
from core.algorithm.route_algorithm import RouteAlgorithm
from config.settings import AreaConfig
from services.redis_cache import RedisCache
from services.geo_transformer import GeoTransformer
from utils.route_summary import format_walk_time


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
        # uncomment after RouteAlgorithm supports GeoDataFrame inputs
        # origin = origin_gdf.geometry.iloc[0]
        # destination = destination_gdf.geometry.iloc[0]
        # cache_key = (
        #     f"route_{round(origin.x, 4)}_{round(origin.y, 4)}_"
        #     f"{round(destination.x, 4)}_{round(destination.y, 4)}"
        # )

        # Workaround remove when RouteAlgorithm supports GeoDataFrame inputs
        origin, destination = RouteService.extract_lonlat_from_gdf(
            origin_gdf, destination_gdf)
        cache_key = (
            f"route_{round(origin[0], 4)}_{round(origin[1], 4)}_"
            f"{round(destination[0], 4)}_{round(destination[1], 4)}"
        )
        # ----

        cached_route = self.redis.get(cache_key)
        if cached_route:
            return cached_route

        # uncomment and make it work when tiles_ids are available in edges and
        # RouteAlgorithm returns edge-level GeoDataFrame output
        # buffer = self._create_buffer(origin, destination, buffer_m=1000)
        # tile_ids = self.tiles[self.tiles.intersects(buffer)]["tile_id"].unique()
        # edges_subset = self.edges[self.edges["tile_id"].isin(tile_ids)]

        # edges_subset["combined_score"] = (
        #     0.5 * edges_subset["length_m"] + 0.5 * edges_subset["aq_value"]
        # )

        # # mode: weight column
        # route_modes = {
        #     "fastest": "length_m",
        #     "best_aq": "aq_value",
        #     "balanced": "combined_score"
        # }

        # routes = {}
        # summaries = {}

        # algorithm = RouteAlgorithm(edges_subset)
        # route_gdf = algorithm.calculate(origin, destination)

        # for mode, weight in route_modes.items():
        #     route_gdf = algorithm.calculate_path(origin, destination, weight=weight)
        #     route_gdf["mode"] = mode

        #     summaries[mode] = summarize_route(route_gdf)

        #     props = [col for col in route_gdf.columns if col != "geometry"]
        #     routes[mode] = GeoTransformer.gdf_to_feature_collection(
        #         route_gdf, property_keys=props
        #     )

        # response = {
        #     "routes": routes,
        #     "summaries": summaries
        # }

        # Workaround — RouteAlgorithm returns only merged LineString without edge attributes
        # Replace when RouteAlgorithm returns edge-level GeoDataFrame.
        # Change when RouteAlgorithm returns 'length_m' column
        algorithm = RouteAlgorithm(self.edges)
        route_gdf = algorithm.calculate(origin, destination)
        route_gdf = route_gdf.to_crs("EPSG:3857")
        total_length_m = float(route_gdf.geometry.length.sum())
        formatted_time = format_walk_time(total_length_m)
        route_gdf["dummy"] = "ok"
        geojson_feature = GeoTransformer.gdf_to_feature_collection(
            route_gdf, property_keys=["dummy"])

        fastest_route_gdf = fastest_route_gdf.to_crs("EPSG:3857")
        fastest_aq_route_gdf = fastest_aq_route_gdf.to_crs("EPSG:3857")
        total_length_m_fastest = fastest_route_gdf.geometry.length.sum()
        total_length_m_fastest_aq = fastest_aq_route_gdf.geometry.length.sum()
        formatted_time_fastest = format_walk_time(total_length_m_fastest)
        formatted_time_fastest_aq = format_walk_time(total_length_m_fastest_aq)
        fastest_route_gdf["dummy"] = "ok"
        fastest_aq_route_gdf["dummy"] = "ok"

        geojson_feature_fastest = GeoTransformer.gdf_to_feature_collection(
            fastest_route_gdf, property_keys=["dummy"])
        response_fastest = {
            "route": geojson_feature_fastest,
            "summary": {
                "length_m": total_length_m_fastest,
                "time_estimate": formatted_time_fastest
            }
        }
        geojson_feature_fastest_aq = GeoTransformer.gdf_to_geojson_feature_collection(
            fastest_aq_route_gdf, property_keys=["dummy"])
        response_aq = {
            "route": geojson_feature_fastest_aq,
            "summary": {
                "length_m": total_length_m_fastest_aq,
                "time_estimate": formatted_time_fastest_aq
            }
        }
        # -----

        self.redis.set(cache_key, response_fastest)
        self.redis.set(cache_key, response_aq)
        return response_fastest, response_aq

    # Remove extract_lonlat_from_gdf once RouteAlgorithm supports GeoDataFrame inputs
    def _create_buffer(self, origin_point, destination_point, buffer_m=1000) -> Polygon:
        """
        Creates a buffer polygon around a straight line between origin and destination points.

        Args:
            origin_point (Point): Starting point of the route.
            destination_point (Point): Ending point of the route.
            buffer_m (int, optional): Buffer radius in meters around the line. Defaults to 1000.

        Returns:
            Polygon: A polygon representing the buffered area around the route line.
        """
        return LineString([origin_point, destination_point]).buffer(buffer_m)

# Remove extract_lonlat_from_gdf once RouteAlgorithm supports GeoDataFrame inputs
    @staticmethod
    def extract_lonlat_from_gdf(
        origin_gdf: gpd.GeoDataFrame,
        destination_gdf: gpd.GeoDataFrame
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """
        TEMPORARY: Extract (lon, lat) tuples from GeoDataFrames by transforming to WGS84.
        Remove when RouteAlgorithm supports GeoDataFrame inputs directly.
        """
        origin_wgs = origin_gdf.to_crs("EPSG:4326").geometry.iloc[0]
        destination_wgs = destination_gdf.to_crs("EPSG:4326").geometry.iloc[0]
        return (origin_wgs.x, origin_wgs.y), (destination_wgs.x, destination_wgs.y)

    def _calculate_time_estimate(self, length_m: float) -> str:
        """
        Calculate formatted time estimate from distance.

        Args:
            length_m (float): Distance in meters

        Returns:
            str: Formatted time estimate (e.g., "1h 5 min" or "15 min 30 s")
        """
        avg_speed_mps = 1.4  # 1.4 meters per second (walking speed)
        seconds = length_m / avg_speed_mps

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes} min"
        return f"{minutes} min {remaining_seconds} s"


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
            edges = model.get_enriched_edges()
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
