"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""
import geopandas as gpd
from core.edge_enricher import EdgeEnricher
from core.algorithm.route_algorithm import RouteAlgorithm
from config.settings import AreaConfig
from services.redis_cache import RedisCache
from services.geo_transformer import GeoTransformer
from utils.time_format import format_walk_time


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

        cached_route = self.redis.get(cache_key)
        if cached_route:
            return cached_route

        algorithm = RouteAlgorithm(self.edges)
        route_gdf = algorithm.calculate(origin, destination)

        # Workaround — RouteAlgorithm returns only merged LineString without edge attributes
        # Replace when RouteAlgorithm returns edge-level GeoDataFrame.
        # Change when RouteAlgorithm returns 'length_m' column
        route_gdf = route_gdf.to_crs("EPSG:3857")
        total_length_m = float(route_gdf.geometry.length.sum())
        formatted_time = format_walk_time(total_length_m)
        route_gdf["dummy"] = "ok"
        geojson_feature = GeoTransformer.gdf_to_feature_collection(
            route_gdf, property_keys=["dummy"])

        response = {
            "route": geojson_feature,
            "summary": {
                "length_m": total_length_m,
                "time_estimate": formatted_time
            }
        }

        self.redis.set(cache_key, response)
        return response


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
            model.load_data()
            edges = model.get_enriched_edges()
            area_config = model.area_config
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"\nRouteServiceFactory failed: edges file for area '{area}' not found.\n"
                f"Expected file: {e.filename}\n"
                f"Please run the preprocessing step to generate the required file.\n"
                f"Example: `invoke preprocess-osm --area={area}`\n"
            ) from e

        return RouteService(edges), area_config
