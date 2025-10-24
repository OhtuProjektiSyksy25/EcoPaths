"""
Download and process OpenStreetMap data into a cleaned road network.
"""

import warnings
import geopandas as gpd
from pyrosm import OSM
from shapely.geometry import Point, LineString, MultiLineString, GeometryCollection
from shapely.ops import split
from shapely.errors import TopologicalError
from src.config.columns import BASE_COLUMNS, EXTRA_COLUMNS
from src.database.db_client import DatabaseClient
from .osm_downloader import OSMDownloader


class OSMPreprocessor:
    """
    Handles downloading and processing OpenStreetMap (OSM) PBF files 
    into a cleaned GeoDataFrame of road network edges.

    This class supports area-specific configurations, bounding box filtering, 
    and network type selection.
    It does not handle data persistence; saving
    to a database should be done using DatabaseClient.
    """

    def __init__(self, area: str = "berlin", network_type: str = "walking"):
        """
        Initialize the OSMPreprocessor with area-specific settings.

        Args:
            area (str): Name of the area defined in AREA_SETTINGS (e.g. 'berlin').
            network_type (str): Type of network to extract (e.g. 'walking', 'cycling').

        Sets up paths, bounding box, CRS, and download URL for the selected area.
        """
        self.area_name = area.lower()
        self.network_type = network_type
        self.downloader = OSMDownloader(self.area_name)
        self.area_config = self.downloader.area_config
        self.crs = self.area_config.crs

    def extract_edges(self):
        """
        Extract, process, and save road network edges for the configured area.

        Workflow:
        - Load OSM data via OSMDownloader
        - Prepare graph and geometries
        - Load spatial tile grid from database
        - Assign tile IDs to edges
        - Clean and filter geometries

        Returns:
            GeoDataFrame: Processed edges with tile assignments and relevant attributes,
                        ready to be saved to a database.
        """
        warnings.filterwarnings(
            "ignore", category=FutureWarning, module="pyrosm")

        osm = self.downloader.get_osm_instance()
        edges_gdf = self._prepare_graph(osm)
        grid = self._load_grid()
        print("Preparing edges...")
        edges_gdf = self._assign_tiles(edges_gdf, grid)
        edges_gdf = self._clean_geometry(edges_gdf)

        return edges_gdf

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
        if graph is None or graph.empty:
            raise ValueError(
                f"No '{self.network_type}' network edges found for area '{self.area_name}'. ")
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

    def _load_grid(self) -> gpd.GeoDataFrame:
        """
        Load spatial tile grid for the current area from the database.

        Uses the DatabaseClient to query the grid table corresponding to the configured area.
        This replaces file-based grid loading and ensures consistency with database-stored tiles.

        Returns:
            GeoDataFrame: Grid tiles with tile_id and geometry for the current area.
        """
        db = DatabaseClient()
        return db.load_grid(self.area_name)

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
        - Retains base and network-specific extra attributes

        Args:
            gdf (GeoDataFrame): Edge data after tile assignment.

        Returns:
            GeoDataFrame: Cleaned edge data with selected columns.

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

        columns = BASE_COLUMNS + EXTRA_COLUMNS.get(self.network_type, [])

        for col in columns:
            if col not in gdf.columns:
                gdf[col] = None

        if gdf.empty or gdf.geometry.is_empty.any():
            raise ValueError(
                "Geometry cleaning resulted in empty or invalid edges.")

        return gdf[columns]
