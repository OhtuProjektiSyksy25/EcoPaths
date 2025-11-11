# pylint: disable=invalid-name

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
        "display_name": "Berlin",
        "bbox": [13.30, 52.46, 13.51, 52.59],  # WGS84 EPSG:4326
        "pbf_url": "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf",
        "crs": "EPSG:25833",
        "tile_size_m": 500,
        "focus_point": [13.404954, 52.520008]
    },
    "la": {
        "display_name": "Los Angeles",
        "bbox": [-118.28, 34.02, -118.24, 34.06],  # WGS84 (EPSG:4326)
        "pbf_url": "https://download.geofabrik.de/north-america/us/california/socal-latest.osm.pbf",
        "crs": "EPSG:2229",
        "tile_size_m": 500,
        "focus_point": [-118.2437, 34.0522]
    },
    "helsinki": {
        "display_name": "Helsinki",
        "bbox": [24.80, 60.13, 25.20, 60.30],  # WGS84 (EPSG:4326)
        "pbf_url": "https://download.geofabrik.de/europe/finland-latest.osm.pbf",
        "crs": "EPSG:3067",  # ETRS-TM35FIN
        "tile_size_m": 500,
        "focus_point": [24.9384, 60.1699]
    },
    "testarea": {
        "display_name": "Test Area",
        "bbox": [13.375, 52.50, 13.395, 52.52],  # small area in Berlin
        "pbf_url": "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf",
        "crs": "EPSG:25833",
        "tile_size_m": 500,
        "focus_point": [13.385, 52.51]
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
            if self.area.startswith("test"):
                AREA_SETTINGS[self.area] = AREA_SETTINGS.get("testarea", {})
            else:
                raise ValueError(f"Unknown area: {self.area}")

        settings = AREA_SETTINGS[self.area]
        self.bbox = settings["bbox"]
        self.pbf_url = settings["pbf_url"]
        self.crs = settings["crs"]
        self.tile_size_m = settings.get("tile_size_m", 500)
        self.focus_point = settings["focus_point"]

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


# Load .env.test for tests, otherwise normal .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = ".env.test" if os.getenv("ENV") == "test" else ".env"
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"
ENV_PATH = os.path.join(BASE_DIR, "..", "..", ENV_FILE)

DB_URL = os.getenv("DB_URL")

if not DB_URL:
    if os.path.exists(ENV_PATH):
        load_dotenv(dotenv_path=ENV_PATH, override=True)
    else:
        raise FileNotFoundError(f"Environment file not found: {ENV_PATH}")


@dataclass
class DatabaseConfig:
    """Configuration for PostgreSQL database."""
    url: str = DB_URL

    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))

    user: str = (
        os.getenv("DB_USER_TEST")
        if os.getenv("ENV") == "test"
        else os.getenv("DB_USER", "pathplanner")
    )
    password: str = (
        os.getenv("DB_PASSWORD_TEST")
        if os.getenv("ENV") == "test"
        else os.getenv("DB_PASSWORD", "sekret")
    )
    dbname: str = (
        os.getenv("DB_NAME_TEST")
        if os.getenv("ENV") == "test"
        else os.getenv("DB_NAME", "ecopaths")
    )

    @property
    def connection_string(self) -> str:
        """Return SQLAlchemy-compatible PostgreSQL connection string."""
        if self.url:
            return self.url

        if not self.dbname:
            raise ValueError(
                "Database name is not set. Check your .env or .env.test file.")

        if os.getenv("ENV") == "test":
            assert "test" in self.dbname.lower(), "Not in test database"

        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.dbname}"
        )


class Settings:
    """Unified access to all major config classes."""

    def __init__(self, area: str):
        """
        Initialize all configuration sections.

        Args:
            area (str): Area name for area-specific settings.
        """
        self.area = AreaConfig(area)
        self.redis = RedisConfig()
        self.db = DatabaseConfig()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.TEST_MODE = TEST_MODE


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
