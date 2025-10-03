# config/settings.py

"""
Configuration settings for EcoPaths backend.
"""
from pathlib import Path

from pathlib import Path


import os


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


class RedisConfig:
    """
    Configuration class for Redis connection settings.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0,
                 default_expire: int = 3600):
        """Initialize Redis configuration.

        Args:
            host (str, optional): Redis host. Defaults to "localhost".
            port (int, optional): Redis port. Defaults to 6379.
            db (int, optional): Redis database number. Defaults to 0.
            default_expire (int, optional): Default expiration time in seconds. Defaults to 3600.
        """
        self.host = os.getenv("REDIS_HOST", host)
        self.port = int(os.getenv("REDIS_PORT", port))
        self.db = int(os.getenv("REDIS_DB", db))
        self.default_expire = int(
            os.getenv("REDIS_DEFAULT_EXPIRE", default_expire))
