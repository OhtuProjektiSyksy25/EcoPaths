"""
Download and process OpenStreetMap data into a cleaned road network.
"""

import warnings
import geopandas as gpd
from pyrosm import OSM
from src.database.db_client import DatabaseClient
from src.config.columns import BASE_COLUMNS, EXTRA_COLUMNS
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
        5. If network type is 'walking':
        - Build nodes and attach to edges
        - Remove disconnected components
        - Assign tile IDs
        - Compute traffic and environmental influence
        """
        warnings.filterwarnings(
            "ignore", category=FutureWarning, module="pyrosm")

        # Step 1–2: Load and prepare raw edges
        osm = self.downloader.get_osm_instance()
        edges_gdf = self.prepare_raw_edges(osm)
        edges_gdf = self.filter_to_selected_columns(
            edges_gdf, self.network_type)
        if self.network_type == "driving":
            edges_gdf = self.clean_maxspeed_column(edges_gdf)
            edges_gdf = self.clean_width_column(edges_gdf)

        # Step 3: Save to database
        db = DatabaseClient()
        db.save_edges(edges_gdf, self.area,
                      self.network_type, if_exists="append")

        # Step 4: Clean and enrich via SQL
        cleaner = EdgeCleanerSQL(db)
        cleaner.run_full_cleaning(self.area, self.network_type)

        # Step 5
        if self.network_type == "walking":
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

        edges_raw["edge_id"] = range(1, len(edges_raw) + 1)

        return edges_raw

    def filter_to_selected_columns(self, gdf, network_type):
        """
        Filters and ensures the GeoDataFrame includes all expected columns
        defined for the given network type. Missing columns are added
        with default None or type-appropriate placeholder values.
        """
        selected = BASE_COLUMNS + EXTRA_COLUMNS.get(network_type, [])

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

    def clean_maxspeed_column(self, gdf):
        """
        Cleans the 'maxspeed' column in a GeoDataFrame by retaining only numeric values.
        Args:
            gdf (GeoDataFrame): Input GeoDataFrame containing a 'maxspeed' column.

        Returns:
            GeoDataFrame: Modified GeoDataFrame with cleaned 'maxspeed' values (integers or None).
        """
        def parse_speed(val):
            """Parses a speed value into an integer, or returns None if invalid."""
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return None

        if "maxspeed" in gdf.columns:
            original_count = len(gdf)
            gdf["maxspeed"] = gdf["maxspeed"].apply(
                parse_speed).astype("Int64")
            valid_count = gdf["maxspeed"].count()  # excludes None
            null_count = original_count - valid_count
            print(
                f"maxspeed cleaned: {valid_count} valid, {null_count} set to NULL")

        return gdf

    def clean_width_column(self, gdf):
        """
        Cleans the 'width' column by extracting numeric values and converting to float.
        Non-numeric or malformed values are replaced with None.
        """
        def parse_width(val):
            try:
                # Poista yksiköt kuten 'm', 'meters', jne.
                if isinstance(val, str):
                    val = val.strip().lower().replace("m", "").replace("meters", "").strip()
                return float(val)
            except (ValueError, TypeError):
                return None

        if "width" in gdf.columns:
            gdf["width"] = gdf["width"].apply(parse_width).astype("float64")
        return gdf
