"""
ComputeModel module for EcoPaths backend.

This module processes preprocessed OSM edge data and prepares it for routing algorithms.

Edge data summary for algorithm developers:
- Format: GeoDataFrame with 6 columns
- CRS: Projected (e.g. EPSG:25833 for Berlin)
- Geometry: MultiLineString
- Lengths: Computed in meters (column: length_m)
- Tags: highway, bicycle, access
- Sample row:
    {
        'edge_id': 0,
        'geometry': <MULTILINESTRING (...)>,
        'length_m': 522.5,
        'highway': 'residential',
        'bicycle': None,
        'access': None
    }

Use `get_data_for_algorithm()` to retrieve clean and lightweight edge data.
"""


import os
import geopandas as gpd
from preprocessor.osm_preprocessing import OSMPreprocessor
from config.settings import AreaConfig


class ComputeModel:
    """Handles computation and formatting of edge data for algorithm module."""

    def __init__(self, area: str = "la"):
        """
        Initialize ComputeModel with area configuration.

        Args:
            area (str, optional): Area identifier. Defaults to "la".
        """
        self.area = area.lower()
        self.config = AreaConfig(area)
        self.input_path = self.config.output_file
        self.relevant_columns = ["edge_id", "geometry",
                                 "length_m", "highway", "bicycle", "access"]

    def load_edges(self) -> gpd.GeoDataFrame:
        """
        Load preprocessed edge data from Parquet file.

        Returns:
            GeoDataFrame: Loaded edge data.
        """
        return gpd.read_parquet(self.input_path)

    def compute_lengths(self, edges: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Assign unique edge IDs and compute geometry lengths in meters.

        Args:
            edges (GeoDataFrame): Preprocessed edge data with projected CRS.

        Returns:
            GeoDataFrame: Edge data with 'edge_id' and 'length_m' columns.
        """
        if not edges.crs or not edges.crs.is_projected:
            raise ValueError(
                "CRS must be projected for accurate length calculation.")

        edges = edges.copy()
        edges["edge_id"] = edges.index
        edges["length_m"] = edges.geometry.length
        return edges

    def get_data_for_algorithm(self) -> gpd.GeoDataFrame:
        """
        Load and process edge data, return it for algorithm module.

        Returns:
            GeoDataFrame: Processed edge data with length.
        """

        if not os.path.exists(self.input_path):
            if os.path.exists(self.config.pbf_file):
                print(
                    f"Edge file '{self.input_path}' missing. "
                    "Using existing PBF to generate edges..."
                )
            else:
                print("Edge file and PBF missing. Downloading and preprocessing...")
            preprocessor = OSMPreprocessor(area=self.area)
            preprocessor.extract_edges()

        edges = self.load_edges()
        edges = self.compute_lengths(edges)
        return self.to_lightweight(edges)

    def to_lightweight(self, edges: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Filter edge data to include only relevant columns for routing algorithms.

        Keeps:
            - edge_id: unique identifier
            - geometry: LineString geometry
            - length_m: computed length in meters
            - highway: road type
            - bicycle: bicycle access info
            - access: general access restrictions

        Args:
            edges (GeoDataFrame): Full edge dataset

        Returns:
            GeoDataFrame: Lightweight edge dataset
        """
        self.relevant_columns = ["edge_id", "geometry",
                                 "length_m", "highway", "bicycle", "access"]
        return edges[self.relevant_columns].copy()

    def __repr__(self):
        return f"<ComputeModel area={self.config.area}>"

    # This method provides a temporary interface between ComputeModel and RouteAlgorithm.
    # Once RouteService is implemented, this logic should be moved there.
    # Algorithm developer can use get_data_for_algorithm() directly in the meantime.

    # def get_route(self, origin: tuple, destination: tuple):
    #    edges = self.get_data_for_algorithm()
    #    algorithm = RouteAlgorithm(edges)
    #    return algorithm.compute(origin, destination)
