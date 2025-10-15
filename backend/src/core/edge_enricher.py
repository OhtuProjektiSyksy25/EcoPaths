"""Module for enriching road network edges with air quality data."""

from pathlib import Path
import geopandas as gpd
from src.config.settings import AreaConfig


class EdgeEnricher:
    """
    EdgeEnricher handles spatial data for environmental routing and analysis.

    It loads preprocessed road network data and optionally combines it with air quality data.
    Designed to work immediately with road data, and extend easily when air quality data is added.
    """

    def __init__(self, area: str = "berlin"):
        """
        Initialize the model with a specific area.

        Parameters:
            area (str): Area identifier (e.g., 'berlin'). Must match AreaConfig settings.
        """
        self.config = AreaConfig(area)
        self.area = area
        self.road_gdf = None
        self.air_quality_gdf = None
        self.combined_gdf = None

    @property
    def area_config(self) -> AreaConfig:
        """
        Exposes the AreaConfig instance used by this enricher.

        Returns:
            AreaConfig: Configuration object for the selected area.
        """
        return self.config

    def load_data(self):
        """
        Load road network and air quality data from files.

        Reads the edge data from a Parquet file and the air quality data from a GeoJSON file.
        Stores the results in `road_gdf` and `air_quality_gdf`.
        """
        self.road_gdf = gpd.read_parquet(self.config.edges_output_file)
        self.air_quality_gdf = gpd.read_file(self.config.aq_output_file)

    def combine_data(self):
        """
        Combine road network with air quality data.

        Uses polygon intersection as the primary method. If the AQ data consists of points only,
        it falls back to nearest-point join.

        Aggregation of multiple AQ matches per edge is always performed (mean of numeric cols).
        """
        if self.air_quality_gdf is None:
            print("Air quality data not loaded, skipping combination.")
            self.combined_gdf = None
            return

        geom_types = set(self.air_quality_gdf.geom_type)
        print(f"Detected AQ geometry types: {geom_types}")

        # Use polygon intersection if any polygons exist
        if any("Polygon" in g for g in geom_types):
            print("Performing intersection join (polygon-based AQ data).")
            self.combined_gdf = gpd.sjoin(
                self.road_gdf,
                self.air_quality_gdf,
                how="left",
                predicate="intersects"
            )
            self.combined_gdf = self.combined_gdf.drop(
                columns=["index_right"], errors="ignore")
        # Otherwise, fallback to nearest-point join
        elif any("Point" in g for g in geom_types):
            print("No polygons detected. Performing nearest join (point-based AQ data).")
            self.combined_gdf = gpd.sjoin_nearest(
                self.road_gdf,
                self.air_quality_gdf,
                how="left",
                distance_col="distance_to_aq"
            )
            self.combined_gdf = self.combined_gdf.drop(
                columns=["index_right"], errors="ignore")
        else:
            print("Unsupported AQ geometry type. No join performed.")
            self.combined_gdf = None
            return

        # handle potential duplicates (multiple AQ features per edge)
        if self.combined_gdf is not None and "edge_id" in self.combined_gdf.columns:
            dup_count = self.combined_gdf.duplicated(subset="edge_id").sum()
            if dup_count > 0:
                print(
                    f"Found {dup_count} duplicate edges. Aggregating aq_value (mean).")

            aq_agg = self.combined_gdf.groupby("edge_id", as_index=False)[
                ["aq_value"]].mean()
            self.combined_gdf = self.road_gdf.merge(
                aq_agg, on="edge_id", how="left")

    def save_combined_data(self, output_path: Path):
        """
        Save the combined dataset to a Parquet file.

        Parameters:
            output_path (Path): Destination path for the output file.
        """
        if self.combined_gdf is not None:
            self.combined_gdf.to_parquet(output_path)
            print(f"Combined data saved to: {output_path}")
        else:
            print("No combined data to save.")

    def get_enriched_edges(self, overwrite: bool = False) -> gpd.GeoDataFrame:
        """
        Return the most relevant network data.

        If enriched data file exists, load and return it.
        If not, generate it by combining road and AQ data, save it, and return.

        Returns:
            GeoDataFrame: Road network with or without air quality data.
        """

        enriched_path = self.config.enriched_output_file

        if enriched_path.exists() and not overwrite:
            print("Enriched data file found. Loading from disk.")
            return gpd.read_parquet(enriched_path)

        print("Enriched data file not found or overwrite requested. Generating now...")
        self.combine_data()
        self.save_combined_data(enriched_path)

        if self.combined_gdf is not None:
            print("Returning newly combined road and air quality network.")
            return self.combined_gdf

        print("Combination failed. Returning original road network.")
        return self.road_gdf
