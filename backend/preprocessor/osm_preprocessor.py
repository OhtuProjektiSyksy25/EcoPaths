"""
Download and process OpenStreetMap data into a cleaned road network.
"""

import warnings
from pathlib import Path
import requests
import geopandas as gpd
from pyrosm import OSM
from shapely.geometry import Point, LineString, MultiLineString, GeometryCollection
from shapely.ops import split
from shapely.errors import TopologicalError
from src.config.settings import AreaConfig
from src.utils.grid import Grid


class OSMPreprocessor:
    """
    Handles downloading and processing OpenStreetMap (OSM) PBF files 
    into a cleaned GeoDataFrame of road network edges.

    This class supports area-specific configurations, bounding box filtering, 
    and network type selection.
    The output is saved as a Parquet file containing 
    simplified geometries and basic attributes.
    """

    def __init__(self, area: str = "berlin", network_type: str = "walking"):
        """
        Initialize the OSMPreprocessor with area-specific settings.

        Args:
            area (str): Name of the area defined in AREA_SETTINGS (e.g. 'berlin').
            network_type (str): Type of network to extract (e.g. 'walking', 'cycling').

        Sets up paths, bounding box, CRS, and download URL for the selected area.
        """
        self.config = AreaConfig(area)
        self.area = self.config.area
        self.pbf_path = self.config.pbf_file
        self.output_path = self.config.edges_output_file
        self.pbf_url = self.config.pbf_url
        self.bbox = self.config.bbox
        self.crs = self.config.crs
        self.network_type = network_type

    def download_pbf_if_missing(self):
        """
        Download the OSM PBF file from the configured URL if it does not exist locally.

        Raises:
            ValueError: If no download URL is provided.
            requests.HTTPError: If the download fails.
        """

        if self.pbf_path.exists():
            return
        if not self.pbf_url:
            raise ValueError(
                "PBF file is missing and no download URL is provided!")

        print(f"Downloading PBF from: {self.pbf_url}")
        response = requests.get(self.pbf_url, timeout=10, stream=True)
        response.raise_for_status()
        with self.pbf_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download completed.")

    def extract_edges(self):
        """
        Extract, process, and save road network edges for the configured area.

        Workflow:
        - Downloads PBF file if missing
        - Loads OSM network data and prepares geometries
        - Loads or generates spatial tile grid
        - Splits edges by tile boundaries and assigns tile IDs
        - Cleans and filters edge geometries
        - Saves final edge dataset to disk

        Returns:
            GeoDataFrame: Final processed edge data with tile assignments and attributes.
        """
        warnings.filterwarnings(
            "ignore", category=FutureWarning, module="pyrosm")

        self.download_pbf_if_missing()
        osm = OSM(str(self.pbf_path), bounding_box=self.bbox)
        graph = self._prepare_graph(osm)
        grid = self._load_or_create_grid()
        print("Preparing edges...")
        graph = self._assign_tiles(graph, grid)
        graph = self._clean_geometry(graph)
        self._save_graph(graph)
        return graph

    def _prepare_graph(self, osm: OSM) -> gpd.GeoDataFrame:
        """
        Load and preprocess raw OSM network data.

        - Extracts network edges using the specified network type
        - Converts geometries to target CRS
        - Explodes MultiLineStrings into individual LineStrings
        - Normalizes geometries to single LineString per edge

        Args:
            osm (OSM): Pyrosm OSM object with bounding box and data source.

        Returns:
            GeoDataFrame: Preprocessed edge geometries in target CRS.
        """
        graph = osm.get_network(network_type=self.network_type)
        graph = graph.to_crs(self.crs)
        graph = graph.explode(index_parts=False).reset_index(drop=True)

        graph["geometry"] = graph.geometry.apply(self._to_linestring)
        return graph

    def _to_linestring(self, geom):
        """
        Normalize geometry to a single LineString.

        - If MultiLineString or GeometryCollection, returns the longest LineString
        - If LineString, returns as-is
        - Otherwise, returns convex hull

        Args:
            geom (shapely geometry): Input geometry.

        Returns:
            LineString: Normalized geometry.
        """
        if isinstance(geom, (MultiLineString, GeometryCollection)):
            lines = [g for g in geom.geoms if isinstance(g, LineString)]
            if lines:
                return max(lines, key=lambda g: g.length)
        if isinstance(geom, LineString):
            return geom
        if isinstance(geom, Point):
            return LineString([geom, geom])  # zero-length line
        return geom.convex_hull if hasattr(geom, "convex_hull") else geom

    def _load_or_create_grid(self):
        """
        Load existing spatial tile grid or generate a new one.

        - If grid file exists, loads it from disk (GeoJSON format)
        - Otherwise, creates a new grid using configured tile size and bounding box

        Returns:
            GeoDataFrame: Grid tiles with tile IDs and geometry.
        """
        grid_path = Path(self.config.grid_file_parquet)
        if not grid_path.exists():
            print("Grid file missing. Generating automatically.")
            grid = Grid(self.config).create_grid()
        else:
            grid = gpd.read_parquet(grid_path)
        return grid

    def _assign_tiles(self, edges: gpd.GeoDataFrame, grid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Split edge geometries by tile boundaries and assign tile IDs.

        - Uses buffered tile boundaries to split edges that cross tile borders
        - Performs spatial join to assign each edge segment to its corresponding tile
        - Preserves original edge attributes

        Args:
            edges (GeoDataFrame): Road network edges with geometry.
            grid (GeoDataFrame): Tile grid with tile_id and geometry.

        Returns:
            GeoDataFrame: Split edge segments with assigned tile_id.
        """
        tile_boundaries = grid.boundary.buffer(0.001).union_all()

        split_rows = []

        for _, row in edges.iterrows():
            geom = row.geometry

            try:
                result = split(geom, tile_boundaries)
            except (ValueError, TopologicalError):
                result = [geom]

            if isinstance(result, GeometryCollection):
                parts = list(result.geoms)
            else:
                parts = list(result)

            for part in parts:
                new_row = row.copy()
                new_row["geometry"] = part
                split_rows.append(new_row)

        split_gdf = gpd.GeoDataFrame(split_rows, crs=edges.crs)

        grid = grid[["tile_id", "geometry"]]
        split_gdf = gpd.sjoin(
            split_gdf.set_geometry("geometry"),
            grid.set_geometry("geometry"),
            how="inner",
            predicate="intersects"
        ).drop(columns="index_right", errors="ignore")

        return split_gdf

    def _clean_geometry(self, gdf):
        """
        Filter and finalize edge geometries.

        - Removes edges with restricted access (e.g. private roads)
        - Normalizes geometries to LineStrings
        - Computes edge lengths in meters
        - Assigns unique edge IDs
        - Retains selected attributes (e.g. highway)

        Args:
            gdf (GeoDataFrame): Edge data after tile assignment.

        Returns:
            GeoDataFrame: Cleaned edge data with geometry, length, and attributes.

        Raises:
            ValueError: If resulting geometries are empty or invalid.
        """

        gdf = gdf.copy()

        allowed_access = [None, "yes", "permissive"]
        if "access" in gdf.columns:
            gdf = gdf[gdf["access"].isin(allowed_access)]

        mask = ~gdf.geometry.apply(lambda g: isinstance(g, LineString))
        if mask.any():
            gdf.loc[mask, "geometry"] = gdf.loc[mask,
                                                "geometry"].apply(self._to_linestring)

        gdf["length_m"] = gdf.geometry.length.round(2)
        gdf["edge_id"] = range(len(gdf))

        selected_attributes = [col for col in [
            "highway"] if col in gdf.columns]
        columns = ["edge_id", "tile_id", "geometry",
                   "length_m"] + selected_attributes

        if gdf.empty or gdf.geometry.is_empty.any():
            raise ValueError(
                "Geometry cleaning resulted in empty or invalid edges.")

        return gdf[columns]

    def _save_graph(self, graph):
        """
        Save the processed road network to a Parquet file.

        Args:
            graph (GeoDataFrame): Cleaned edge data.

        Raises:
            ValueError: If the graph contains empty geometries.
        """
        if graph.empty or graph.geometry.is_empty.any():
            raise ValueError("Cannot save: graph contains empty geometries.")
        graph.to_parquet(self.output_path)
        print(f"Saved {len(graph)} edges to {self.output_path}")
