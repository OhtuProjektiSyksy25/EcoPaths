"""
OSM preprocessing utilities for EcoPaths backend.

Includes downloading .pbf files, extracting road networks,
cropping to bounding box, and reprojecting to a suitable CRS
for accurate spatial analysis.
"""
import os
import requests
from pathlib import Path
from pyrosm import OSM
from sqlalchemy import inspect
from src.config.settings import AreaConfig, USE_POSTGIS
from src.db.db_manager import DatabaseManager

class OSMPreprocessor:
    """Handles downloading and processing OSM PBF files into GeoDataFrames."""

    def __init__(self, area: str = "la", network_type: str = "walking"):
        self.area = area.lower()
        self.config = AreaConfig(area)
        self.pbf_path: Path = self.config.pbf_file
        self.output_path: Path = self.config.output_file
        self.pbf_url = self.config.pbf_url
        self.bbox = self.config.bbox  # None = use full PBF
        self.network_type = network_type
        self.table_name = f"edges_{self.area}"

        self.pbf_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def download_pbf_if_missing(self):
        """Download the PBF file if it does not exist locally."""
        if not self.pbf_path.exists():
            if not self.pbf_url:
                raise ValueError("PBF file is missing and no download URL is provided!")
            print(f"Downloading PBF from: {self.pbf_url}")
            r = requests.get(self.pbf_url, timeout=10, stream=True)
            with self.pbf_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Download completed.")

    def extract_edges(self):
        """
        Extract the road network from the PBF file for the configured area.

        Returns:
            GeoDataFrame: The processed and reprojected edge network
        """
        if USE_POSTGIS:
                db = DatabaseManager(table_name=self.table_name)
                if db.exists():
                    print(f"Table '{self.table_name}' already exists in PostGIS. Skipping extraction.")
                    return
        self.download_pbf_if_missing()

        # OSM network extraction
        if self.bbox:
            min_lon, min_lat, max_lon, max_lat = self.bbox
            osm = OSM(str(self.pbf_path), bounding_box=[min_lon, min_lat, max_lon, max_lat])
        else:
            osm = OSM(str(self.pbf_path))  # full extent
            
      # graph is GeoDataframe
        graph = osm.get_network(network_type=self.network_type)

  
        graph = self._reproject_graph(graph)

        # Save to PostGIS or Parquet
        self._save_graph(graph)

        return graph

    def _reproject_graph(self, graph):
        """Reproject the edge network to a projected CRS based on the area."""
        area_crs_map = {
            "berlin": "EPSG:25833",
            "la": "EPSG:2229",
        }
        crs = area_crs_map.get(self.area)
        if not crs:
            raise ValueError(f"Unknown area '{self.area}', no CRS defined.")
        return graph.to_crs(crs)

    def _save_graph(self, graph):
        """Save the GeoDataFrame to PostGIS or Parquet depending on USE_POSTGIS."""
        if USE_POSTGIS:
            self._save_to_postgis(graph)
        else:
            graph.to_parquet(self.output_path)
            print(f"Parquet edge list saved to {self.output_path} with {len(graph)} rows")

    def _save_to_postgis(self, graph):
        """Save the GeoDataFrame to a PostGIS table."""
        db = DatabaseManager(table_name=self.table_name)
        db.save(graph)
        print(f"Edge data saved to PostGIS table '{self.table_name}' with {len(graph)} rows")
