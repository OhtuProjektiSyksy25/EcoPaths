# config/settings.py

"""
Configuration settings for EcoPaths backend.
"""
from pathlib import Path
import os


# === Area-specific settings ===
AREA_SETTINGS = {
    "berlin": {
        # WGS84 (EPSG:4326), use None for full file
        "bbox": [13.300, 52.4525, 13.510, 52.5875],
        "pbf_url": "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf",
        "crs": "EPSG:25833",
    },
    "la": {
        "bbox": [-118.30, 33.95, -118.083, 34.13],  # WGS84 (EPSG:4326)
        "pbf_url": "https://download.geofabrik.de/north-america/us/california/socal-latest.osm.pbf",
        "crs": "EPSG:2229",
    },
    "helsinki": {
        "bbox": [24.80, 60.13, 25.20, 60.30],  # WGS84 (EPSG:4326)
        "pbf_url": "https://download.geofabrik.de/europe/finland-latest.osm.pbf",
        "crs": "EPSG:3067",  # ETRS-TM35FIN
    },
}


class AreaConfig:
    """Configuration class for area-specific parameters."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, area: str = "berlin"):
        self.area = area.lower()
        if self.area not in AREA_SETTINGS:
            raise ValueError(f"Unknown area: {self.area}")

        settings = AREA_SETTINGS[self.area]
        self.bbox = settings["bbox"]
        self.pbf_url = settings["pbf_url"]
        self.crs = settings["crs"]

        self.project_root = Path(__file__).resolve().parents[2]
        self.data_dir = self.project_root / "preprocessor" / "data"
        self.output_dir = self.project_root / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # === File paths ===
        self.pbf_file = self.data_dir / f"{self.area}-latest.osm.pbf"
        self.edges_output_file = self.output_dir / f"{self.area}_edges.parquet"
        self.aq_output_file = self.output_dir / f"{self.area}_aq.geojson"
        self.enriched_output_file = self.output_dir / \
            f"{self.area}_enriched.parquet"


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
