"""
Service for computing round-trip loop routes with multiple variants.

This module provides the LoopRouteService class which computes three distinct
loop route variants by rotating candidate destination tiles around the origin.
"""
import math
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from core.route_algorithm import RouteAlgorithm
from logger.logger import log
from services.route_service import RouteService
from utils.geo_transformer import GeoTransformer
from utils.route_summary import summarize_route
from utils.exposure_calculator import compute_exposure


class LoopRouteService:
    """
    Service for computing round-trip loop routes with multiple variants.

    Computes three distinct loop routes by selecting candidate destination tiles
    rotated 120° apart around the origin, ranking by air quality, and returning
    each completed route as a separate variant (loop1, loop2, loop3).
    """

    def __init__(self, area: str):
        """
        Initialize the LoopRouteService.

        Args:
            area (str): Area name (e.g., 'berlin', 'helsinki').
        """
        self.area = area
        self.route_service = RouteService(area)

    def get_round_trip(self, origin_gdf, distance=2500):
        """
        Computes a round-trip route starting and ending at `origin_gdf`.

        The method selects candidate points on the outermost tiles, calculates
        routes to each, ranks them by air quality, and yields each completed
        loop as loop1, loop2, loop3.

        Args:
            origin_gdf (GeoDataFrame): Starting point for the round trip.
            distance (float, optional): Approximate total distance of the trip.
                Defaults to 2500.

        Yields:
            dict: Full round-trip route and summary with keys:
                  {"routes": {"loopN": ...}, "summaries": {"loopN": ...}}
        """
        max_distance = distance / 2.2 - 100
        buffer = self.route_service.create_buffer(
            origin_gdf, origin_gdf, max_distance)
        origin_buffer = self.route_service.create_buffer(
            origin_gdf, origin_gdf, 1)
        origin_tile = self.route_service.get_tile_ids_by_buffer(origin_buffer)

        tile_ids = self.route_service.get_tile_ids_by_buffer(buffer)

        if not tile_ids:
            raise RuntimeError(
                "No tiles found in the requested area. Try a larger distance.")

        outer_tiles = self._get_outermost_tiles(tile_ids)

        if not outer_tiles:
            raise RuntimeError(
                "This location may be isolated (e.g., an island). "
                "Try a different location or larger distance.")

        edges = self.route_service.get_tile_edges(tile_ids)
        if edges is None or edges.empty:
            raise RuntimeError(
                "No road network found in the requested area. "
                "Try a different location.")

        best_edges_by_outer_tiles = self.extract_best_aq_point_from_tile(
            edges, outer_tiles)

        if best_edges_by_outer_tiles.empty:
            raise RuntimeError(
                "Unable to compute loop routes from this location. "
                "Try a different location.")

        first_tile_id = best_edges_by_outer_tiles.iloc[0]["tile_id"]

        tile_rotated_right = self.rotate_tile_about_center(
            first_tile_id, origin_tile[0], outer_tiles)
        if tile_rotated_right is None:
            log.warning("Could not find rotated tile candidate")
            tile_rotated_right_edges = gpd.GeoDataFrame()
        else:
            tile_rotated_right_edges = best_edges_by_outer_tiles[
                best_edges_by_outer_tiles["tile_id"] == tile_rotated_right]

        tile_rotated_left = self.rotate_tile_about_center(
            first_tile_id, origin_tile[0], outer_tiles, degrees=-120)
        if tile_rotated_left is None:
            log.warning("Could not find rotated left tile candidate")
            tile_rotated_left_edges = gpd.GeoDataFrame()
        else:
            tile_rotated_left_edges = best_edges_by_outer_tiles[
                best_edges_by_outer_tiles["tile_id"] == tile_rotated_left]

        best_3 = [best_edges_by_outer_tiles.iloc[[0]],
                  tile_rotated_right_edges, tile_rotated_left_edges]

        all_gdf = self.get_round_trip_forward(origin_gdf, best_3)

        # Yield routes as they complete
        yield from self.iterate_candidates(all_gdf, origin_gdf)

    def iterate_candidates(self, all_gdf, origin_gdf):
        """
        Generator: yields completed loop routes one by one.

        Fails gracefully if a candidate fails and continues to next one.

        Args:
            all_gdf (list): Candidate forward route data entries.
            origin_gdf (GeoDataFrame): Original starting point.

        Yields:
            dict: Full round-trip route and summaries with loop variant key.
        """
        if not all_gdf:
            raise RuntimeError(
                "Unable to compute loop routes from this location. "
                "Try a different area or distance."
            )

        loop_index = 1
        successful_loops = 0

        for candidate in all_gdf:
            loop_key = f"loop{loop_index}"

            try:
                full_route = self.get_round_trip_back(origin_gdf, candidate)

                result = {
                    "routes": {loop_key: full_route["routes"]["loop"]},
                    "summaries": {loop_key: full_route["summaries"]["loop"]},
                    "aqi_differences": None
                }

                yield result

                successful_loops += 1
                loop_index += 1

            except Exception as e:  # pylint: disable=broad-exception-caught
                # LOG BUT DO NOT STOP LOOP GENERATION
                log.warning(f"Loop candidate failed: {e}")
                continue

        # Only raise error if NO loops succeeded
        if successful_loops == 0:
            raise RuntimeError(
                "Unable to compute loop routes from this location. "
                "Try a different area or distance."
            )

    def get_round_trip_forward(self, origin_gdf, best_3):
        """
        Compute forward routes to candidate outer-tile points.
        Uses expanded buffer to find routes across bridges/obstacles.

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

            buffer = self.route_service.create_buffer(
                origin_gdf, gdf.iloc[[0]], buffer_m=1000)
            tile_ids = self.route_service.get_tile_ids_by_buffer(buffer)

            if not tile_ids:
                continue

            edges = self.route_service.get_tile_edges(tile_ids)
            if edges is None or edges.empty:
                continue

            nodes = self.route_service.get_nodes_from_db(tile_ids)
            if nodes is None or nodes.empty:
                continue

            snapped_gdf = self._snap_points_to_network(gdf, edges)
            if snapped_gdf.empty:
                continue

            success = False
            single_gdf = None
            epath = []
            gdf_route = None

            for idx in snapped_gdf.index:
                edges_x = edges.copy()
                nodes_x = nodes.copy()

                try:
                    current_route_algorithm = RouteAlgorithm(
                        edges_x, nodes_x)
                except (ValueError, RuntimeError) as e:
                    log.debug(f"Failed to initialize RouteAlgorithm: {e}")
                    continue

                single_gdf = snapped_gdf.loc[[idx]]

                try:
                    gdf_route, epath = (
                        current_route_algorithm.calculate_round_trip(
                            origin_gdf, single_gdf,
                            current_route_algorithm.igraph,
                            balance_factor=0.15
                        )
                    )

                    if (gdf_route is not None and not gdf_route.empty and
                            'geometry' in gdf_route.columns):
                        success = True
                        break
                except (ValueError, KeyError) as e:
                    log.debug(f"Route calculation failed: {e}")
                    continue

            if not success or single_gdf is None or gdf_route is None:
                continue

            data_entry = {
                "destination": single_gdf,
                "route": gdf_route,
                "summary": summarize_route(gdf_route),
                "epath_gdf_ids": [
                    current_route_algorithm.igraph.es[eid]["gdf_edge_id"]
                    for eid in epath
                    if 0 <= eid < (
                        current_route_algorithm.igraph.ecount())
                ]
            }
            all_gdf.append(data_entry)

        all_gdf.sort(key=lambda x: x["summary"]["aq_average"])
        return all_gdf

    def get_round_trip_back(self, destination, first_path_data):
        """
        Compute the return trip from destination back to the original origin.

        Args:
            destination (GeoDataFrame): Destination point for the return leg.
            first_path_data (dict): Data from the first leg, including:
                                    origin, route, and previous edge IDs.

        Returns:
            dict: Routes and summaries for the full round-trip under "loop" key.

        Raises:
            RuntimeError: If any step of the route computation fails.
        """
        if not first_path_data or "route" not in first_path_data or first_path_data["route"].empty:
            raise RuntimeError(
                "Route computation failed. Try a different location.")

        if destination is None or (hasattr(destination, 'empty') and destination.empty):
            raise RuntimeError(
                "Route computation failed. Try a different location.")

        origin = first_path_data.get("destination")
        if origin is None or (hasattr(origin, 'empty') and origin.empty):
            raise RuntimeError(
                "Route computation failed. Try a different location.")

        try:
            buffer = self.route_service.create_buffer(
                origin, destination, buffer_m=1000)
            tile_ids = self.route_service.get_tile_ids_by_buffer(buffer)

            if not tile_ids:
                raise RuntimeError(
                    "No tiles found between origin and destination.")

        except Exception as exc:
            raise RuntimeError(
                "Route computation failed. Try a different location.") from exc

        edges = self.route_service.get_tile_edges(tile_ids)
        if edges is None or edges.empty:
            raise RuntimeError(
                "No road network found in requested area.")

        nodes = self.route_service.get_nodes_from_db(tile_ids)
        if nodes is None or nodes.empty:
            raise RuntimeError(
                "No nodes found in requested area.")

        try:
            current_route_algorithm = RouteAlgorithm(edges, nodes)
        except Exception as exc:
            raise RuntimeError(
                "Route computation failed. Try a different location.") from exc

        prev_gdf_ids = first_path_data.get("epath_gdf_ids", None)

        try:
            gdf, _ = current_route_algorithm.calculate_round_trip(
                destination, origin, current_route_algorithm.igraph,
                balance_factor=0.15, reverse=True, previous_edges=prev_gdf_ids
            )

            if gdf is None or gdf.empty or 'geometry' not in gdf.columns:
                raise RuntimeError(
                    "Route computation failed. Try a different location.")

        except (ValueError, KeyError, Exception):
            raise RuntimeError(
                "Route computation failed. Try a different location.") from None

        combined_gdf = pd.concat(
            [first_path_data["route"], gdf], ignore_index=True)
        if combined_gdf.empty or 'geometry' not in combined_gdf.columns:
            raise RuntimeError(
                "Route computation failed. Try a different location.")

        try:
            combined_gdf = compute_exposure(combined_gdf)
            full_path = GeoTransformer.gdf_to_feature_collection(
                combined_gdf,
                property_keys=[
                    c for c in combined_gdf.columns if c != "geometry"]
            )
        except Exception as exc:
            raise RuntimeError(
                "Route computation failed. Try a different location.") from exc

        return {
            "routes": {"loop": full_path},
            "summaries": {"loop": summarize_route(combined_gdf)},
            "aqi_differences": None
        }

    def extract_best_aq_point_from_tile(self, edges, tile_ids) -> gpd.GeoDataFrame:
        """
        Extract the best air quality points for each tile.

        Gets the point with best (lowest) AQ value per tile by extracting
        the start coordinate of the edge with best air quality.

        Args:
            edges (gpd.GeoDataFrame): GeoDataFrame with columns: tile_id, aqi,
                                      edge_id, and geometry (LineString).
            tile_ids (list): List of tile identifiers to consider.

        Returns:
            gpd.GeoDataFrame: Points (one per tile) at best AQ edge starts.
        """
        edges = edges[edges['tile_id'].isin(tile_ids)]
        if edges.empty:
            return gpd.GeoDataFrame(columns=["geometry", "tile_id"], crs=edges.crs)
        best_edges = (
            edges.sort_values(["aqi", "edge_id"], ascending=[True, True])
            .groupby("tile_id", group_keys=True)
            .head(5)
        )
        geometries = [Point(g.coords[0]) for g in best_edges.geometry]
        tile_ids_list = best_edges["tile_id"].tolist()

        best_points_gdf = gpd.GeoDataFrame({
            "geometry": geometries,
            "tile_id": tile_ids_list
        }, crs=edges.crs)

        return best_points_gdf

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

    def decode_tile(self, tile):
        """
        Decode tile string to row and column integers.

        Args:
            tile (str): Tile string in format "rX_cY" (e.g., "r14_c12").

        Returns:
            tuple: (row, col) as integers.
        """
        row = int(tile.split("_")[0][1:])
        col = int(tile.split("_")[1][1:])
        return row, col

    def rotate_tile_about_center(self, tile, center_tile, candidate_tiles, degrees=120.0):
        """
        Rotate a tile around a center tile by given degrees.

        Given a center tile and target tile, returns the tile from candidate_tiles
        that is at the same distance but rotated by the specified degrees.

        Args:
            tile (str): Tile to rotate from (in "rX_cY" format).
            center_tile (str): Center point for rotation.
            candidate_tiles (list): List of tiles to match result to.
            degrees (float, optional): Degrees to rotate. Defaults to 120.0.

        Returns:
            str: Tile ID from candidate_tiles closest to rotated position.
        """
        row, col = self.decode_tile(tile)
        center_row, center_col = self.decode_tile(center_tile)

        vx = col - center_col
        vy = row - center_row

        rad = math.radians(degrees)
        rx = vx * math.cos(rad) - vy * math.sin(rad)
        ry = vx * math.sin(rad) + vy * math.cos(rad)

        new_row = int(round(center_row + ry))
        new_col = int(round(center_col + rx))

        closest_match = self.get_closest_tile_match(
            f"r{new_row}_c{new_col}", candidate_tiles)
        return closest_match

    def get_closest_tile_match(self, tile, tiles):
        """
        Find the closest tile match from a list of candidate tiles.

        Uses Manhattan distance to find the closest match to the target tile.

        Args:
            tile (str): Target tile in "rX_cY" format.
            tiles (list): List of candidate tiles to match against.

        Returns:
            str: Closest matching tile ID, or None if no match found.
        """
        if tile in tiles:
            return tile

        r, c = self.decode_tile(tile)
        # uses set for fast lookup
        decoded_tiles = {self.decode_tile(t) for t in tiles}

        # Check distance in increasing Manhattan distance
        for distance in range(1, 3):
            for dr in range(-distance, distance + 1):
                for dc in range(-distance, distance + 1):
                    if abs(dr) + abs(dc) != distance:
                        continue
                    candidate = (r + dr, c + dc)
                    if candidate in decoded_tiles:
                        return f"r{candidate[0]}_c{candidate[1]}"

        return None

    def _snap_points_to_network(self, points_gdf, edges_gdf) -> gpd.GeoDataFrame:
        """
        Snap points to nearest edges in the walking network.

        Args:
            points_gdf: GeoDataFrame with destination points (can be on water)
            edges_gdf: GeoDataFrame with walking network edges

        Returns:
            GeoDataFrame: Snapped points that are on the network
        """
        snapped_points = []

        for idx, point in points_gdf.iterrows():

            distances = edges_gdf.geometry.distance(point.geometry)
            nearest_idx = distances.idxmin()
            nearest_edge = edges_gdf.iloc[nearest_idx]

            snapped_point = nearest_edge.geometry.interpolate(
                nearest_edge.geometry.project(point.geometry)
            )

            snapped_points.append({
                'geometry': snapped_point,
                'tile_id': (
                    points_gdf.loc[idx, 'tile_id']
                    if 'tile_id' in points_gdf.columns
                    else None
                )
            })

        if snapped_points:
            return gpd.GeoDataFrame(snapped_points, crs=points_gdf.crs)
        return gpd.GeoDataFrame(columns=["geometry", "tile_id"])
