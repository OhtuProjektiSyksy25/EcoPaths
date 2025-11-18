"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Polygon, shape, mapping, Point
from config.settings import AreaConfig, get_settings
from core.route_algorithm import RouteAlgorithm
from core.edge_enricher import EdgeEnricher
from database.db_client import DatabaseClient
from services.redis_cache import RedisCache
from services.redis_service import RedisService
from utils.route_summary import summarize_route
from utils.geo_transformer import GeoTransformer
import matplotlib.pyplot as plt
import copy
import hashlib
import json



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


    def get_round_trip(self, origin_gdf, distance = 2000):
        """
            Computes a round-trip route starting and ending at `origin_gdf`.

            The method selects candidate points on the outermost tiles, calculates
            routes to each, ranks them by air quality, and returns the full route
            with the best air quality.

            Args:
                origin_gdf (GeoDataFrame): Starting point for the round trip.
                distance (float, optional): Approximate total distance of the trip. Defaults to 2000.

            Returns:
                dict: Full round-trip route and summary under the key "balanced"
        """

        max_distance = distance / 3
        buffer = self._create_buffer(origin_gdf, origin_gdf, max_distance)
        tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)
        outer_tiles = self._get_outermost_tiles(tile_ids)

        # Get edges for relevant tiles (Redis + enrich new tiles if needed)
        edges = self._get_tile_edges(tile_ids)
        # Nodes_gdf from database
        nodes = self._get_nodes_from_db(tile_ids)
        if edges is None or edges.empty:
            raise RuntimeError("No edges found for requested route area.")
        #edges = edges[edges.geometry.intersects(buffer)].copy()  #Should work now, didnt have time to test

        best_edges_by_outer_tiles = self.extract_best_aq_point_from_tile(edges, outer_tiles)

        all_gdf = []

        for idx in best_edges_by_outer_tiles.index:
            edges_x = edges.copy()
            nodes_x = nodes.copy()

            current_route_algorithm = RouteAlgorithm(edges_x, nodes_x)
            for e in current_route_algorithm.igraph.es:
                if 'length_m' not in e.attributes():
                    print("Missing length_m:", e.tuple)
            single_gdf = best_edges_by_outer_tiles.loc[[idx]]
            try:
                gdf, epath = current_route_algorithm.calculate_round_trip(
                    origin_gdf, single_gdf, current_route_algorithm.igraph, balance_factor=0.15)
            except Exception as exc:
                print(f"first part of round trip failed for candidate: {exc}")
                continue

            data_entry = {}
            data_entry["destination"] = single_gdf
            data_entry["route"] = gdf
            data_entry["summary"] = summarize_route(gdf)
            epath_gdf_ids = []

            for eid in epath:
                if 0 <= eid < current_route_algorithm.igraph.ecount():
                    epath_gdf_ids.append(current_route_algorithm.igraph.es[eid]["gdf_edge_id"])
            data_entry["epath_gdf_ids"] = epath_gdf_ids
            all_gdf.append(data_entry)

        all_gdf.sort(key=lambda x: x["summary"]["aq_average"])

        for candidate in all_gdf:
            try:
                full_route = self.get_round_trip_back(origin_gdf, edges, nodes, candidate)
                print(full_route["summaries"]["balanced"])
                return full_route
            except Exception as exc:
                print(f"round trip back failed for: {exc}")
                continue
        return full_route


    def get_round_trip_back(self, destination, edges, nodes, first_path_data):
        """
            Compute the return trip from "destination" back to the original origin.

            Args:
                destination (GeoDataFrame): Destination point for the return leg.
                edges (GeoDataFrame): Edges for the routing graph.
                nodes (GeoDataFrame): Nodes for the routing graph.
                first_path_data (dict): Data from the first leg, including:
                                        origin, route, and previous edge IDs.

            Returns:
                dict: Routes and summaries for the full round-trip under key ..
        """
        current_route_algorithm = RouteAlgorithm(edges, nodes)
        origin = first_path_data["destination"]
        prev_gdf_ids = first_path_data.get("epath_gdf_ids", None)
        gdf, _ = current_route_algorithm.calculate_round_trip(
            destination, origin, current_route_algorithm.igraph,
            balance_factor=0.15, reverse=True, previous_edges=prev_gdf_ids)

        combined_gdf = pd.concat([first_path_data["route"], gdf], ignore_index=True)
        full_path = GeoTransformer.gdf_to_feature_collection(
            combined_gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
        )
        results, summaries = {}, {}
        results["balanced"] = full_path
        summaries["balanced"] = summarize_route(combined_gdf)
        return {"routes": results, "summaries": summaries} #FIX BALANCED



        
    def extract_best_aq_point_from_tile(self,edges, tile_ids) -> gpd.GeoDataFrame:
        """Extracts the best air quality point for each tile in tile_ids.
           edge_id is also used for sorting to make extracting determenistic
           gets point by getting the start of linestring coordinates of edge.
           

        Args:
            edges (gpd.GeoDataFrame): GeoDataFrame containing edge geometries 
                                      with columns, tile_id, aqi, edge_id
                                      and geometry (LineString).
            tile_ids (list): List of tile identifiers to consider.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing a single Point per tile,
            representing the start point of the edge with the best air quality.
        """
        edges = edges[edges['tile_id'].isin(tile_ids)]
        best_edges = (
            edges.sort_values(["aqi", "edge_id"], ascending=[True, True])
            .groupby("tile_id", as_index=False)
            .first()
        )
        all_gdfs = []
        for _, row in best_edges.iterrows():
            geometry = row['geometry']
            first_point = Point(geometry.coords[0]) 
            gdf = gpd.GeoDataFrame(geometry=[shape(first_point)], crs=edges.crs)
            all_gdfs.append(gdf)
        return pd.concat(all_gdfs, ignore_index=True)


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

        if origin_point == destinaion_point:
            return origin_point.buffer(buffer_m)
        
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
                origin_gdf, destination_gdf, graph=None, balance_factor=balance_factor)
            gdf["mode"] = mode
            summaries[mode] = summarize_route(gdf)
            results[mode] = GeoTransformer.gdf_to_feature_collection(
                gdf, property_keys=[c for c in gdf.columns if c != "geometry"]
            )

        return {"routes": results, "summaries": summaries}
