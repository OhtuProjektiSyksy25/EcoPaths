"""
Download and process OpenStreetMap data into a cleaned road network.

"""

import gc
import warnings
import geopandas as gpd
from src.database.db_client import DatabaseClient
from src.config.columns import BASE_COLUMNS_DF, EXTRA_COLUMNS
from src.config.settings import get_settings
from .edge_cleaner_sql import EdgeCleanerSQL
from .osm_downloader import OSMDownloader
from .node_builder import NodeBuilder
from .traffic_influence import TrafficInfluenceBuilder
from .env_influence import EnvInfluenceBuilder


class OSMPreprocessor:
    """
    Downloads and processes OpenStreetMap (OSM) data into a cleaned and enriched road network.

    This class handles:
    - Area-specific configuration and bounding box setup
    - Downloading and parsing OSM PBF data
    - Converting raw network data into GeoDataFrame
    - Saving raw edges to the database
    - Cleaning and enriching edges via SQL
    - Node generation and influence metrics for walking networks
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
        self.settings = get_settings(area)
        self.batch_size = self.settings.area.batch_size
        self.downloader = OSMDownloader(self.area)
        self.area_config = self.downloader.area_config
        self.crs = self.area_config.crs

    def extract_edges(self):
        """
        Extract and clean road network edges for the configured area.

        Steps:
        1. Load OSM data using Pyrosm
        2. Convert to GeoDataFrame and normalize geometries
        3. Save raw edges to PostGIS (in batches)
        4. Clean and enrich edges using SQL-based operations
        5. If network type is 'walking':
        - Build nodes and attach to edges
        - Remove disconnected components
        - Assign tile IDs
        - Compute traffic and environmental influence

        Notes:
            - Memory is explicitly freed before node generation using `gc.collect()`.
            - Batches of edges are saved to the database as they are processed.
        """
        warnings.filterwarnings(
            "ignore", category=FutureWarning, module="pyrosm")

        db = DatabaseClient()

        self.downloader.save_bbox_network_to_file(self.network_type)
        for batch in self.load_raw_edges_in_batches():
            batch = self.prepare_raw_edges(batch)
            batch = self.filter_to_selected_columns(batch, self.network_type)
            db.save_edges(batch, self.area, self.network_type,
                          if_exists="append")

        cleaner = EdgeCleanerSQL(db)
        cleaner.run_full_cleaning(self.area, self.network_type)

        if self.network_type == "walking":
            print("Freeing memory before node generation...")
            gc.collect()

            builder = NodeBuilder(db, self.area, self.network_type)
            builder.build_nodes_and_attach_to_edges()

            cleaner.remove_disconnected_edges(self.area, self.network_type)
            builder.remove_unused_nodes()
            builder.assign_tile_ids()

            tib = TrafficInfluenceBuilder(db, self.area)
            tib.compute_cumulative_influence_by_tile()
            tib.summarize_influence_distribution()

            eib = EnvInfluenceBuilder(db, area=self.area)
            eib.run()

        print(
            f"Edge preprocessing complete for '{self.area}' ({self.network_type})")

    def prepare_raw_edges(self, edges_raw) -> gpd.GeoDataFrame:
        """
        Prepare raw edge geometries from OSM data.

        Args:
            edges_raw (GeoDataFrame): Raw edge geometries loaded from file.

        Returns:
            GeoDataFrame: Cleaned edge geometries in target CRS 
            with exploded LineStrings and edge IDs.
        """

        edges_raw = edges_raw.to_crs(self.crs)
        edges_raw = edges_raw.explode(index_parts=False).reset_index(drop=True)

        return edges_raw

    def load_raw_edges_in_batches(self, file_format: str = "gpkg"):
        """
        Load raw edges from file if it exists and yield them in batches.

        Args:
            file_format (str): File format ('gpkg' or 'parquet').

        Yields:
            GeoDataFrame: Batches of edges with maximum size `self.batch_size`.

        Raises:
            FileNotFoundError: If the raw OSM file does not exist.

        Notes:
            - Returns a generator yielding subsets of the GeoDataFrame.
            - The GeoDataFrame is copied to avoid side-effects between batches.
        """
        file_path = self.area_config.get_raw_osm_file_path(
            self.network_type, file_format)
        if not file_path.exists():
            raise FileNotFoundError(f"No raw OSM file found at {file_path}")

        print(
            f"Loading raw edges from {file_path} in batches of {self.batch_size}...")
        if file_format == "gpkg":
            gdf = gpd.read_file(file_path)
        elif file_format == "parquet":
            gdf = gpd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        n = len(gdf)
        for start in range(0, n, self.batch_size):
            end = min(start + self.batch_size, n)
            yield gdf.iloc[start:end].copy()

    def filter_to_selected_columns(self, gdf, network_type):
        """
        Filters and ensures the GeoDataFrame includes all expected columns
        defined for the given network type. Missing columns are added
        with default None or type-appropriate placeholder values.

        Args:
            gdf (GeoDataFrame): Input data containing raw or cleaned edges.
            network_type (str): Type of network ('walking', 'cycling', 'driving').

        Returns:
            GeoDataFrame: Filtered data with expected columns and default values for missing ones.

        """
        selected = BASE_COLUMNS_DF + EXTRA_COLUMNS.get(network_type, [])

        if "geometry" not in selected:
            selected.append("geometry")

        filtered = gdf[[col for col in gdf.columns if col in selected]].copy()

        for col in selected:
            if col not in filtered.columns:
                if col.endswith("_influence"):
                    filtered[col] = 1.0
                else:
                    filtered[col] = None

        return filtered.set_geometry("geometry")
