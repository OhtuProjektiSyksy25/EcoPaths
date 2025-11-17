"""Routing algorithm for spatial networks using GeoDataFrames and igraph."""

import geopandas as gpd
import igraph as ig
from shapely.strtree import STRtree
from shapely.ops import split
from shapely.geometry import Point, LineString
import pandas as pd


class RouteAlgorithm:
    """Class for computing shortest paths through a spatial network using igraph."""

    def __init__(self, edges_gdf: gpd.GeoDataFrame, nodes_gdf: gpd.GeoDataFrame):
        """
        Initializes the routing algorithm with a set of edges and nodes.
        Calls graph initialization

        Args:
            edges_gdf (gpd.GeoDataFrame): GeoDataFrame containing 
                LineString geometries representing edges.
            nodes_gdf (gpd.GeoDataFrame): GeodataFrame containing
                Point geometries representing nodes.
        """

        self.edges = edges_gdf.copy()
        self.nodes = nodes_gdf.copy()
        self.route_specific_gdf = None  # placeholder
        self.route_edges_tree = None  # placeholder
        self.nodes_tree = STRtree(self.nodes.geometry.to_list())
        self.init_graph()
        self.route_specific_gdf = self.edges_gdf_filtered.copy()
        self.route_edges_tree = STRtree(
            self.route_specific_gdf.geometry.to_list())

    def init_graph(self):
        """
        Initialize an igraph Graph from node and edge GeoDataFrames
        - Adds vertices to graph using node IDs
        - Adds node attributes
        - Filters and adds valid edges
        - Adds edge attributes

        """
        self.igraph = ig.Graph()
        edges_gdf = self.edges.copy()
        nodes_gdf = self.nodes.copy()
        vertices = nodes_gdf["node_id"].astype(str).tolist()
        valid_vertices = set(vertices)
        self.igraph.add_vertices(vertices)

        self.igraph.vs["geometry"] = nodes_gdf.geometry.tolist()
        self.igraph.vs["x"] = nodes_gdf.geometry.x.tolist()
        self.igraph.vs["y"] = nodes_gdf.geometry.y.tolist()
        self.igraph.vs["tile_id"] = nodes_gdf["tile_id"].tolist()
        edges_gdf_filtered = edges_gdf[
            edges_gdf["from_node"].astype(str).isin(valid_vertices) &
            edges_gdf["to_node"].astype(str).isin(valid_vertices)
        ]
        self.edges_gdf_filtered = edges_gdf_filtered.copy()
        edge_tuples = list(
            zip(edges_gdf_filtered["from_node"].astype(str),
                edges_gdf_filtered["to_node"].astype(str))
        )
        self.igraph.add_edges(edge_tuples)
        self.igraph.es["gdf_edge_id"] = edges_gdf_filtered["edge_id"].tolist()
        self.igraph.es["length_m"] = edges_gdf_filtered["length_m"].tolist()
        self.igraph.es["aqi"] = edges_gdf_filtered["aqi"].tolist()
        self.igraph.es["normalized_aqi"] = edges_gdf_filtered["normalized_aqi"].tolist()
        self.igraph.es["weight"] = [0] * len(edges_gdf_filtered)  # placeholder

    def update_weights(self, balance_factor):
        """
        Update edge weights in the igraph according to balance_factor.
        Args:
            balance_factor (float): Value between 0 and 1 determening the tradeoff
                between shortest distance (1) and best air quality (0)
        """
        min_normalized_aqi = 0.001 if balance_factor == 0 else 0

        for edge in self.igraph.es:
            edge["weight"] = (
                balance_factor * edge["length_m"] +
                (1 - balance_factor) * (edge["length_m"]
                                        * (edge["normalized_aqi"] + min_normalized_aqi))
            )

    def calculate_path(self, origin_gdf, destination_gdf, balance_factor=1):
        """
        Calculates the shortest path between origin and destination points.

        Args:
            origin_gdf (gpd.GeoDataFrame): GeoDataFrame with a Point geometry for origin.
            destination_gdf (gpd.GeoDataFrame): GeoDataFrame witha Point geometry for destination.
            balance_factor (float): Float value between 0 and 1 that dictates how much the algorithm
                                    consideres air quality when finding route. Lower values value
                                    air quality more over distance. Defaults to 1.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing the edges along the calculated route.
        """

        origin_node, destination_node, graph = self.prepare_graph_and_nodes(
            origin_gdf, destination_gdf, balance_factor=balance_factor
        )

        if origin_node not in graph.vs["name"] or destination_node not in graph.vs["name"]:
            raise ValueError("node not found.")

        path_nodes = self.run_routing_algorithm(
            graph, origin_node, destination_node)
        path_edges = self.extract_path_edges(path_nodes)
        print(f"Extracted {len(path_edges)} edges for final route")
        return path_edges

    def re_calculate_balanced_path(self, balance_factor):
        """Re calculates only the balanced path for the current graph

        Args:
            balance_factor (float): Float value between 0 and 1 that dictates how much the algorithm
                                    consideres air quality when finding route. Lower values value
                                    air quality more over distance. Defaults to 1.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing the edges along the balanced route.
        """

        self.update_weights(balance_factor=balance_factor)
        path_nodes = self.run_routing_algorithm(
            self.igraph, "origin", "destination")
        path_edges = self.extract_path_edges(path_nodes)
        return path_edges

    def init_route_specific(self):
        """
        Inits route specific data:
            self.route_specific_gdf
            self.route_edges_tree
        """
        self.route_specific_gdf = self.edges_gdf_filtered.copy()
        self.route_edges_tree = STRtree(
            self.route_specific_gdf.geometry.to_list())

    def prepare_graph_and_nodes(self, origin_gdf, destination_gdf, balance_factor=1, specific_graph=None):
        """
        Prepares graph and determines nearest origin and destination node for routing.
        Updates edge weights according to balance_factor
        Args:
            origin_gdf (gpd.GeoDataFrame): Origin point.
            destination_gdf (gpd.GeoDataFrame): Destination point.
            balance_factor (float): Float value between 0 and 1 that dictates how much the algorithm
                                    consideres air quality when finding route. Lower values value
                                    air quality more over distance. Defaults to 1.

        Returns:
            tuple: origin_node, destination_node, graph, combined_edges
        """
        if "origin" not in self.igraph.vs["name"]:
            self.snap_and_split(origin_gdf.geometry.iat[0], "origin")
        if "destination" not in self.igraph.vs["name"]:
            self.snap_and_split(destination_gdf.geometry.iat[0], "destination")
        self.update_weights(balance_factor=balance_factor)

        isolates = [
            v.index for v in self.igraph.vs if self.igraph.degree(v.index) == 0]
        self.igraph.delete_vertices(isolates)

        return "origin", "destination", self.igraph

    def extract_path_edges(self, path_nodes):
        """
        Extracts edge geometries along a given path.

        Args:
            path_nodes (list): Ordered list of node ids (["name"]).

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing the edges of the path
        """
        name_to_idx = {vertice["name"]: vertice.index for vertice in self.igraph.vs}

        edges_gdf_rows = []

        for from_node_name, to_node_name in zip(path_nodes[:-1], path_nodes[1:]):
            from_node_idx = name_to_idx[from_node_name]
            to_node_idx = name_to_idx[to_node_name]
            try:
                edge_id = self.igraph.get_eid(from_node_idx, to_node_idx)
                gdf_edge_id = self.igraph.es[edge_id]["gdf_edge_id"]
                row = self.route_specific_gdf[self.route_specific_gdf["edge_id"] == gdf_edge_id]
                if not row.empty:
                    edges_gdf_rows.append(row.iloc[0])
            except ig.InternalError:
                print(f"Missing edge for {from_node_name} ↔ {to_node_name}")

        edges_gdf = gpd.GeoDataFrame(
            edges_gdf_rows, crs=self.route_specific_gdf.crs)

        return edges_gdf

    def _find_nearest_edge(self, point: Point):
        """
        Finds the nearest edge to a given point.

        Args:
            point (Point): Point to search from.

        Returns:
            pd.Series: Row from edges GeoDataFrame representing the nearest edge.
        """
        try:
            nearest_geom = self.route_edges_tree.nearest(point)
            match = self.route_specific_gdf[self.route_specific_gdf.geometry == nearest_geom]
            if not match.empty:
                return match.iloc[0]
        except Exception as exc:
            raise RuntimeError(
                "STRtree.nearest failed during edge lookup.") from exc
        distances = self.route_specific_gdf.geometry.distance(point)
        if distances.empty:
            return None
        nearest_idx = distances.idxmin()
        return self.route_specific_gdf.loc[nearest_idx]

    def snap_and_split(self, point: Point, destination: str):
        """
        Snaps a point to the nearest edge and splits that edge at the snapped location.
        Adds snapped locations as a vertice to self.igraph
        Adds split edges to self.igraph

        Args:
            point (Point): Point to snap.
            destination (str): "origin" or "destination
                used to name new vertice either origin or destination
        """

        edge_row = self._find_nearest_edge(point)

        line: LineString = edge_row.geometry
        snapped_point = line.interpolate(line.project(point))
        snapped_coord = self._normalize_node(
            (snapped_point.x, snapped_point.y))

        split_result = self._compute_split_result(line, snapped_point)

        parts = [geom for geom in split_result.geoms if isinstance(
            geom, LineString)]
        if len(parts) == 1:
            parts.append(parts[0])

        existing_vertices = [
            v for v in self.igraph.vs
            if v["geometry"].equals(snapped_point)
        ]
        if existing_vertices:
            v = existing_vertices[0]
            v["name"] = destination
            return

        self.igraph.add_vertices(destination)
        vertice = self.igraph.vs.find(name=destination)
        vertice["geometry"] = snapped_point
        vertice["x"] = snapped_coord[0]
        vertice["y"] = snapped_coord[1]

        self.init_split_edges(edge_row, destination,
                              parts, snapped_coord, line)

    def init_split_edges(self, edge_row, destination, parts, snapped_coord, line):
        """
        Splits an existing edge at a given location.
        Deletes the original edge between "from_node" and "to_node" if it exists.
        Adds two new edges: from "from_node" to "destination" and from 
        "destination" to "to_node".
        Sets edge attributes such as length, aqi, normalized AQI, gdf_edge_id,
        and a placeholder weight.

        Args:
            edge_row (GeoSeries): The original edge's row from the GeoDataFrame.
            destination (str): The name of the new vertex where the edge is split.
                "origin" or "destination
            parts (list[LineString]): Two LineString geometries resulting from 
                splitting the original edge at the destination.

        Raises:
            ValueError: If the original edge between `from_node` and `to_node` 
                cannot be found in the graph.
        """
        from_node = str(edge_row["from_node"])
        to_node = str(edge_row["to_node"])
        aqi = edge_row.get("aqi", 250)
        normalized_aqi = edge_row.get("normalized_aqi", 0.5)
        max_id = self.route_specific_gdf["edge_id"].max()

        try:
            eid = self.igraph.get_eid(from_node, to_node)
            self.igraph.delete_edges([eid])
        except ig.InternalError:
            pass

        new_edges = [
            (from_node, destination),
            (destination, to_node)
        ]
        self.igraph.add_edges(new_edges)

        new_edge_ids = [
            self.igraph.get_eid(from_node, destination),
            self.igraph.get_eid(destination, to_node)
        ]

        self.igraph.es[new_edge_ids[0]]["length_m"] = parts[0].length
        self.igraph.es[new_edge_ids[0]]["aqi"] = aqi
        self.igraph.es[new_edge_ids[0]]["normalized_aqi"] = normalized_aqi
        self.igraph.es[new_edge_ids[0]]["gdf_edge_id"] = max_id+1
        self.igraph.es[new_edge_ids[0]]["weight"] = 0  # placeholder

        self.igraph.es[new_edge_ids[1]]["length_m"] = parts[1].length
        self.igraph.es[new_edge_ids[1]]["aqi"] = aqi
        self.igraph.es[new_edge_ids[1]]["normalized_aqi"] = normalized_aqi
        self.igraph.es[new_edge_ids[1]]["gdf_edge_id"] = max_id+2
        self.igraph.es[new_edge_ids[1]]["weight"] = 0  # placeholder

        new_edges_gdf = gpd.GeoDataFrame([
            {
                **edge_row.to_dict(),
                "edge_id": max_id+1,
                "from_node": from_node,
                "to_node": destination,
                "length_m": parts[0].length,
                "geometry": LineString([line.coords[0], snapped_coord])
            },
            {
                **edge_row.to_dict(),
                "edge_id": max_id+2,
                "from_node": destination,
                "to_node": to_node,
                "length_m": parts[1].length,
                "geometry": LineString([snapped_coord, line.coords[-1]])
            }
        ], crs=self.route_specific_gdf.crs)

        self.route_specific_gdf = pd.concat(
            [self.route_specific_gdf, new_edges_gdf], ignore_index=True
        )


    def calculate_round_trip(self, origin_gdf, destination_gdf, balance_factor=0, distance=0):
        self.initial_graph = self.igraph.copy()
        origin_node, destination_node, graph = self.prepare_graph_and_nodes(
            origin_gdf, destination_gdf, balance_factor=balance_factor
        )

        if origin_node not in graph.vs["name"] or destination_node not in graph.vs["name"]:
            raise ValueError("node not found.")

        path_nodes = self.run_routing_algorithm(
            graph, origin_node, destination_node)
        path_edges = self.extract_path_edges(path_nodes)
        print(f"Extracted {len(path_edges)} edges for final route")
        self.igraph = self.initial_graph.copy()
        return path_edges

    @staticmethod
    def _compute_split_result(line, snapped_point, offset=0.01):
        """
        Splits a LineString at a given point using a short perpendicular cut.

        Args:
            line (LineString): Line to split.
            snapped_point (Point): Point on the line where the split occurs.
            offset (float, optional): Length of the cut line. Defaults to 0.01.

        Returns:
            GeometryCollection: Resulting geometries from the split.
        """
        dx = line.coords[-1][0] - line.coords[0][0]
        dy = line.coords[-1][1] - line.coords[0][1]
        cut_line = LineString([
            (snapped_point.x + dy * offset, snapped_point.y - dx * offset),
            (snapped_point.x - dy * offset, snapped_point.y + dx * offset)
        ])
        split_result = split(line, cut_line)
        return split_result

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
    def run_routing_algorithm(graph, origin_node, destination_node):
        """
        Run the routing algorithm on the igraph graph

        Args:
            graph (igraph.Graph): Graph on which the algorithm is ran on
            origin_node (str): name attribute of origin node
            destination_node (str): name attribute of the destination node

        Returns:
            name_path (list): Ordered list of node name attributes 

        Raises:
            ValueError: If no route is found between origin and destination.
        """
        try:
            origin_idx = graph.vs.find(name=origin_node).index
            destination_idx = graph.vs.find(name=destination_node).index

            vpath = graph.get_shortest_paths(
                origin_idx, to=destination_idx, weights="weight", output="vpath")[0]
            name_path = [graph.vs[i]["name"] for i in vpath]
            return name_path

        except ig.InternalError as exc:
            raise ValueError(
                "No route found between origin and destination.") from exc
