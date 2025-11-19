"""
OSM pipeline runner for preprocessing spatial data.

This module orchestrates the full preprocessing workflow for a given area:
- Creates grid tiles covering the area
- Downloads and processes green areas (parks, forests, etc.)
- Downloads and processes driving and walking networks
- Cleans and normalizes geometries
- Builds nodes and attaches them to edges
- Removes disconnected components and unused nodes
- Assigns tile IDs to nodes
- Calculates influence metrics (traffic, green, environmental)

The pipeline is executed in batch mode with memory cleanup and timing
information printed for each stage.
"""

import gc
import time

import geopandas as gpd

from src.database.db_client import DatabaseClient
from src.config.settings import get_settings
from src.utils.grid import Grid

from .osm_preprocessor import OSMPreprocessor
from .edge_cleaner_sql import EdgeCleanerSQL
from .green_cleaner_sql import GreenCleanerSQL
from .node_builder import NodeBuilder
from .traffic_influence import TrafficInfluenceBuilder
from .green_influence import GreenInfluenceBuilder
from .env_influence import EnvInfluenceBuilder


class OSMPipelineRunner:
    """
    Entry point for processing green areas, driving, and walking networks
    in batch mode with memory cleanup.
    """

    def __init__(self, area: str):
        self.area = area.lower()
        self.settings = get_settings(area)
        self.batch_size = self.settings.area.batch_size
        self.db = DatabaseClient()

    def run(self):
        """Run the full pipeline for the specified area."""
        start_time = time.time()
        self._process_grid()
        gridtime = time.time()
        print(
            f"[PIPELINE] Grid processing took {gridtime - start_time:.2f} seconds")
        self._process_green_areas()
        greentime = time.time()
        print(
            f"[PIPELINE] Green areas processing took {greentime - gridtime:.2f} seconds")
        self._process_network("driving")
        drivingtime = time.time()
        print(
            f"[PIPELINE] Driving network processing took {drivingtime - greentime:.2f} seconds")
        self._process_network("walking")
        walkingtime = time.time()
        print(
            f"[PIPELINE] Walking network processing took {walkingtime - drivingtime:.2f} seconds")

        end_time = time.time()
        elapsed = end_time - start_time
        print(
            f"[PIPELINE] Completed full pipeline for {self.area} in {elapsed:.2f} seconds")

    def _process_grid(self):
        """ Create a grid covering the area and save it to the database."""
        print(f"\n[PIPELINE] Creating grid for {self.area}")

        grid = Grid(self.settings.area)
        grid_gdf = grid.create_grid()
        self.db.save_grid(grid_gdf, area=self.area, if_exists="replace")

        print("[PIPELINE] Grid creation complete.\n")

    def _process_in_batches(self, gdf, prepare_fn, save_fn, *save_args):
        """Generic batch loop for processing and saving GeoDataFrames."""
        n = len(gdf)
        for start in range(0, n, self.batch_size):
            end = min(start + self.batch_size, n)
            batch = gdf.iloc[start:end].copy()

            batch = prepare_fn(batch)
            save_fn(batch, *save_args, if_exists="append")

            del batch
            gc.collect()

    def _process_green_areas(self):
        """Download, preprocess, and save green areas for the current area."""
        print(f"\n[PIPELINE] Processing green areas for {self.area}")
        preproc = OSMPreprocessor(self.area, network_type="walking")

        green_file = preproc.downloader.extract_and_save_green_areas(
            file_format="gpkg")
        gdf = gpd.read_file(green_file)

        total = len(gdf)
        print(
            f"[PIPELINE] Handling green areas in batches (total rows: {total})")

        self._process_in_batches(
            gdf,
            preproc.prepare_green_area_batch,
            self.db.save_green_areas,
            self.area
        )

        print(f"[PIPELINE] Saved {total} green areas to the database.")

        cleaner = GreenCleanerSQL(self.db)
        cleaner.run(self.area)

        print("[PIPELINE] Green areas processing complete.\n")

    def _process_network(self, network_type: str):
        """Process a driving or walking network for the current area."""
        print(
            f"\n[PIPELINE] Processing {network_type} network for {self.area}")
        preproc = OSMPreprocessor(self.area, network_type=network_type)

        network_file = preproc.downloader.extract_and_save_network(
            network_type)
        gdf = gpd.read_file(network_file)

        total = len(gdf)
        print(
            f"[PIPELINE] Handling {network_type} network in batches (total rows: {total})")

        self._process_in_batches(
            gdf,
            lambda b: preproc.filter_to_selected_columns(
                preproc.prepare_raw_edges(b), network_type),
            self.db.save_edges,
            self.area,
            network_type
        )

        print(
            f"[PIPELINE] Saved {total} {network_type} edges to the database.")

        # Edge cleaning / splitting
        cleaner = EdgeCleanerSQL(self.db)
        cleaner.run_full_cleaning(self.area, network_type)

        if network_type == "walking":
            start_time = time.time()
            builder = NodeBuilder(self.db, self.area, network_type)
            builder.build_nodes_and_attach_to_edges()
            cleaner.remove_disconnected_edges(self.area, network_type)
            builder.remove_unused_nodes()
            builder.assign_tile_ids()

            end_time = time.time()
            elapsed = end_time - start_time
            print(f"[PIPELINE] Completed node steps in {elapsed:.2f} seconds")

            # Influence calculations
            start_time = time.time()
            TrafficInfluenceBuilder(self.db, self.area).run()
            GreenInfluenceBuilder(self.db, self.area).run()
            EnvInfluenceBuilder(self.db, self.area).run()
            end_time = time.time()
            elapsed = end_time - start_time
            print(
                f"[PIPELINE] Completed influence calculations in {elapsed:.2f} seconds")

        print(
            f"[PIPELINE] {network_type.capitalize()} network processing complete.\n")
