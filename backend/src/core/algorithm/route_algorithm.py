import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString
from shapely.strtree import STRtree
from shapely.ops import split
import numpy as np
import pandas as pd


class RouteAlgorithm:
    def __init__(self, edges_gdf: gpd.GeoDataFrame):
        self.edges = edges_gdf.copy()
        self.edges_tree = STRtree(self.edges.geometry.values)
        self.edges["start_node"] = self.edges.geometry.apply(
            lambda g: tuple(g.coords[0]))
        self.edges["end_node"] = self.edges.geometry.apply(
            lambda g: tuple(g.coords[-1]))
        print(f"Edgejä ladattu: {len(self.edges)}")

    def calculate_path(self, origin_gdf: gpd.GeoDataFrame, destination_gdf: gpd.GeoDataFrame,
                       weight="length_m", method="dijkstra") -> gpd.GeoDataFrame:

        origin_point = origin_gdf.geometry.iloc[0]
        destination_point = destination_gdf.geometry.iloc[0]

        origin_node, origin_splits = self.snap_and_split(origin_point)
        destination_node, destination_splits = self.snap_and_split(
            destination_point)

        self.extra_edges = origin_splits + destination_splits
        G = self.build_graph(weight=weight, extra_edges=self.extra_edges)

        if origin_node not in G or destination_node not in G:
            raise ValueError("Snap point not in graph.")

        path_nodes = self.calculate_route(
            G, origin_node, destination_node, method=method)

        all_edges = pd.concat(
            [self.edges, gpd.GeoDataFrame(self.extra_edges)], ignore_index=True)

        path_edges = []
        for u, v in zip(path_nodes[:-1], path_nodes[1:]):
            edge_row = all_edges[
                (all_edges.start_node == u) & (all_edges.end_node == v)
            ]
            if not edge_row.empty:
                path_edges.append(edge_row.iloc[0])
            else:
                print(f"Cannot find edge for nodes: {u} → {v}")

        print(f"Path edges count: {len(path_edges)}")
        route_gdf = gpd.GeoDataFrame(path_edges, crs=self.edges.crs).copy()
        return route_gdf

    def snap_and_split(self, point: Point) -> tuple[tuple, list]:
        try:
            nearest_idx = self.edges_tree.nearest(point)
            edge_row = self.edges.iloc[nearest_idx]
            print(f"Lähin edge indeksi: {nearest_idx}")
        except Exception as e:
            distances = self.edges.geometry.distance(point)
            if distances.empty:
                return None, []
            nearest_idx = distances.idxmin()
            edge_row = self.edges.iloc[nearest_idx]

        line: LineString = edge_row.geometry
        snapped_point = line.interpolate(line.project(point))
        snapped_coord = tuple(snapped_point.coords[0])
        snapped_coord = (round(snapped_point.x, 3), round(snapped_point.y, 3))

        snapped_point = line.interpolate(line.project(point))

        cut_line = LineString([
            (snapped_point.x - 0.01, snapped_point.y - 0.01),
            (snapped_point.x + 0.01, snapped_point.y + 0.01)
        ])

        split_result = split(line, cut_line)

        print(
            f"Split result: {split_result.geom_type}, parts: {len(split_result.geoms)}")

        lines = [geom for geom in split_result.geoms if isinstance(
            geom, LineString)]
        if len(lines) != 2:
            return snapped_coord, []

        edge_a = edge_row.copy()
        edge_a.geometry = lines[0]
        edge_a.start_node = tuple(lines[0].coords[0])
        edge_a.end_node = tuple(lines[0].coords[-1])

        edge_b = edge_row.copy()
        edge_b.geometry = lines[1]
        edge_b.start_node = tuple(lines[1].coords[0])
        edge_b.end_node = tuple(lines[1].coords[-1])

        print(
            f"Splitted edges: {edge_a.start_node}→{edge_a.end_node}, {edge_b.start_node}→{edge_b.end_node}")
        split_point = tuple(lines[0].coords[-1])
        return split_point, [edge_a, edge_b]

    def build_graph(self, weight="length_m", extra_edges: list = None) -> nx.DiGraph:
        print("Build a graph...")
        G = nx.DiGraph()
        all_edges = self.edges.copy()
        if extra_edges:
            all_edges = gpd.GeoDataFrame(
                pd.concat([all_edges, gpd.GeoDataFrame(extra_edges)]), crs=self.edges.crs)
            print(f"Added {len(extra_edges)} slitted edges to graph.")

        for _, row in all_edges.iterrows():
            start, end = row.start_node, row.end_node
            G.add_edge(start, end, edge_id=row.get(
                "edge_id", None), weight=row.get(weight, 1))
        return G

    def find_edge_by_nodes(self, u: tuple, v: tuple):
        match = self.edges[
            (self.edges.start_node == u) & (self.edges.end_node == v)
        ]
        return match.iloc[0] if not match.empty else None

    @staticmethod
    def euclidean_heuristic(u, v):
        x1, y1 = u
        x2, y2 = v
        return np.hypot(x2 - x1, y2 - y1)

    @staticmethod
    def calculate_route(G: nx.DiGraph, origin_node: tuple, destination_node: tuple, method="dijkstra") -> list:
        try:
            if method == "astar":
                return nx.astar_path(
                    G,
                    origin_node,
                    destination_node,
                    heuristic=RouteAlgorithm.euclidean_heuristic,
                    weight="weight"
                )
            else:
                return nx.dijkstra_path(G, origin_node, destination_node, weight="weight")
        except nx.NetworkXNoPath:
            print("No route found.")
            raise ValueError(
                "No route could be found between the given origin and destination points.")
