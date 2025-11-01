"""Routing algorithm for spatial networks using GeoDataFrames and NetworkX."""

from math import hypot
import geopandas as gpd
import pandas as pd
import networkx as nx
from shapely.geometry import Point, LineString
from shapely.ops import split
from shapely.strtree import STRtree


class RouteAlgorithm:
    """Class for computing shortest paths through a spatial network."""

    def __init__(self, edges_gdf: gpd.GeoDataFrame):
        """
        Initializes the routing algorithm with a set of edges.

        Args:
            edges_gdf (gpd.GeoDataFrame): GeoDataFrame containing 
            LineString geometries representing edges.
        """
        self.edges = edges_gdf.copy()
        self.edges["start_node"] = self.edges.geometry.apply(
            lambda g: self._normalize_node(g.coords[0])
        )
        self.edges["end_node"] = self.edges.geometry.apply(
            lambda g: self._normalize_node(g.coords[-1])
        )
        self.edges_tree = STRtree(self.edges.geometry.to_list())
        print(f"Subset_edges count: {len(self.edges)}")

    def calculate_path(self, origin_gdf, destination_gdf, balance_factor=0, method="dijkstra"):
        """
        Calculates the shortest path between origin and destination points.

        Args:
            origin_gdf (gpd.GeoDataFrame): GeoDataFrame with a Point geometry for origin.
            destination_gdf (gpd.GeoDataFrame): GeoDataFrame witha Point geometry for destination.
            weight (str): Column name used as edge weight.
            method (str): Routing algorithm to use ("dijkstra" or "astar").

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing the edges along the calculated route.
        """
        origin_node, destination_node, graph, extra_edges = self.prepare_graph_and_nodes(
            origin_gdf, destination_gdf, balance_factor
        )

        if origin_node not in graph or destination_node not in graph:
            raise ValueError("Snapped point not found in graph nodes.")

        path_nodes = self.run_routing_algorithm(
            graph, origin_node, destination_node, method)
        path_edges = self._extract_path_edges(extra_edges, path_nodes)

        print(f"Extracted {len(path_edges)} edges for final route")
        return path_edges

    def prepare_graph_and_nodes(self, origin_gdf, destination_gdf, balance_factor):
        """
        Prepares graph and snapped nodes for routing.

        Args:
            origin_gdf (gpd.GeoDataFrame): Origin point.
            destination_gdf (gpd.GeoDataFrame): Destination point.
            weight (str): Edge weight column.

        Returns:
            tuple: origin_node, destination_node, graph, combined_edges
        """
        origin_point = origin_gdf.geometry.iat[0]
        destination_point = destination_gdf.geometry.iat[0]

        origin_node, origin_splits = self.snap_and_split(origin_point)
        destination_node, destination_splits = self.snap_and_split(
            destination_point)

        extra_edges = self._combine_edges([origin_splits, destination_splits])
        graph = self.build_graph(balance_factor, edges_gdf=extra_edges)

        return origin_node, destination_node, graph, extra_edges

    def snap_and_split(self, point: Point):
        """
        Snaps a point to the nearest edge and splits that edge at the snapped location.

        Args:
            point (Point): Point to snap.

        Returns:
            tuple: snapped coordinate (tuple), GeoDataFrame of split edges
        """
        edge_row = self._find_nearest_edge(point)
        if edge_row is None:
            return None, gpd.GeoDataFrame(columns=self.edges.columns, crs=self.edges.crs)

        line: LineString = edge_row.geometry
        snapped_point = line.interpolate(line.project(point))
        snapped_coord = self._normalize_node(
            (snapped_point.x, snapped_point.y))

        offset = 0.01
        dx = line.coords[-1][0] - line.coords[0][0]
        dy = line.coords[-1][1] - line.coords[0][1]
        cut_line = LineString([
            (snapped_point.x + dy * offset, snapped_point.y - dx * offset),
            (snapped_point.x - dy * offset, snapped_point.y + dx * offset)
        ])

        split_result = split(line, cut_line)
        parts = [geom for geom in split_result.geoms if isinstance(
            geom, LineString)]

        if len(parts) != 2:
            return snapped_coord, gpd.GeoDataFrame(columns=self.edges.columns, crs=self.edges.crs)

        split_edges = gpd.GeoDataFrame([
            {**edge_row.to_dict(), "geometry": parts[0]},
            {**edge_row.to_dict(), "geometry": parts[1]}
        ], crs=self.edges.crs)

        split_edges["start_node"] = split_edges.geometry.apply(
            lambda g: self._normalize_node(g.coords[0])
        )
        split_edges["end_node"] = split_edges.geometry.apply(
            lambda g: self._normalize_node(g.coords[-1])
        )

        print(f"Split edge at {snapped_coord}")

        return snapped_coord, split_edges

    def _find_nearest_edge(self, point: Point):
        """
        Finds the nearest edge to a given point.

        Args:
            point (Point): Point to search from.

        Returns:
            pd.Series: Row from edges GeoDataFrame representing the nearest edge.
        """
        try:
            nearest_geom = self.edges_tree.nearest(point)
            match = self.edges[self.edges.geometry == nearest_geom]
            if not match.empty:
                return match.iloc[0]
        except Exception as exc:
            raise RuntimeError(
                "STRtree.nearest failed during edge lookup.") from exc
        distances = self.edges.geometry.distance(point)
        if distances.empty:
            return None
        nearest_idx = distances.idxmin()
        return self.edges.loc[nearest_idx]

    def build_graph(self, balance_factor=0.5, edges_gdf=None) -> nx.Graph:
        """
        Builds a NetworkX graph from edge data.

        Args:
            weight (str): Column name used as edge weight.
            edges_gdf (gpd.GeoDataFrame, optional): Edge data to use. Defaults to self.edges.

        Returns:
            nx.Graph: Constructed graph.
        """
        graph = nx.Graph()
        edges = edges_gdf if edges_gdf is not None else self.edges


        for _, row in edges.iterrows():
            start = self._normalize_node(row.start_node)
            end = self._normalize_node(row.end_node)

            aqi = row.get("aqi", None)
            length = row.get("length_m", row.geometry.length)
            # balance_factor is used to balance the influence of aqi on the weight
            # lower balance_factor values equate to weighing air quality more
            # normalized_aq gets values between 0 and 1
            if aqi is not None:
                normalized_aq = min(aqi / 500, 1)
                aq_multipler_balanced_weight = balance_factor * length + (1 - balance_factor) * (length * normalized_aq)
                w = aq_multipler_balanced_weight if aqi is not None else length
            else:
                print("Error: Edge without AQI value")
                w = length
            graph.add_edge(start, end, weight=w)

        return graph

    def _extract_path_edges(self, edges_gdf, path_nodes):
        """
        Extracts edge geometries along a given path.

        Args:
            edges_gdf (gpd.GeoDataFrame): Edge data.
            path_nodes (list): Ordered list of node coordinates.

        Returns:
            gpd.GeoDataFrame: Subset of edges forming the path.
        """
        edge_rows = []
        for u, v in zip(path_nodes[:-1], path_nodes[1:]):
            match = edges_gdf[
                ((edges_gdf["start_node"] == u) & (edges_gdf["end_node"] == v)) |
                ((edges_gdf["start_node"] == v) & (edges_gdf["end_node"] == u))
            ]
            if not match.empty:
                edge_rows.append(match.iloc[0])
            else:
                print(f"Missing edge for {u} ↔ {v}")
        return gpd.GeoDataFrame(edge_rows, crs=self.edges.crs)

    def _combine_edges(self, gdfs):
        """
        Combines original edges with additional split edges.

        Args:
            gdfs (list): List of GeoDataFrames.

        Returns:
            gpd.GeoDataFrame: Combined edge set.
        """
        valid_gdfs = [g for g in gdfs if not g.empty]
        if not valid_gdfs:
            return self.edges.copy()
        combined = gpd.GeoDataFrame(
            pd.concat([self.edges, *valid_gdfs], ignore_index=True), crs=self.edges.crs)
        return combined

    @staticmethod
    def _normalize_node(point, decimals=3):
        """
        Rounds coordinates to a fixed number of decimals for node identification.

        Args:
            point (tuple): Coordinate pair.
            decimals (int): Number of decimals to round to.

        Returns:
            tuple: Rounded coordinate pair.
        """
        return (round(point[0], decimals), round(point[1], decimals))

    @staticmethod
    def euclidean_heuristic(u, v):
        """
        Computes Euclidean distance between two nodes.

        Args:
            u (tuple): First node.
            v (tuple): Second node.

        Returns:
            float: Distance between nodes.
        """
        x1, y1 = u
        x2, y2 = v
        return hypot(x2 - x1, y2 - y1)

    @staticmethod
    def run_routing_algorithm(G, origin_node, destination_node, method="dijkstra"):
        """
        Computes the shortest path between two nodes in a graph
        using the specified routing algorithm.

        Args:
            G (nx.Graph): NetworkX graph representing the spatial network.
            origin_node (tuple): Coordinates of the origin node.
            destination_node (tuple): Coordinates of the destination node.
            method (str): Routing method to use ("dijkstra" or "astar").

        Returns:
            list: Ordered list of node coordinates forming the shortest path.

        Raises:
            ValueError: If no path is found between origin and destination.
        """
        try:
            if method == "astar":
                return nx.astar_path(
                    G, origin_node, destination_node,
                    heuristic=RouteAlgorithm.euclidean_heuristic, weight="weight"
                )
            return nx.dijkstra_path(G, origin_node, destination_node, weight="weight")
        except nx.NetworkXNoPath as exc:
            raise ValueError(
                "No route found between origin and destination.") from exc
