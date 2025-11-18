"""
Download and load OpenStreetMap (OSM) PBF data for a configured area.
"""
from pathlib import Path
import warnings
import requests
from pyrosm import OSM
import pandas as pd
import geopandas as gpd
from src.config.settings import AreaConfig
from src.config.columns import LANDUSE_MAP, LEISURE_MAP, NATURAL_MAP

warnings.filterwarnings("ignore", category=FutureWarning, module="pyrosm")


class OSMDownloader:
    """Download and access OSM PBF data for a given area."""

    def __init__(self, area_name: str):
        """
        Initialize with area name from configuration.

        Args:
            area_name (str): Area identifier defined in settings.
        """
        self.area_config = AreaConfig(area_name)
        self.local_path = self.area_config.pbf_file

    def download_if_missing(self):
        """
        Download the OSM PBF file if it does not already exist locally.

        The file is retrieved from the URL defined in 'AreaConfig.pbf_url'.
        The download is streamed to disk in chunks to avoid memory issues.

        Raises:
            ValueError: If no download URL is provided.
            requests.HTTPError: If the download fails.
        """
        if self.local_path.exists():
            return
        if not self.area_config.pbf_url:
            raise ValueError("No PBF URL configured for this area.")
        print(f"Downloading {self.area_config.pbf_url} ...")
        response = requests.get(self.area_config.pbf_url,
                                stream=True, timeout=10)
        response.raise_for_status()
        with self.local_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded PBF to {self.local_path}")

    def write_layer_file(self, gdf: gpd.GeoDataFrame, name: str, file_format: str) -> Path:
        """
        Save a GeoDataFrame to disk in the specified format.

        Args:
            gdf (GeoDataFrame): The data to save.
            name (str): Name used to generate the output file.
            file_format (str): File format, either 'gpkg' or 'parquet'.

        Returns:
            Path: Full path to the saved file.

        Raises:
            ValueError: If the GeoDataFrame is empty or format unsupported.
        """
        if gdf.empty:
            raise ValueError(
                f"No features found for '{name}' in {self.area_config.area}")

        output_path = self.area_config.get_raw_file_path(name, file_format)

        if file_format == "gpkg":
            gdf.to_file(output_path, driver="GPKG")
        elif file_format == "parquet":
            gdf.to_parquet(output_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        print(f"Saved {name} to {output_path}")
        return output_path

    def extract_and_save_network(self, network_type: str, file_format: str = "gpkg") -> Path:
        """
        Extract a road network of the specified type within the bounding box and save to disk.
        """
        self.download_if_missing()
        osm = OSM(str(self.local_path), bounding_box=self.area_config.bbox)
        edges = osm.get_network(network_type=network_type)
        return self.write_layer_file(edges, f"{network_type}", file_format)

    def extract_and_save_green_areas(self, file_format: str = "gpkg") -> Path:
        """
        Extract green areas (parks, forests, grass, recreation grounds) and save to disk.

        Combines landuse, leisure, and natural layers from OSM to produce a comprehensive
        green areas GeoDataFrame with unified 'green_type' column.
        """
        self.download_if_missing()
        osm = OSM(str(self.local_path), bounding_box=self.area_config.bbox)

        # Landuse
        landuse = osm.get_landuse()
        green_landuse = landuse[landuse["landuse"].isin(
            LANDUSE_MAP.keys())].copy()
        green_landuse["green_type"] = green_landuse["landuse"].map(LANDUSE_MAP)

        # Leisure
        leisure = osm.get_pois(custom_filter={"leisure": True})
        green_leisure = leisure[leisure["leisure"].isin(
            LEISURE_MAP.keys())].copy()
        green_leisure["green_type"] = green_leisure["leisure"].map(LEISURE_MAP)

        # Natural
        natural = osm.get_pois(custom_filter={"natural": True})
        green_natural = natural[natural["natural"].isin(
            NATURAL_MAP.keys())].copy()
        green_natural["green_type"] = green_natural["natural"].map(NATURAL_MAP)

        # Combine all
        green_areas = gpd.GeoDataFrame(pd.concat(
            [green_landuse, green_leisure, green_natural],
            ignore_index=True
        ))

        if green_areas.empty:
            raise ValueError(
                f"No green areas found for {self.area_config.area}")

        return self.write_layer_file(green_areas, "green_areas", file_format)
