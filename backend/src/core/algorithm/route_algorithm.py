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
        Moved to preprocessor

        Initialize the routing algorithm with edge data.

        Args:
            edges (GeoDataFrame): GeoDataFrame containing edge geometries and lengths.
        """
        self.graph_fastest = nx.Graph()
        self.graph_fast_and_aq = nx.Graph()
        self.edges_crs = edges.crs
        # if any(edges.geometry.type == "MultiLineString"):
        #     edges = edges.explode(index_parts=False).reset_index(drop=True)
        #     edges["length_m"] = edges.geometry.length
        print('edges:', edges)

        for _, row in edges.iterrows():
            geom = row["geometry"]

            if geom.geom_type == "LineString":
                coords = list(geom.coords)
            else:
                continue
            # ottaa kadunpätkän ensimmäisen ja viimeisen pisteen
            # ja lisää ne solmuiksi verkkoon
            u = coords[0]
            v = coords[-1]

            self.graph_fastest.add_edge(
                u,
                v,
                weight=row["length_m"],
                geometry=geom
            )
            self.graph_fast_and_aq.add_edge(
                u,
                v,
                weight=row["length_m"] * row["aq_value"],
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
        # Koordinaatit ei ole kaikkiin pisteisiin, vaan esim kodin koordinaatit pitää snäpätä johonkin pisteeseen

        origin_proj = self._project_point(origin)
        destination_proj = self._project_point(destination)

        largest_cc_nodes_fastest = set(
            max(nx.connected_components(self.graph_fastest), key=len))
        largest_cc_nodes_fastest_and_aq = set(
            max(nx.connected_components(self.graph_fast_and_aq), key=len))
        origin_node = self._nearest_node(largest_cc_nodes_fastest, origin_proj)
        dest_node = self._nearest_node(largest_cc_nodes_fastest, destination_proj)

        origin_node = self._nearest_node(largest_cc_nodes_fastest_and_aq, origin_proj)
        dest_node = self._nearest_node(largest_cc_nodes_fastest_and_aq, destination_proj)

        path_fastest = nx.shortest_path(self.graph_fastest, origin_node,
                                dest_node, weight="weight")
        path_fastest_and_aq = nx.shortest_path(self.graph_fast_and_aq, origin_node,
                                dest_node, weight="weight")

        line_parts_fastest = [self.graph_fastest.get_edge_data(u, v)["geometry"]
                      for u, v in zip(path_fastest[:-1], path_fastest[1:])]
        line_parts_fastest_and_aq = [self.graph_fast_and_aq.get_edge_data(u, v)["geometry"]
                      for u, v in zip(path_fastest_and_aq[:-1], path_fastest_and_aq[1:])]
        #mitä tekee ja miksi?
        merged_geom_fastest = unary_union(line_parts_fastest)
        merged_geom_fastest_and_aq = unary_union(line_parts_fastest_and_aq)

        #merged geom on palautettu sellaiseen muotoon, että se voidaan palauttaa geodataframina
        if not isinstance(merged_geom_fastest, LineString):
            merged_geom_fastest = linemerge(merged_geom_fastest)
        if not isinstance(merged_geom_fastest_and_aq, LineString):
            merged_geom_fastest_and_aq = linemerge(merged_geom_fastest_and_aq)
        if merged_geom_fastest.geom_type == "MultiLineString":
            # MultiLineString may not be directly iterable in some Shapely versions;
            # iterate its .geoms sequence to access component LineStrings.
            merged_geom_fastest = LineString(
                [pt for line in merged_geom_fastest.geoms for pt in line.coords]
            )
        if merged_geom_fastest_and_aq.geom_type == "MultiLineString":
            merged_geom_fastest_and_aq = LineString(
                [pt for line in merged_geom_fastest_and_aq.geoms for pt in line.coords]
            )
        gdf_fastest = gpd.GeoDataFrame([{"geometry": merged_geom_fastest}],
                               geometry="geometry",
                               crs=self.edges_crs)
        gdf_fast_and_aq = gpd.GeoDataFrame([{"geometry": merged_geom_fastest_and_aq}],
                                   geometry="geometry",
                                   crs=self.edges_crs)

        return gdf_fastest, gdf_fast_and_aq


    def _project_point(self, lonlat):
        """Project a WGS84 (lon, lat) point into the edges CRS."""
        transformer = Transformer.from_crs(
            "EPSG:4326", self.edges_crs, always_xy=True)
        return transformer.transform(*lonlat)

    def _nearest_node(self, nodes, point):
        """Find nearest node from a set given a projected point."""
        return min(nodes, key=lambda n: (n[0] - point[0])**2 + (n[1] - point[1])**2)
