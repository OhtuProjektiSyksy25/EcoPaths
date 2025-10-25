"""
Download and process OpenStreetMap data into a cleaned road network.
"""

import warnings
import geopandas as gpd
from pyrosm import OSM
from src.database.db_client import DatabaseClient
from .edge_cleaner_sql import EdgeCleanerSQL
from .osm_downloader import OSMDownloader
from .node_builder import NodeBuilder


class OSMPreprocessor:
    """
    Downloads and processes OpenStreetMap (OSM) data into a cleaned road network.

    This class handles:
    - Area-specific configuration and bounding box setup
    - Downloading and parsing OSM PBF data
    - Converting raw network data into GeoDataFrame
    - Saving raw edges to the database
    - Delegating cleaning to SQL-based EdgeCleanerSQL

    Note: Node processing is not handled here.
    """

    def __init__(self, area: str, network_type: str):
        """
        Initialize the preprocessor with area-specific settings.

        Args:
            area (str): Area name (e.g., 'berlin').
            network_type (str): Network type ('walking', 'cycling', 'driving').
        """
        self.area = area.lower()
        self.network_type = network_type
        self.downloader = OSMDownloader(self.area)
        self.area_config = self.downloader.area_config
        self.crs = self.area_config.crs

    def extract_edges(self):
        """
        Extract and clean road network edges for the configured area.

        Steps:
        1. Load OSM data using Pyrosm
        2. Convert to GeoDataFrame and normalize geometries
        3. Save raw edges to PostGIS
        4. Clean and enrich edges using SQL-based operations
        """
        warnings.filterwarnings(
            "ignore", category=FutureWarning, module="pyrosm")

        # Step 1–2: Load and prepare raw edges
        osm = self.downloader.get_osm_instance()
        edges_gdf = self.prepare_raw_edges(osm)

        # Step 3: Save to database
        db = DatabaseClient()
        db.save_edges(edges_gdf, self.area,
                      self.network_type, if_exists="replace")

        # Step 4: Clean and enrich via SQL
        cleaner = EdgeCleanerSQL(db)
        cleaner.normalize_geometry(self.area, self.network_type)
        cleaner.drop_invalid_geometries(self.area, self.network_type)
        cleaner.filter_access(self.area, self.network_type)
        cleaner.compute_lengths(self.area, self.network_type)
        cleaner.assign_tile_ids(self.area, self.network_type)

        builder = NodeBuilder(db, self.area, self.network_type)
        builder.build_nodes_and_attach_to_edges()

        print(
            f"Edge preprocessing complete for '{self.area}' ({self.network_type})")
        cleaned_gdf = db.load_edges(self.area, self.network_type)
        return cleaned_gdf

    def prepare_raw_edges(self, osm: OSM) -> gpd.GeoDataFrame:
        """
        Prepare raw edge geometries from OSM data.

        - Extracts network edges using the specified network type
        - Converts geometries to target CRS
        - Explodes MultiLineStrings into individual LineStrings

        Args:
            osm (OSM): Pyrosm OSM instance with bounding box and data source.

        Returns:
            GeoDataFrame: Raw edge geometries in target CRS.
        """
        edges_raw = osm.get_network(network_type=self.network_type)
        if edges_raw is None or edges_raw.empty:
            raise ValueError(
                f"No '{self.network_type}' network edges found for area '{self.area}'.")

        edges_raw = edges_raw.to_crs(self.crs)
        edges_raw = edges_raw.explode(index_parts=False).reset_index(drop=True)
        return edges_raw
