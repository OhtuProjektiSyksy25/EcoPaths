"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""

import geopandas as gpd
from shapely.geometry import mapping, LineString
from core.compute_model import ComputeModel
# from core.algorithm import RouteAlgorithm  # Uncomment when ready
from services.redis_cache import RedisCache

# Cache key template now includes origin and destination coordinates
CACHE_KEY_TEMPLATE = "route_{area}_{from_lon}_{from_lat}_{to_lon}_{to_lat}"


class RouteService:
    """
    Service that computes routes and returns them as GeoJSON LineStrings.
    CRS: EPSG:4326 (lon/lat), ready for Mapbox or Leaflet.
    Routes are cached in Redis to avoid recalculation.
    """

    def __init__(self, area: str = "berlin"):
        self.area = area.lower()
        self.compute_model = ComputeModel(area=self.area)
        self.redis = RedisCache()

    def get_route(self, origin: tuple, destination: tuple) -> dict:
        """
        Computes a route from origin to destination.
        Returns GeoJSON Feature, and caches it in Redis for next use.

        Args:
            origin (tuple): (lon, lat)
            destination (tuple): (lon, lat)

        Returns:
            dict: GeoJSON Feature of the route
        """

        # Generate a unique cache key for this route
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

        # Temporary stub algorithm: replace with RouteAlgorithm later
        class StubAlgorithm:
            """
            A temporary stub algorithm for route computation.
            """
            def __init__(self, edges):
                self.edges = edges

            def compute(self, origin, destination):
                """Return a simple dummy LineString from origin to destination"""
                return gpd.GeoDataFrame(
                    [{"geometry": LineString([origin, destination])}],
                    geometry="geometry",
                    crs="EPSG:4326"
                )

        algorithm = StubAlgorithm(edges)
        route_gdf = algorithm.compute(origin, destination)

        # Ensure the route is in EPSG:4326
        if route_gdf.crs is None or route_gdf.crs.to_string() != "EPSG:4326":
            route_gdf = route_gdf.to_crs("EPSG:4326")

        # Merge all geometries into a single LineString
        unified_geom = route_gdf.geometry.unary_union

        # Create GeoJSON Feature
        geojson_feature = {
            "type": "Feature",
            "geometry": mapping(unified_geom),
            "properties": {}
        }

        # Save the completed route to Redis cache
        self.redis.set(cache_key, geojson_feature)

        return geojson_feature
