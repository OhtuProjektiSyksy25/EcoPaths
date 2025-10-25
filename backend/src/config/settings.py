"""
Configuration settings for EcoPaths backend.

Provides area-specific settings, Redis and PostgreSQL configurations,
and unified access through the Settings class.
"""

from pathlib import Path
import os
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv


# === Area-specific settings ===
AREA_SETTINGS = {
    "berlin": {
        "bbox": [13.30, 52.46, 13.51, 52.59],  # WGS84 EPSG:4326
        "pbf_url": "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf",
        "crs": "EPSG:25833",
        "tile_size_m": 500,
    },
    "la": {
        "bbox": [-118.28, 34.02, -118.24, 34.06],  # WGS84 (EPSG:4326)
        "pbf_url": "https://download.geofabrik.de/north-america/us/california/socal-latest.osm.pbf",
        "crs": "EPSG:2229",
        "tile_size_m": 500,
    },
    "helsinki": {
        "bbox": [24.80, 60.13, 25.20, 60.30],  # WGS84 (EPSG:4326)
        "pbf_url": "https://download.geofabrik.de/europe/finland-latest.osm.pbf",
        "crs": "EPSG:3067",  # ETRS-TM35FIN
        "tile_size_m": 500,
    },
    "testarea": {
        "bbox": [13.375, 52.50, 13.395, 52.52],  # small area in Berlin
        "pbf_url": "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf",
        "crs": "EPSG:25833",
        "tile_size_m": 500,
    },
}


class AreaConfig:
    """Configuration class for area-specific parameters."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, area: str = "berlin"):
        """
        Initialize area configuration.

        Args:
            area (str): Area name as defined in AREA_SETTINGS.
        """
        self.area = area.lower()
        if self.area not in AREA_SETTINGS:
            raise ValueError(f"Unknown area: {self.area}")

        settings = AREA_SETTINGS[self.area]
        self.bbox = settings["bbox"]
        self.pbf_url = settings["pbf_url"]
        self.crs = settings["crs"]
        self.tile_size_m = settings.get("tile_size_m", 500)

        self.project_root = Path(__file__).resolve().parents[2]
        self.pbf_data_dir = self.project_root / "preprocessor" / "data"
        self.output_dir = self.project_root / "data"
        self.pbf_data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.pbf_file = self.pbf_data_dir / f"{self.area}-latest.osm.pbf"


class RedisConfig:
    """Configuration class for Redis connection settings."""

    def __init__(self):
        """Initialize Redis configuration from environment variables."""
        self.url = os.getenv("REDIS_URL")
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.default_expire = int(os.getenv("REDIS_DEFAULT_EXPIRE", "3600"))


load_dotenv()


@dataclass
class DatabaseConfig:
    """Configuration for PostgreSQL database."""

    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "postgres")
    dbname: str = os.getenv("DB_NAME", "ecopaths")
    url: str = os.getenv("DB_URL")

    @property
    def connection_string(self) -> str:
        """Return SQLAlchemy/PostGIS-compatible connection string."""

        if self.url:
            return self.url

        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.dbname}"
        )


class Settings:
    """Unified access to all major config classes."""

    def __init__(self, area: str = "berlin"):
        """
        Initialize all configuration sections.

        Args:
            area (str): Area name for area-specific settings.
        """
        self.area = AreaConfig(area)
        self.redis = RedisConfig()
        self.db = DatabaseConfig()


@lru_cache(maxsize=None)
def get_settings(area: str) -> Settings:
    """
    Retrieve a cached Settings instance for the specified area.

    This function returns a unified configuration object containing area-specific settings,
    Redis connection parameters, and database credentials. It uses an LRU cache to avoid
    reinitializing the same area configuration multiple times.

    Args:
        area (str): Name of the area (e.g., "berlin", "helsinki").

    Returns:
        Settings: A configuration object with access to AreaConfig, RedisConfig, and DatabaseConfig.
    """
    return Settings(area)
