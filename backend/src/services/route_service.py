# services/route_service.py

import geopandas as gpd
import pandas as pd
from shapely.wkt import loads as load_wkt
from shapely.geometry import mapping
from core.compute_model import ComputeModel
from core.algorithm import RouteAlgorithm
from services.redis_cache import RedisCache

CACHE_KEY_TEMPLATE = "edges_{area}"


class RouteService:
    """
        Returns a GeoJSON LineString representing the route.
        CRS: EPSG:4326 (lon/lat), ready for Mapbox or Leaflet.

        Args:
            origin (tuple): (lon, lat)
            destination (tuple): (lon, lat)

        Returns:
            dict: GeoJSON Feature with LineString geometry
        """

    def __init__(self, area: str = "berlin"):
        self.area = area.lower()
        self.compute_model = ComputeModel(area=self.area)
        self.redis = RedisCache()
        self.cache_key = CACHE_KEY_TEMPLATE.format(area=self.area)

    def get_route(self, origin: tuple, destination: tuple) -> dict:
        edges = self._load_edges_from_cache()
        if edges is None:
            edges = self.compute_model.get_data_for_algorithm()
            self._save_edges_to_cache(edges)

        algorithm = RouteAlgorithm(edges)
        route_gdf = algorithm.compute(origin, destination)

        # Change to EPSG:4326 lon/lat
        if route_gdf.crs is None or route_gdf.crs.to_string() != "EPSG:4326":
            route_gdf = route_gdf.to_crs("EPSG:4326")

        # Union alla geometrylines to one LineString (if many)
        unified_geom = route_gdf.geometry.unary_union

        geojson_feature = {
            "type": "Feature",
            "geometry": mapping(unified_geom),
            "properties": {}
        }
        return geojson_feature

    def _load_edges_from_cache(self):
        data = self.redis.get(self.cache_key)
        if data is None:
            return None
 
        # oletetaan että data on tallennettu listana dict-muodossa, jossa geometry WKT
        df = pd.DataFrame(data)
        df["geometry"] = df["geometry"].apply(load_wkt)
        gdf = gpd.GeoDataFrame(df, geometry="geometry",
                               crs="EPSG:25833")  # tai alueen CRS
        return gdf

    def _save_edges_to_cache(self, edges):
        # Muutetaan GeoDataFrame JSON-ystävälliseen muotoon
        data = edges.copy()
        data["geometry"] = data["geometry"].apply(lambda geom: geom.wkt)
        self.redis.set(self.cache_key, data.to_dict(orient="records"))
