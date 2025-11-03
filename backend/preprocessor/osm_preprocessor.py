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
from .landuse_influence import LanduseInfluenceBuilder


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

    def __init__(self, area: str, network_type: str, db: DatabaseClient | None = None):
        """
        Initialize the preprocessor with area-specific settings.

        Args:
            area (str): Area name (e.g., 'berlin').
            network_type (str): Network type ('walking', 'cycling', 'driving').
        """
        self.area = area.lower()
        self.network_type = network_type.lower()
        self.db = db or DatabaseClient()
        self.downloader = OSMDownloader(self.area)
        self.area_config = self.downloader.area_config
        self.crs = self.area_config.crs

    
    # Public interface

    def run(self):
        """Main entry point: run all preprocessing steps."""
        if self.network_type == "walking":
            self._extract_landuse()

        edges = self._load_and_prepare_edges()
        self._save_edges_to_db(edges)
        self._clean_edges_in_db()

        if self.network_type == "walking":
            self._postprocess_walking_network()

        print(f"Preprocessing complete for '{self.area}' ({self.network_type})")


    # Internal methods
    
    def _extract_landuse(self):
        """Extract and save green landuse polygons (forest, park, meadow, etc.)."""
        osm = self.downloader.get_osm_instance()
        landuse = osm.get_landuse()
        green_tags = ["forest", "grass", "meadow", "recreation_ground", "park"]
        landuse = landuse[landuse["landuse"].isin(green_tags)]
        self.db.save_landuse(landuse, self.area, if_exists="append")
        print(f"Landuse data saved for '{self.area}'")

    def _load_and_prepare_edges(self):
        """Load OSM network data and prepare it for database insertion."""
        warnings.filterwarnings("ignore", category=FutureWarning, module="pyrosm")
        osm = self.downloader.get_osm_instance()
        gdf = osm.get_network(network_type=self.network_type)

        if gdf is None or gdf.empty:
            raise ValueError(f"No '{self.network_type}' network edges found for area '{self.area}'.")

        gdf = gdf.to_crs(self.crs).explode(index_parts=False).reset_index(drop=True)
        gdf["edge_id"] = range(1, len(gdf) + 1)
        gdf = self._filter_to_selected_columns(gdf)

        if self.network_type == "driving":
            gdf = self._clean_maxspeed(gdf)

        return gdf

    def _save_edges_to_db(self, edges):
        """Save raw edges to the database."""
        self.db.save_edges(edges, self.area, self.network_type, if_exists="append")
        print(f"Edges saved to database for '{self.area}' ({self.network_type})")

    def _clean_edges_in_db(self):
        """Clean and enrich edges in the database using SQL transformations."""
        cleaner = EdgeCleanerSQL(self.db)
        cleaner.run_full_cleaning(self.area, self.network_type)
        print(f"SQL cleaning complete for '{self.area}' ({self.network_type})")

    def _postprocess_walking_network(self):
        """Run node generation and influence calculations (walking only)."""
        builder = NodeBuilder(self.db, self.area, self.network_type)
        builder.build_nodes_and_attach_to_edges()

        cleaner = EdgeCleanerSQL(self.db)
        cleaner.remove_disconnected_edges(self.area, self.network_type)

        builder.remove_unused_nodes()
        builder.assign_tile_ids()

        tib = TrafficInfluenceBuilder(self.db, self.area)
        tib.compute_cumulative_influence_by_tile()
        tib.summarize_influence_distribution()

        lib = LanduseInfluenceBuilder(self.db, area=self.area)
        lib.run()

        eib = EnvInfluenceBuilder(self.db, area=self.area)
        eib.run()

        print(f"Postprocessing (nodes + influences) complete for '{self.area}' ({self.network_type})")

    # Utility methods
    
    def _filter_to_selected_columns(self, gdf):
        """Ensure the GeoDataFrame includes all expected columns."""
        selected = BASE_COLUMNS + EXTRA_COLUMNS.get(self.network_type, [])
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

    def _clean_maxspeed(self, gdf):
        """Clean 'maxspeed' column to contain only numeric values."""
        def parse_speed(val):
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return None

        if "maxspeed" in gdf.columns:
            original_count = len(gdf)
            gdf["maxspeed"] = gdf["maxspeed"].apply(parse_speed).astype("Int64")
            valid_count = gdf["maxspeed"].count()
            null_count = original_count - valid_count
            print(f"maxspeed cleaned: {valid_count} valid, {null_count} set to NULL")

        return gdf
