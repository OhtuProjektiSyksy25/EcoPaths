"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""

import geopandas as gpd
from shapely.geometry import mapping, LineString
from core.compute_model import ComputeModel
from core.algorithm.route_algorithm import RouteAlgorithm
from services.redis_cache import RedisCache

# Cache key template now includes origin and destination coordinates
CACHE_KEY_TEMPLATE = "route_{area}_{from_lon}_{from_lat}_{to_lon}_{to_lat}"


class RouteService:
    """
    Service for computing optimal routes and returning them as GeoJSON Features.

    Attributes:
        area (str): Name of the area (lowercased).
        compute_model (ComputeModel): Instance of ComputeModel to get edge data.
    """

    def __init__(self, area: str = "berlin"):
        """
        Initialize RouteService with a specific area.

        Args:
            area (str): Name of the area (default "berlin").
        """
        self.area = area.lower()
        self.compute_model = ComputeModel(area=self.area)
        self.redis = RedisCache()

    def get_route(self, origin: tuple, destination: tuple) -> dict:
        """
        Compute the optimal route between two points as a GeoJSON Feature.

        Args:
            origin (tuple): Starting point as (lon, lat)
            destination (tuple): Ending point as (lon, lat)

        Returns:
            dict: GeoJSON Feature representing the route, e.g.
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[13.404954, 52.520008], [13.4062, 52.521]]
                    },
                    "properties": {}
                }
        """

        # Generate a unique cache key for this route
        # example: route_berlin_13.404954_52.520008_13.4062_52.521
        cache_key = CACHE_KEY_TEMPLATE.format(
            area=self.area,
            from_lon=origin[0],
            from_lat=origin[1],
            to_lon=destination[0],
            to_lat=destination[1]
        )

        # Try to fetch the route from cache first
        cached_route = self.redis.get(cache_key)
        if cached_route:
            return cached_route

        # If not in cache, compute the edges from ComputeModel
        edges = self.compute_model.get_data_for_algorithm()


        algorithm = RouteAlgorithm(edges)

#        algorithm = RouteAlgorithm(edges)
        route_gdf = algorithm.calculate(origin, destination)

        # Ensure the route is in EPSG:4326
        if route_gdf.crs is None or route_gdf.crs.to_string() != "EPSG:4326":
            route_gdf = route_gdf.to_crs("EPSG:4326")

        # Merge all geometries into a single LineString
        unified_geom = route_gdf.geometry.union_all()

        #calculate time estimate
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
        # Save the completed route to Redis cache
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
        avg_speed_mps = 1.4  # 5 meters per second (walking speed)
        seconds = length_m / avg_speed_mps

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes} min"
        return f"{minutes} min {remaining_seconds} s"
