"""
    A module for calculating routes using a simple routing algorithm.
    Uses NetworkX for graph representation and shortest path calculation.
"""

from shapely.ops import linemerge, unary_union
from shapely.geometry import LineString
import networkx as nx
import geopandas as gpd
from pyproj import Transformer


class RouteAlgorithm:
    """
    Simple routing algorithm using NetworkX for shortest path calculation.

    Attributes:
        graph (nx.Graph): NetworkX graph representation of the edges.
        edges_crs (str): CRS of the input edges for coordinate transformation.
    """

    def __init__(self, edges):
        """
        Initialize the routing algorithm with edge data.

        Args:
            edges (GeoDataFrame): GeoDataFrame containing edge geometries and lengths.
        """
        self.graph = nx.Graph()
        self.edges_crs = edges.crs
        edges = edges.explode(index_parts=False).reset_index(drop=True)
        edges["length_m"] = edges.geometry.length

        for _, row in edges.iterrows():
            geom = row["geometry"]

            if geom.geom_type == "LineString":
                coords = list(geom.coords)
            else:
                continue

            u = coords[0]
            v = coords[-1]

            self.graph.add_edge(
                u,
                v,
                weight=row["length_m"],
                geometry=geom
            )

    def calculate(self, origin, destination):
        """
        Calculate the shortest path between origin and destination.

        Args:
            origin (tuple): Starting point as (lon, lat)
            destination (tuple): Ending point as (lon, lat)

        Returns:
            GeoDataFrame: GeoDataFrame with the route as a LineString geometry.
        """
        origin_proj = self._project_point(origin)
        destination_proj = self._project_point(destination)

        largest_cc_nodes = set(
            max(nx.connected_components(self.graph), key=len))
        origin_node = self._nearest_node(largest_cc_nodes, origin_proj)
        dest_node = self._nearest_node(largest_cc_nodes, destination_proj)

        path = nx.shortest_path(self.graph, origin_node,
                                dest_node, weight="weight")

        line_parts = [self.graph.get_edge_data(u, v)["geometry"]
                      for u, v in zip(path[:-1], path[1:])]

        merged_geom = unary_union(line_parts)
        if not isinstance(merged_geom, LineString):
            merged_geom = linemerge(merged_geom)
        if merged_geom.geom_type == "MultiLineString":
            merged_geom = LineString(
                [pt for line in merged_geom for pt in line.coords])

        return gpd.GeoDataFrame([{"geometry": merged_geom}],
                                geometry="geometry",
                                crs=self.edges_crs)

    def _project_point(self, lonlat):
        """Project a WGS84 (lon, lat) point into the edges CRS."""
        transformer = Transformer.from_crs(
            "EPSG:4326", self.edges_crs, always_xy=True)
        return transformer.transform(*lonlat)

    def _nearest_node(self, nodes, point):
        """Find nearest node from a set given a projected point."""
        return min(nodes, key=lambda n: (n[0] - point[0])**2 + (n[1] - point[1])**2)
