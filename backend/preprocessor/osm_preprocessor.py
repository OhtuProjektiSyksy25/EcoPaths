import requests
from pathlib import Path
from pyrosm import OSM
import warnings
from src.config.settings import AreaConfig
from shapely.geometry import LineString, MultiLineString

class OSMPreprocessor:
    """Handles downloading and processing OSM PBF files into GeoDataFrames."""

    def __init__(self, area: str = "berlin", network_type: str = "walking"):
        self.config = AreaConfig(area)
        self.area = self.config.area
        self.pbf_path = self.config.pbf_file
        self.output_path = self.config.edges_output_file
        self.pbf_url = self.config.pbf_url
        self.bbox = self.config.bbox
        self.crs = self.config.crs
        self.network_type = network_type

    def download_pbf_if_missing(self):
        """Download the PBF file if it does not exist locally."""
        if self.pbf_path.exists():
            return
        if not self.pbf_url:
            raise ValueError("PBF file is missing and no download URL is provided!")

        print(f"Downloading PBF from: {self.pbf_url}")
        response = requests.get(self.pbf_url, timeout=10, stream=True)
        response.raise_for_status()
        with self.pbf_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download completed.")

    def extract_edges(self):
        """Extract and process the road network from the PBF file."""
        # Suppress Pandas FutureWarning (e.g. chained assignment)
        warnings.filterwarnings("ignore", category=FutureWarning, module="pyrosm")

        self.download_pbf_if_missing()

        osm = OSM(str(self.pbf_path), bounding_box=self.bbox) if self.bbox else OSM(str(self.pbf_path))
        graph = osm.get_network(network_type=self.network_type)

        graph = graph.to_crs(self.crs)

        graph = graph.explode(index_parts=False).reset_index(drop=True)
        graph = self._clean_geometry(graph)
        self._save_graph(graph)

        return graph

    def _clean_geometry(self, gdf):
        """Convert MultiLineStrings to LineStrings, compute lengths, and keep selected attributes."""
        def to_linestring(geom):
            if isinstance(geom, MultiLineString):
                return max(geom.geoms, key=lambda g: g.length)
            elif isinstance(geom, LineString):
                return geom
            return geom.convex_hull

        gdf = gdf.copy()
        gdf["geometry"] = gdf.geometry.apply(to_linestring)
        gdf["length_m"] = gdf.geometry.length
        gdf["edge_id"] = range(len(gdf))

        selected_attributes = [col for col in ["highway", "access"] if col in gdf.columns]
        columns = ["edge_id", "geometry", "length_m"] + selected_attributes


        if gdf.empty or gdf.geometry.is_empty.any():
            raise ValueError("Geometry cleaning resulted in empty or invalid edges.")

        return gdf[columns]

    def _save_graph(self, graph):
        """Save the processed graph to a Parquet file."""
        if graph.empty or graph.geometry.is_empty.any():
            raise ValueError("Cannot save: graph contains empty geometries.")
        graph.to_parquet(self.output_path)
        print(f"Saved {len(graph)} edges to {self.output_path}")

    
