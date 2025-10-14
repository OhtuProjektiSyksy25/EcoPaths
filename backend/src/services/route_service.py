"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""
import geopandas as gpd
from shapely.geometry import mapping
from core.edge_enricher import EdgeEnricher
from core.algorithm.route_algorithm import RouteAlgorithm
from services.redis_cache import RedisCache


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

    def get_route(self, origin: tuple, destination: tuple) -> dict:
        """
        Compute the optimal route between two points as a GeoJSON Feature.

        Args:
            origin (tuple): Starting point as (lon, lat)
            destination (tuple): Ending point as (lon, lat)

        Returns:
            dict: GeoJSON Feature representing the route
        """

        cache_key = f"route_{origin[0]}_{origin[1]}_{destination[0]}_{destination[1]}"
        cached_route = self.redis.get(cache_key)
        if cached_route:
            return cached_route

        algorithm = RouteAlgorithm(self.edges)
        route_gdf = algorithm.calculate(origin, destination)

        if route_gdf.crs is None or route_gdf.crs.to_string() != "EPSG:4326":
            route_gdf = route_gdf.to_crs("EPSG:4326")

        unified_geom = route_gdf.geometry.union_all()
        length_m = route_gdf.to_crs("EPSG:3857").geometry.length.sum()
        time_estimate_formatted = self._calculate_time_estimate(length_m)

        geojson_feature = {
            "type": "Feature",
            "geometry": mapping(unified_geom),
            "properties": {
                "time_estimate": time_estimate_formatted,
                "length_m": length_m
            }
        }

        self.redis.set(cache_key, geojson_feature)
        return geojson_feature

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
    def from_area(area: str) -> RouteService:
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
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"\nRouteServiceFactory failed: edges file for area '{area}' not found.\n"
                f"Expected file: {e.filename}\n"
                f"Please run the preprocessing step to generate the required file.\n"
                f"Example: `invoke preprocess-osm --area={area}`\n"
            ) from e

        return RouteService(edges)
