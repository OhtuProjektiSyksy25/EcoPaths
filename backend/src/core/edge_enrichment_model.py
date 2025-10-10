"""Module for enriching road network edges with air quality data."""

from pathlib import Path
import geopandas as gpd
from src.config.settings import AreaConfig


class EdgeEnrichmentModel:
    """
    EdgeEnrichmentModel handles spatial data for environmental routing and analysis.

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

        # Load road network from preprocessed Parquet file
        self.road_gdf = gpd.read_parquet(self.config.edges_output_file)

        # Placeholders for optional air quality and combined data
        self.air_quality_gdf = None
        self.combined_gdf = None

    def load_air_quality_data(self, filepath: Path):
        """
        Load air quality data from a file and reproject it to match the road network CRS.

        Parameters:
            filepath (Path): Path to the air quality dataset (GeoJSON, Shapefile, etc.)
        """
        if not filepath.exists():
            print(
                f"Air quality file not found: {filepath}. Proceeding without it.")
            return
        self.air_quality_gdf = gpd.read_file(
            filepath).to_crs(self.road_gdf.crs)

        self.air_quality_gdf = gpd.read_file(
            filepath).to_crs(self.road_gdf.crs)

    def combine_data(self):
        """
        Combine road network with air quality data using spatial join.
        If not AQ data available, skip combining and use road network as-is.
        """
        if self.air_quality_gdf is None:
            print("Air quality data not loaded. Skipping combination.")
            self.combined_gdf = None
            return

        self.combined_gdf = gpd.sjoin(
            self.road_gdf,
            self.air_quality_gdf,
            how="left",
            predicate="intersects"
        )

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

    def get_enriched_edges(self) -> gpd.GeoDataFrame:
        """
        Return the most relevant network data.

        If air quality has been combined, return the enriched network.
        Otherwise, return the original road network.

        Returns:
            GeoDataFrame: Road network with or without air quality data.
        """
        if self.combined_gdf is not None:
            print("Returning combined road and air quality network.")
            return self.combined_gdf

        print("Returning original road network.")
        return self.road_gdf
