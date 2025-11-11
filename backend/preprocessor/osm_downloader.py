"""
Download and load OpenStreetMap (OSM) PBF data for a configured area.
"""
from pathlib import Path
import requests
from pyrosm import OSM
from src.config.settings import AreaConfig


class OSMDownloader:
    """Download and access OSM PBF data for a given area."""

    def __init__(self, area_name: str):
        """
        Initialize with area name from configuration.

        Args:
            area_name (str): Area identifier defined in settings.
        """
        self.area_config = AreaConfig(area_name)
        self.local_path = self.area_config.pbf_file

    def download_if_missing(self):
        """
        Download the OSM PBF file if it does not already exist locally.

        The file is retrieved from the URL defined in 'AreaConfig.pbf_url'.
        The download is streamed to disk in chunks to avoid memory issues.

        Raises:
            ValueError: If no download URL is provided.
            requests.HTTPError: If the download fails.
        """
        if self.local_path.exists():
            return
        if not self.area_config.pbf_url:
            raise ValueError("No PBF URL configured for this area.")
        print(f"Downloading {self.area_config.pbf_url} ...")
        response = requests.get(self.area_config.pbf_url,
                                stream=True, timeout=10)
        response.raise_for_status()
        with self.local_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded PBF to {self.local_path}")

    def save_bbox_network_to_file(self, network_type: str, file_format: str = "gpkg") -> Path:
        """
        Extracts a network of edges from the OSM PBF file for the
        configured area and saves it to disk.

        The network is filtered using the bounding box defined in AreaConfig. 
        The result is saved in either GPKG or Parquet format, 
        depending on the specified file_format.

        Args:
            network_type (str): Type of network to extract ('walking', 'cycling', 'driving').
            file_format (str): Output file format ('gpkg' or 'parquet'). Defaults to 'gpkg'.

        Returns:
            Path: Full path to the saved network file.

        Raises:
            ValueError: If no edges are found or an unsupported format is specified.
        """
        self.download_if_missing()
        osm = OSM(str(self.local_path), bounding_box=self.area_config.bbox)
        edges = osm.get_network(network_type=network_type)
        if edges is None or edges.empty:
            raise ValueError(
                f"No edges found for '{network_type}' in '{self.area_config.area}'")

        output_path = self.area_config.get_raw_osm_file_path(
            network_type, file_format)

        if file_format == "gpkg":
            edges.to_file(output_path, driver="GPKG")
        elif file_format == "parquet":
            edges.to_parquet(output_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        print(f"Saved raw OSM network to {output_path}")
        return output_path
