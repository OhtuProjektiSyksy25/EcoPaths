"""Routing algorithm for spatial networks using GeoDataFrames and igraph."""

import geopandas as gpd
import igraph as ig
import pandas as pd
from shapely.strtree import STRtree
from shapely.ops import split
from shapely.geometry import Point, LineString
from src.logging.logger import log


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

    def update_weights(self, graph, balance_factor):
        """
        Update edge weights in the igraph according to balance_factor.
        Args:
            balance_factor (float): Value between 0 and 1 determening the tradeoff
                between shortest distance (1) and best air quality (0)
        """
        min_normalized_aqi = 0.001 if balance_factor == 0 else 0

        for edge in graph.es:
            edge["weight"] = (
                balance_factor * edge["length_m"] +
                (1 - balance_factor) * (edge["length_m"]
                                        * (edge["normalized_aqi"] + min_normalized_aqi))
            )

    def calculate_path(self, origin_gdf, destination_gdf, graph=None, balance_factor=1):
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
        if graph is None:
            graph = self.igraph

        origin_node, destination_node, graph = self.prepare_graph_and_nodes(
            origin_gdf, destination_gdf, graph, balance_factor=balance_factor,
        )

        if origin_node not in graph.vs["name"] or destination_node not in graph.vs["name"]:
            raise ValueError("node not found.")

        path_nodes = self.run_routing_algorithm(
            graph, origin_node, destination_node)
        path_edges = self.extract_path_edges(path_nodes, graph)

        log.debug(
            f"Extracted {len(path_edges)} edges for final route", edge_count=len(path_edges))

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

    def prepare_graph_and_nodes(self, origin_gdf, destination_gdf, graph,
                                balance_factor=1, no_update=False):
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

        try:
            graph.vs.find(name="origin")
        except ValueError:
            self.snap_and_split(origin_gdf.geometry.iat[0], "origin", graph)

        try:
            graph.vs.find(name="destination")
        except ValueError:
            self.snap_and_split(
                destination_gdf.geometry.iat[0], "destination", graph)

        if not no_update:
            self.update_weights(graph, balance_factor=balance_factor)

        isolates = [
            v.index for v in graph.vs if graph.degree(v.index) == 0]
        graph.delete_vertices(isolates)

        return "origin", "destination", graph

    def extract_path_edges(self, path_nodes, graph):
        """
        Extracts edge geometries along a given path.

        Args:
            path_nodes (list): Ordered list of node ids (["name"]).

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing the edges of the path
        """
        name_to_idx = {vertice["name"]: vertice.index for vertice in graph.vs}

        edges_gdf_rows = []

        for from_node_name, to_node_name in zip(path_nodes[:-1], path_nodes[1:]):
            from_node_idx = name_to_idx[from_node_name]
            to_node_idx = name_to_idx[to_node_name]
            try:
                edge_id = graph.get_eid(from_node_idx, to_node_idx)
                gdf_edge_id = graph.es[edge_id]["gdf_edge_id"]
                row = self.route_specific_gdf[self.route_specific_gdf["edge_id"] == gdf_edge_id]
                if not row.empty:
                    edges_gdf_rows.append(row.iloc[0])
            except ig.InternalError:
                log.error(
                    f"Missing edge for {from_node_name} ↔ {to_node_name}",
                    from_node=from_node_name, to_node=to_node_name)

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

    def snap_and_split(self, point: Point, destination: str, graph):
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
            v for v in graph.vs
            if v["geometry"].equals(snapped_point)
        ]
        if existing_vertices:
            v = existing_vertices[0]
            v["name"] = destination
            return

        graph.add_vertices(destination)
        vertice = graph.vs.find(name=destination)
        vertice["geometry"] = snapped_point
        vertice["x"] = snapped_coord[0]
        vertice["y"] = snapped_coord[1]

        self.init_split_edges(edge_row, destination,
                              parts, snapped_coord, line, graph)

    def init_split_edges(self, edge_row, destination, parts, snapped_coord, line, graph):
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
            eid = graph.get_eid(from_node, to_node)
            graph.delete_edges([eid])
        except ig.InternalError:
            pass

        new_edges = [
            (from_node, destination),
            (destination, to_node)
        ]
        graph.add_edges(new_edges)

        new_edge_ids = [
            graph.get_eid(from_node, destination),
            graph.get_eid(destination, to_node)
        ]

        graph.es[new_edge_ids[0]]["length_m"] = parts[0].length
        graph.es[new_edge_ids[0]]["aqi"] = aqi
        graph.es[new_edge_ids[0]]["normalized_aqi"] = normalized_aqi
        graph.es[new_edge_ids[0]]["gdf_edge_id"] = max_id+1
        graph.es[new_edge_ids[0]]["weight"] = 0  # placeholder

        graph.es[new_edge_ids[1]]["length_m"] = parts[1].length
        graph.es[new_edge_ids[1]]["aqi"] = aqi
        graph.es[new_edge_ids[1]]["normalized_aqi"] = normalized_aqi
        graph.es[new_edge_ids[1]]["gdf_edge_id"] = max_id+2
        graph.es[new_edge_ids[1]]["weight"] = 0  # placeholder

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

    def calculate_round_trip(self, origin_gdf, destination_gdf, inital_graph,
                             balance_factor=0, reverse=False, previous_edges=None):
        """
            Compute a forward or return route of a round-trip route.

            Depending on 'reverse', prepares routing nodes and runs the shortest-path
            algorithm on the provided graph, optionally penalizing edges used in the
            first route.

            Args:
                origin_gdf (GeoDataFrame): Start point of this route.
                destination_gdf (GeoDataFrame): End point of this route.
                inital_graph (igraph.Graph): Graph containing edges and weights.
                balance_factor (float, optional): Weight between speed and air quality.
                reverse (bool, optional): If True, swap origin and destination.
                previous_edges (list[int] | None): gdf_edge_id values from the
                    outbound route to heavily penalize for the return route.

            Returns:
                tuple:
                    - path_edges (GeoDataFrame): Edges forming the computed route.
                    - epath (list[int]): List of igraph edge indices representing the path.

            Raises:
                ValueError: If origin or destination node cannot be found in the graph.
        """
        if reverse:
            destination_node, origin_node, graph = self.prepare_graph_and_nodes(
                origin_gdf, destination_gdf, inital_graph, balance_factor=balance_factor
            )
        else:
            origin_node, destination_node, graph = self.prepare_graph_and_nodes(
                origin_gdf, destination_gdf, inital_graph, balance_factor=balance_factor
            )

        if previous_edges is not None:
            # previous_edges is a list of gdf_edge_id values (stable identifiers)
            prev_gdf_ids = previous_edges
            # For each gdf id, find the matching edge(s) in inital_graph and set weight high
            for gdf_id in prev_gdf_ids:
                for e in inital_graph.es:
                    if e.attributes().get("gdf_edge_id") == gdf_id:
                        # very large so algorithm avoids it
                        e["weight"] = 999999

        if origin_node not in graph.vs["name"] or destination_node not in graph.vs["name"]:
            raise ValueError("node not found.")

        path_nodes, epath = self.run_routing_algorithm(
            graph, origin_node, destination_node, epath=True)
        path_edges = self.extract_path_edges(path_nodes, graph)
        print(f"Extracted {len(path_edges)} edges for final route")
        return path_edges, epath

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
    def run_routing_algorithm(graph, origin_node, destination_node, epath=False):
        """6  POINT (390423.121 5820062.024)
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
            if epath is True:
                epath = graph.get_shortest_paths(
                    origin_idx, to=destination_idx, weights="weight", output="epath")[0]
                return name_path, epath
            return name_path

        except ig.InternalError as exc:
            raise ValueError(
                "No route found between origin and destination.") from exc
