"""
Download and load OpenStreetMap (OSM) PBF data for a configured area.

Uses AreaConfig for area settings (URL, local path, bounding box).
Downloads missing PBF files and returns a pyrosm.OSM instance for data access.
"""
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

    def get_osm_instance(self):
        """
        Ensure PBF exists and return Pyrosm OSM object.
        Returns:
            pyrosm.OSM: A Pyrosm OSM instance initialized with the area's data.

        Raises:
            ValueError: If no PBF URL is configured and the file is missing.
            requests.HTTPError: If downloading the file fails.
        """

        self.download_if_missing()
        return OSM(str(self.local_path), bounding_box=self.area_config.bbox)
