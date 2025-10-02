# config/settings.py

"""
Configuration settings for EcoPaths backend.
"""

from pathlib import Path


class AreaConfig:
    """
    Configuration class for different geographic areas.

    Provides bounding box coordinates, PBF file URLs, local file paths,
    and Parquet output paths for each supported area.
    """

    def __init__(self, area: str = "berlin"):
        """
        Initialize configuration for a specific area.

        Args:
            area (str, optional): Area identifier, e.g., "la" or "berlin".
                                  Defaults to "berlin".
        """

        self.area = area.lower()
        self.project_root = Path(__file__).resolve().parents[2]
        self._set_area_settings()

    def _set_area_settings(self):
        """
        Set area-specific settings based on the chosen area.

        Attributes set:
            bbox (list): Bounding box [min_lon, min_lat, max_lon, max_lat]
            pbf_url (str): URL to download the PBF file
            pbf_file (str): Local path for the PBF file
            output_file (str): Path to save the Parquet edge list

        Raises:
            ValueError: If an unknown area is provided
        """
        if self.area == "la":
            self.bbox = [-118.33, 33.93, -118.20, 34.10]
            self.pbf_url = (
                "https://download.geofabrik.de/north-america/us/california/socal-latest.osm.pbf"
            )
            self.pbf_file = self.project_root / \
                "preprocessor" / "data" / "socal-latest.osm.pbf"
            self.output_file = self.project_root / "data" / "la_edges.parquet"

        elif self.area == "berlin":
            self.bbox = [13.0884, 52.3383, 13.7611, 52.6755]
            self.pbf_url = (
                "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf"
            )
            self.pbf_file = self.project_root / \
                "preprocessor" / "data" / "berlin-latest.osm.pbf"
            self.output_file = self.project_root / "data" / "berlin_edges.parquet"

        else:
            raise ValueError(f"Unknown area: {self.area}")
