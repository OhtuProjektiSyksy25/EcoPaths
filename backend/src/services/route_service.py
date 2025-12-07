"""
Service that computes routes and returns them as GeoJSON LineStrings.
"""
import math
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Polygon, Point
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

    def get_round_trip(self, origin_gdf, distance=2500):
        """
            Computes a round-trip route starting and ending at `origin_gdf`.

            The method selects candidate points on the outermost tiles, calculates
            routes to each, ranks them by air quality, and returns the full route
            with the best air quality.

            Args:
                origin_gdf (GeoDataFrame): Starting point for the round trip.
                distance (float, optional): Approximate total distance of the trip. 
                Defaults to 2000.

            Returns:
                dict: Full round-trip route and summary under the key "balanced"
        """

        max_distance = distance / 2.2 - 100  # needs fine tuning
        buffer = self._create_buffer(origin_gdf, origin_gdf, max_distance)
        origin_buffer = self._create_buffer(origin_gdf, origin_gdf, 1)
        origin_tile = self.db_client.get_tile_ids_by_buffer(
            self.area, origin_buffer)

        tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)
        outer_tiles = self._get_outermost_tiles(tile_ids)

        # Get edges for relevant tiles (Redis + enrich new tiles if needed)
        edges = self._get_tile_edges(tile_ids)
        if edges is None or edges.empty:
            raise RuntimeError("No edges found for requested route area.")

        best_edges_by_outer_tiles = self.extract_best_aq_point_from_tile(
            edges, outer_tiles)
        first_tile_id = best_edges_by_outer_tiles.iloc[0]["tile_id"]

        tile_rotated_right = self.rotate_tile_about_center(
            first_tile_id, origin_tile[0], outer_tiles)
        tile_rotated_left = self.rotate_tile_about_center(
            first_tile_id, origin_tile[0], outer_tiles, degrees=-120)
        tile_rotated_right_edges = best_edges_by_outer_tiles[
            best_edges_by_outer_tiles["tile_id"] == tile_rotated_right]
        tile_rotated_left_edges = best_edges_by_outer_tiles[
            best_edges_by_outer_tiles["tile_id"] == tile_rotated_left]
        best_3 = [best_edges_by_outer_tiles.iloc[[0]],
                  tile_rotated_right_edges, tile_rotated_left_edges]

        all_gdf = self.get_round_trip_forward(
            origin_gdf, best_3)
        return self.iterate_candidates(all_gdf, origin_gdf)

    def iterate_candidates(self, all_gdf, origin_gdf):
        """
            Iterates over potential routes
            Returns first valid route.

        Args:
            all_gdf (list): Candidate forward route data entries.
            origin_gdf (GeoDataFrame): Original starting point.

        Returns:
            dict: Full round-trip route and summaries for the first valid candidate.

        """
        for candidate in all_gdf:
            try:
                full_route = self.get_round_trip_back(
                    origin_gdf, candidate)
                return full_route
            except RuntimeError as exc:
                print(f"round trip back failed for: {exc}")
                continue
            except ValueError as exc:
                print(f"round trip back failed for: {exc}")
                continue
        return full_route

    def get_round_trip_forward(self, origin_gdf, best_3):
        """
        Compute forward routes to candidate outer-tile points.

        Args:
            origin_gdf (GeoDataFrame): Starting point of the round trip.
            best_3 (list): List of gdfs per tile with top aq edges.

        Returns:
            list: Forward route candidates sorted by air-quality average.
        """
        all_gdf = []

        for gdf in best_3:
            if gdf.empty:
                continue
            buffer = self._create_buffer(origin_gdf, gdf.iloc[[0]])
            tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)

            # Get edges for relevant tiles (Redis + enrich new tiles if needed)
            edges = self._get_tile_edges(tile_ids)

            # Nodes_gdf from database
            nodes = self._get_nodes_from_db(tile_ids)
            for idx in gdf.index:
                edges_x = edges.copy()
                nodes_x = nodes.copy()
                current_route_algorithm = RouteAlgorithm(edges_x, nodes_x)
                for e in current_route_algorithm.igraph.es:
                    if 'length_m' not in e.attributes():
                        print("Missing length_m:", e.tuple)
                single_gdf = gdf.loc[[idx]]
                try:
                    gdf, epath = current_route_algorithm.calculate_round_trip(
                        origin_gdf, single_gdf, current_route_algorithm.igraph, balance_factor=0.15)
                    break
                except (ValueError, KeyError) as exc:
                    print(
                        f"first part of round trip failed for candidate: {exc}")
                    continue

            data_entry = {}
            data_entry["destination"] = single_gdf
            data_entry["route"] = gdf
            data_entry["summary"] = summarize_route(gdf)
            epath_gdf_ids = []
            for eid in epath:
                if 0 <= eid < current_route_algorithm.igraph.ecount():
                    epath_gdf_ids.append(
                        current_route_algorithm.igraph.es[eid]["gdf_edge_id"])
            data_entry["epath_gdf_ids"] = epath_gdf_ids
            all_gdf.append(data_entry)

        all_gdf.sort(key=lambda x: x["summary"]["aq_average"])
        return all_gdf

    def get_round_trip_back(self, destination, first_path_data):
        """
            Compute the return trip from "destination" back to the original origin.

            Args:
                destination (GeoDataFrame): Destination point for the return leg.
                first_path_data (dict): Data from the first leg, including:
                                        origin, route, and previous edge IDs.

            Returns:
                dict: Routes and summaries for the full round-trip under key ..
        """
        origin = first_path_data["destination"]

        buffer = self._create_buffer(origin, destination)
        tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)
        edges = self._get_tile_edges(tile_ids)
        nodes = self._get_nodes_from_db(tile_ids)
        current_route_algorithm = RouteAlgorithm(edges, nodes)
        prev_gdf_ids = first_path_data.get("epath_gdf_ids", None)
        gdf, _ = current_route_algorithm.calculate_round_trip(
            destination, origin, current_route_algorithm.igraph,
            balance_factor=0.15, reverse=True, previous_edges=prev_gdf_ids)

        combined_gdf = pd.concat(
            [first_path_data["route"], gdf], ignore_index=True)
        combined_gdf = compute_exposure(combined_gdf)
        full_path = GeoTransformer.gdf_to_feature_collection(
            combined_gdf, property_keys=[
                c for c in combined_gdf.columns if c != "geometry"]
        )
        results, summaries = {}, {}
        results["loop"] = full_path
        summaries["loop"] = summarize_route(combined_gdf)

        # FIX BALANCED
        return {"routes": results, "summaries": summaries, "aqi_differences": None}

    def extract_best_aq_point_from_tile(self, edges, tile_ids) -> gpd.GeoDataFrame:
        """Extracts the best (5) air quality points for each tile in tile_ids.
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
            .groupby("tile_id", group_keys=True)
            .head(5)
        )
        all_gdfs = []
        best_edges = best_edges.copy()
        best_edges["geometry"] = best_edges["geometry"].apply(
            lambda g: Point(g.coords[0]))
        best_edges = gpd.GeoDataFrame(best_edges, crs=edges.crs)

        for _, row in best_edges.iterrows():
            geometry = row['geometry']
            first_point = Point(geometry.coords[0])
            gdf = gpd.GeoDataFrame({
                "geometry": [first_point],
                "tile_id": [row["tile_id"]]
            }, crs=edges.crs)

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
                    log.warning(
                        "Failed to save enriched tiles to Redis.")
            else:
                log.warning(
                    "Enrichment failed or returned empty. Skipping save.")

        if all_gdfs:
            return pd.concat(all_gdfs, ignore_index=True)

        return None

    def _get_outermost_tiles(self, tile_ids):
        """
        Identify tiles on the outer boundary of a tile grid.

        Args:
            tile_ids (list): Tile identifiers in "rX_cY" format.

        Returns:
            list: Tile IDs located at the outer edge of the set.
        """
        coordinates = {(int(t.split('_')[0][1:]), int(
            t.split('_')[1][1:])) for t in tile_ids}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        outer_tiles = []
        for row, column in coordinates:
            if any((row+row_direction, column+column_direction) not in coordinates
                    for row_direction, column_direction in directions):
                outer_tiles.append((row, column))

        outer_tiles = [f"r{row}_c{column}" for row, column in outer_tiles]
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
        Works statelessly by rebuilding the graph from scratch.

        Args:
            origin_gdf (GeoDataFrame): Origin point.
            destination_gdf (GeoDataFrame): Destination point.
            balanced_value (float): Weight for balanced route (0.0 = fastest, 1.0 = best AQ).

        Returns:
            dict: Contains routes, summaries, and aqi_differences keys.
        """
        buffer = self._create_buffer(origin_gdf, destination_gdf)
        tile_ids = self.db_client.get_tile_ids_by_buffer(self.area, buffer)

        edges = self._get_tile_edges(tile_ids)

        nodes = self._get_nodes_from_db(tile_ids)

        if edges is None or edges.empty:
            raise RuntimeError("No edges found for requested route area.")

        edges_subset = edges[edges.geometry.intersects(buffer)].copy()

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

        return {
            "routes": {"balanced": result},
            "summaries": {"balanced": summary},
            "aqi_differences": None
        }

    @staticmethod
    def decode_tile(tile):
        """Decodes tile str to integers
           Example: r14_c12 -> 14, 12

        Args:
            tile (str): string with tile row and column

        Returns:
            row (int): row
            col (int): column
        """
        row = int(tile.split("_")[0][1:])
        col = int(tile.split("_")[0][1:])
        return row, col

    def rotate_tile_about_center(self, tile, center_tile, candidate_tiles, degrees=120.0):
        """Given a center tile and target tile, returns tile that is
           at the same distance but according to degrees paramater
           that many degrees rotated

        Args:
            tile (str): str with tile information
            center_tile (str): str with tile information
            candidate_tiles(list): list of tiles that rotated tile will be matched to
            degrees (float, optional): degrees to be rotated to. Defaults to 120.0.

        Returns:
            tile (str): tile id of rotated tile
        """
        row, col = RouteService.decode_tile(tile)
        center_row, center_col = RouteService.decode_tile(center_tile)

        vx = col - center_col
        vy = row - center_row

        rad = math.radians(degrees)
        rx = vx * math.cos(rad) - vy * math.sin(rad)
        ry = vx * math.sin(rad) + vy * math.cos(rad)

        new_row = int(round(center_row + ry))
        new_col = int(round(center_col + rx))

        closest_match = RouteService.get_closest_tile_match(
            f"r{new_row}_c{new_col}", candidate_tiles)
        return closest_match

    @staticmethod
    def get_closest_tile_match(tile, tiles):
        """Gets closes tile match of given tile to list of tiles

        Args:
            tile (str): tile to be matched
            tiles (list): list of tiles to be matched to

        Returns:
            tile (str): closest match tile
        """
        if tile in tiles:
            return tile
        r, c = RouteService.decode_tile(tile)
        decoded_tiles = []
        for single_tile in tiles:
            row, col = RouteService.decode_tile(single_tile)
            decoded_tiles.append((row, col))
        for dr in [0, 1, -1]:
            for dc in [0, 1, -1]:
                if dr == 0 and dc == 0:
                    continue
                if (r+dr, c+dc) in decoded_tiles:
                    return f"r{r+dr}_c{c+dc}"
        return tiles[0]
