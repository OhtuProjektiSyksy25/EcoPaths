import os
import requests
from pyrosm import OSM
from shapely.geometry import box
from backend.src.config.settings import AreaConfig

"""
OSM preprocessing utilities for EcoPaths backend.
"""


class OSMPreprocessor:
    """Handles downloading and processing OSM PBF files into GeoDataFrames."""

    def __init__(self, area: str = "la", network_type: str = "all"):
        """
        Initialize a Preprocessor instance for a given geographic area.

        This sets up the PBF file paths, output paths, and bounding box
        based on the area configuration.

        Args:
            area (str, optional): Area identifier, e.g., "la" or "berlin".
                                  Defaults to "la".
            network_type (str, optional): Type of OSM network to extract
                                          ('walking', 'cycling', 'all', etc.).
                                          Defaults to "all".
        """
        self.config = AreaConfig(area)
        self.pbf_path = self.config.pbf_file
        self.output_path = self.config.output_file
        self.pbf_url = self.config.pbf_url
        self.bbox = self.config.bbox
        self.network_type = network_type

        os.makedirs(os.path.dirname(self.pbf_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def download_pbf_if_missing(self):
        """
        Download the PBF file if it does not exist locally.

        Raises:
            ValueError: If the PBF file is missing and no URL is provided.
        """
        if not os.path.exists(self.pbf_path):
            if not self.pbf_url:
                raise ValueError(
                    "PBF file is missing and no download URL is provided!")
            print(f"Downloading PBF from: {self.pbf_url}")
            r = requests.get(self.pbf_url, timeout=10, stream=True)
            with open(self.pbf_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Download completed.")

    def extract_edges(self):
        """
        Extract the road network from the PBF file for the configured area
        and save it as a Parquet edge list.

        The network is cropped to the area's bounding box and filtered
        according to the selected network type.
        """

        self.download_pbf_if_missing()

        osm = OSM(self.pbf_path)
        # graph is GeoDataframe
        graph = osm.get_network(network_type=self.network_type)

        min_lon, min_lat, max_lon, max_lat = self.bbox
        bbox_polygon = box(min_lon, min_lat, max_lon, max_lat)
        graph = graph.loc[graph.geometry.intersects(bbox_polygon)].copy()

        graph.to_parquet(self.output_path)

        print(
            f"Parquet edge list saved to {self.output_path} with {len(graph)} rows")
