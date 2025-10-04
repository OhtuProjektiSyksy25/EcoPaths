import networkx as nx
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString

class RouteAlgorithm:
    """Laskee lyhimmän reitin edge-pituuksien perusteella."""

    def __init__(self, edges):
        # edges oletetaan GeoDataFrameksi, jossa on sarakkeet: u, v, geometry, length
        self.graph = nx.Graph()
        self.edges_crs = edges.crs
        
        
        print("Building graph from edges...")
        
        for _, row in edges.iterrows():
            geom = row["geometry"]

            if geom.geom_type == "LineString":
                coords = list(geom.coords)
            elif geom.geom_type == "MultiLineString":
                # pick the longest part for start/end
                longest = max(geom.geoms, key=lambda g: g.length)
                coords = list(longest.coords)
            else:
                continue  # skip weird geometries

            u = coords[0]   # start point
            v = coords[-1]  # end point

            self.graph.add_edge(
                u,
                v,
                weight=row["length_m"],
                geometry=geom
            )



    def compute(self, origin, destination):
        # Transform origin/destination to match the edges CRS
        transformer = Transformer.from_crs("EPSG:4326", self.edges_crs, always_xy=True)
        origin_proj = transformer.transform(*origin)         # returns (x, y) in edges CRS
        destination_proj = transformer.transform(*destination)

        # Hae lähin solmu alku- ja loppukoordinaateille
        origin_node = min(
            self.graph.nodes,
            key=lambda n: (n[0] - origin_proj[0])**2 + (n[1] - origin_proj[1])**2
        )
        dest_node = min(
            self.graph.nodes,
            key=lambda n: (n[0] - destination_proj[0])**2 + (n[1] - destination_proj[1])**2
        )



        print(f"Origin node: {origin_node}, Destination node: {dest_node}")
        print("computing shortest path with these nodes...")
        # Laske lyhin polku pituuden perusteella
        path = nx.shortest_path(self.graph, origin_node, dest_node, weight="weight")

        # Muodosta LineString reitin edge-geometrioista
        line_parts = []
        for u, v in zip(path[:-1], path[1:]):
            data = self.graph.get_edge_data(u, v)
            line_parts.append(data["geometry"])

        return gpd.GeoDataFrame(
            [{"geometry": LineString([pt for geom in line_parts for pt in geom.coords])}],
            geometry="geometry",
            crs="EPSG:4326"
        )