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
from services.redis_service import RedisService
from utils.route_summary import summarize_route
from utils.geo_transformer import GeoTransformer
import matplotlib.pyplot as plt


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
                  balanced_value: float = 0.5) -> dict:
        """
        Main entrypoint: compute route and return routes + summaries.

            Args:
                origin_gdf (GeoDataFrame): GeoDataFrame with origin point.
                destination_gdf (GeoDataFrame): GeoDataFrame with destination point.
                balanced_weight (float): Weight for balanced route (0.0 = fastest, 1.0 = best AQ).

        Returns:
            dict: GeoJSON FeatureCollection and route summaries.
        """

        buffer = self._create_buffer(origin_gdf, destination_gdf)
        tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)

        # Get edges for relevant tiles (Redis + enrich new tiles if needed)
        edges = self._get_tile_edges(tile_ids)

        # Nodes_gdf from database
        nodes = self._get_nodes_from_db(tile_ids)
        if edges is None or edges.empty:
            raise RuntimeError("No edges found for requested route area.")

        edges_subset = edges[edges.geometry.intersects(buffer)].copy()

        return self._compute_routes(
            edges_subset, nodes, origin_gdf, destination_gdf, balanced_value
        )

    def compute_balanced_route_only(self, balanced_value):
        """
        Computes only the "balanced route" for the given balanced_value
        Uses a pre-initialized graph

        Args:
            balanced_value (float): Weight for balanced route (0.0 = fastest, 1.0 = best AQ).

        Returns:
            result (GeoJSON FeatureCollection): Route edges
            summary (dict): Route data summary
        """
        gdf = self.current_route_algorithm.re_calculate_balanced_path(
            balanced_value)
        summary = summarize_route(gdf)
        result = GeoTransformer.gdf_to_feature_collection(
            gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
        )

        results, summaries = {}, {}
        results["balanced"] = result
        summaries["balanced"] = summary
        return {"routes": results, "summaries": summaries}

    def get_round_trip(self, origin_gdf, distance = 1000):
        center_tile_buffer = self._create_buffer(origin_gdf, origin_gdf, 1)
        center_tile = self.db_client.get_tile_ids_by_buffer(self.area, center_tile_buffer)

        if len(center_tile) > 1:
            center_tile = center_tile[0]

        max_distance = (distance / 2) + 300
        buffer = self._create_buffer(origin_gdf, origin_gdf, max_distance)
        tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)
        print(tile_ids)
        outer_tiles = self._get_outermost_tiles(tile_ids)

        # Get edges for relevant tiles (Redis + enrich new tiles if needed)
        edges = self._get_tile_edges(tile_ids)
        # Nodes_gdf from database
        nodes = self._get_nodes_from_db(tile_ids)
        if edges is None or edges.empty:
            raise RuntimeError("No edges found for requested route area.")
        edges_subset = edges[edges.geometry.intersects(buffer)].copy()

        best_edges_by_outer_tiles = self.extract_best_aq_edge_from_tile(edges_subset,outer_tiles)
        self.current_route_algorithm = RouteAlgorithm(edges_subset, nodes)
        all_gdf = []


        for idx in best_edges_by_outer_tiles.index:
            single_gdf = best_edges_by_outer_tiles.loc[[idx]]  # note the double brackets, keeps it as GeoDataFrame
            gdf = self.current_route_algorithm.calculate_round_trip(
                origin_gdf, single_gdf, balance_factor=0)
            all_gdf.append(gdf)
            print("HEP")



        x = GeoTransformer.gdf_to_feature_collection(
                gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
            )
        return {"routes": x, "summaries": None}


    def extract_best_aq_edge_from_tile(self,edges_subset, tile_ids) -> gpd.GeoDataFrame:
        edges_subset = edges_subset[edges_subset['tile_id'].isin(tile_ids)]

        best_edges = (
            edges_subset.sort_values("aqi")
            .groupby("tile_id", as_index=False)
            .first()
        )
        points_gdf = gpd.GeoDataFrame(
            geometry=best_edges['geometry'].apply(lambda line: line.interpolate(0.5, normalized=True)),
            crs=edges_subset.crs
        )

        return points_gdf


# tEMP debuggin PRINTING TEMP DELETE DELTE
    def parse_tiles(self, tiles):
        
        return [(int(t.split('_')[0][1:]), int(t.split('_')[1][1:])) for t in tiles]

    def temp_plot(self, tile_ids,origin_gdf):
        center_tile_buffer = self._create_buffer(origin_gdf, origin_gdf, 1)
        center_tile = self.db_client.get_tile_ids_by_buffer(self.area, center_tile_buffer)

        x = self._get_outermost_tiles(tile_ids)

        all_coords = self.parse_tiles(tile_ids)
        outer_coords = self.parse_tiles(x)
        center_coords = self.parse_tiles(center_tile)  # parse_tiles expects a list

        # Plot
        plt.figure(figsize=(8,8))
        all_rows, all_cols = zip(*all_coords)
        outer_rows, outer_cols = zip(*outer_coords)
        center_row, center_col = zip(*center_coords)


        plt.scatter(all_cols, all_rows, color='lightblue', label='All tiles', s=200)
        plt.scatter(outer_cols, outer_rows, color='red', label='Outer tiles', s=200)
        plt.scatter(center_col, center_row, color='green', label='Center tile', s=200)

        plt.gca().invert_yaxis()  # Optional: match typical grid orientation
        plt.grid(True)
        plt.legend()
        plt.show()
# END OF TEMP DELET EDEBUGGING PRINT OK

    def _create_buffer(self, origin_gdf, destination_gdf, buffer_m=600) -> Polygon:
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
        destinaion_point = destination_gdf.geometry.iloc[0]

        #if origin_point == destinaion_point:

        #    return origin_point.buffer(buffer_m)
        
        line = LineString([
            origin_point,
            destinaion_point
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
        non_existing_tile_ids = RedisService.prune_found_ids(
            tile_ids, self.redis, self.area_config)
        existing_tile_ids = list(set(tile_ids) - set(non_existing_tile_ids))

        all_gdfs = []
        if len(existing_tile_ids) > 0:
            found_gdf, expired_tiles = RedisService.get_gdf_by_list_of_keys(
                existing_tile_ids, self.redis, self.area_config)
            non_existing_tile_ids = list(
                set(non_existing_tile_ids + expired_tiles))
            if found_gdf is not False:
                all_gdfs.append(found_gdf)

        if len(non_existing_tile_ids) > 0:
            enricher = EdgeEnricher(area=self.area)
            new_gdf = enricher.get_enriched_tiles(
                non_existing_tile_ids, network_type=self.network_type)

            if new_gdf is not False and new_gdf is not None and not new_gdf.empty:
                saved = RedisService.save_gdf(
                    new_gdf, self.redis, self.area_config)
                if saved:
                    all_gdfs.append(new_gdf)
                else:
                    print("Warning: Failed to save enriched tiles to Redis.")
            else:
                print("Warning: Enrichment failed or returned empty. Skipping save.")

        if all_gdfs:
            return pd.concat(all_gdfs, ignore_index=True)

        return None

    def _get_outermost_tiles(self, tile_ids):
        coordinates = {(int(t.split('_')[0][1:]), int(t.split('_')[1][1:])) for t in tile_ids}

        directions = [(-1,0),(1,0),(0,-1),(0,1)]

        # Outer tiles: has at least one missing neighbor
        outer_tiles = []
        for row,column in coordinates:
            if any((row+row_direction, column+column_direction) not in coordinates for row_direction, column_direction in directions):
                outer_tiles.append((row,column))
        # Back to tile strings
        outer_tiles = [f"r{row}_c{column}" for row,column in outer_tiles]
        return outer_tiles

    def _get_nodes_from_db(self, tile_ids: list) -> gpd.GeoDataFrame:
        """
        Fetch nodes for the given tile_ids from the database.

        Args:
            tile_ids (list): List of tile_ids intersecting route buffer.

        Returns:
            GeoDataFrame: Nodes for requested tiles.
        """
        return self.db_client.get_nodes_by_tile_ids(
            self.area_config.area,
            self.network_type,
            tile_ids
        )

    def _compute_routes(self, edges, nodes, origin_gdf, destination_gdf, balanced_value=0.5):
        """Compute multiple route variants and summaries."""

        modes = {
            "fastest": 1,
            "best_aq": 0,
            "balanced": balanced_value
        }

        self.current_route_algorithm = RouteAlgorithm(edges, nodes)
        results, summaries = {}, {}

        for mode, balance_factor in modes.items():
            gdf = self.current_route_algorithm.calculate_path(
                origin_gdf, destination_gdf, balance_factor=balance_factor)
            gdf["mode"] = mode
            summaries[mode] = summarize_route(gdf)
            results[mode] = GeoTransformer.gdf_to_feature_collection(
                gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
            )

        return {"routes": results, "summaries": summaries}

    def _compute_roundtrip(self, edges, nodes, origin_gdf, distance):
        results, summaries = {}, {}
        self.current_route_algorithm = RouteAlgorithm(edges, nodes)

        gdf = self.current_route_algorithm.calculate_round_trip(
                origin_gdf, distance)

        # "balanced" needs to be changed TEMPORARY FIX

        results["balanced"] = GeoTransformer.gdf_to_feature_collection(
                gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
            )
        summaries["balanced"] = summarize_route(gdf)
        
        return {"routes":gdf, "summaries": summaries}