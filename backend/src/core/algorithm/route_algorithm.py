"""
    A module for calculating routes using a simple routing algorithm.
    Uses NetworkX for graph representation and shortest path calculation.
"""

from itertools import groupby
import networkx as nx
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString

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
        transformer = Transformer.from_crs("EPSG:4326", self.edges_crs, always_xy=True)
        origin_proj = transformer.transform(*origin)
        destination_proj = transformer.transform(*destination)

        origin_node = min(
            self.graph.nodes,
            key=lambda n: (n[0] - origin_proj[0])**2 + (n[1] - origin_proj[1])**2
        )
        dest_node = min(
            self.graph.nodes,
            key=lambda n: (n[0] - destination_proj[0])**2 + (n[1] - destination_proj[1])**2
        )

        path = nx.shortest_path(self.graph, origin_node, dest_node, weight="weight")

        line_parts = []
        for u, v in zip(path[:-1], path[1:]):
            data = self.graph.get_edge_data(u, v)
            line_parts.append(data["geometry"])

        all_points = [pt for geom in line_parts for pt in geom.coords]
        unique_points = [x for x, _ in groupby(all_points)]

        return gpd.GeoDataFrame(
            [{"geometry": LineString(unique_points)}],
            geometry="geometry",
            crs=self.edges_crs
        )
