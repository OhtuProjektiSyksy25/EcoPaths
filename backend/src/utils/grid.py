"""
Grid module for creating and managing spatial tile grids.

This module provides a Grid class that creates a regular grid of tiles
over a geographic area, using GeoPandas for efficient spatial operations.
"""
import pyproj
import geopandas as gpd
from shapely.geometry import box, Point
from src.config.settings import AreaConfig


class Grid:
    """
    Grid class for creating and querying a spatial tile grid.
    """
    def __init__(self, area_config: AreaConfig):
        """
        Initialize grid for an area.

        Args:
            area_config (AreaConfig): Configuration for the area.
        """
        self.area_config = area_config

        self.origin_lon = area_config.bbox[0]
        self.origin_lat = area_config.bbox[1]
        self.max_lon = area_config.bbox[2]
        self.max_lat = area_config.bbox[3]

        self.tile_size_m = area_config.tile_size_m

        # setup coordinate transformation
        # WGS84 (lat/lon) <-> Local CRS (meters)
        self.wgs84 = pyproj.CRS("EPSG:4326")
        self.local_crs = pyproj.CRS(area_config.crs)

        # transformers
        self.to_meters = pyproj.Transformer.from_crs(
            self.wgs84,
            self.local_crs,
            always_xy=True
        )
        self.to_latlon = pyproj.Transformer.from_crs(
            self.local_crs,
            self.wgs84,
            always_xy=True
        )

        self.origin_x, self.origin_y = self.to_meters.transform(
            self.origin_lon,
            self.origin_lat
        )

    def create_grid(self) -> gpd.GeoDataFrame:
        """Create a grid of tiles for the given area.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing the grid tiles.
        """

        # Return from parquet file if exists
        if self.area_config.grid_file.exists():
            return gpd.read_parquet(self.area_config.grid_file)

        # Otherwise, create new grid
        print(f"Creating new grid for area '{self.area_config.area}'...")

        # Convert max bounds to meters
        max_x, max_y = self.to_meters.transform(self.max_lon, self.max_lat)

        # Create grid cells
        grid_cells = []
        x = self.origin_x
        col = 0

        while x <= max_x:
            y = self.origin_y
            row = 0

            while y <= max_y:
                # Create box polygon (500m × 500m in Web Mercator)
                grid_cells.append({
                    "tile_id": f"r{row}_c{col}",
                    "row": row,
                    "col": col,
                    "geometry": box(x, y, x + self.tile_size_m, y + self.tile_size_m)
                })
                y += self.tile_size_m
                row += 1

            x += self.tile_size_m
            col += 1

        # Convert to GeoDataFrame
        grid_gdf = gpd.GeoDataFrame(grid_cells, crs=self.area_config.crs)

        # Get center points for tiles
        grid_gdf['centroid'] = grid_gdf.geometry.centroid

        # Convert center points to lat/lon for API calls
        grid_gdf['center_lon'], grid_gdf['center_lat'] = self.to_latlon.transform(
            grid_gdf['centroid'].x.values,
            grid_gdf['centroid'].y.values
        )

        # Save to parquet
        grid_gdf.to_parquet(self.area_config.grid_file)
        print(f"Grid saved to {self.area_config.grid_file}")

        return grid_gdf

    def get_tile_id(self, lon: float, lat: float) -> str:
        """
        Get tile ID for given lon/lat.

        Args:
            lon (float): longitude.
            lat (float): latitude.
        """

        # Creates grid
        grid_gdf = self.create_grid()

        # Convert coordinates to meters: same as grid
        x, y = self.to_meters.transform(lon, lat)
        point = Point(x, y)

        # Find tile containing the point
        found = grid_gdf[grid_gdf.intersects(point)]

        if found.empty:
            raise ValueError(f"Point ({lon}, {lat}) not in grid bounds")

        return found.iloc[0]['tile_id']

    def get_tile_center(self, tile_id: str) -> tuple[float, float]:
        """
        Get center coordinates of a tile by its ID.

        Args:
            tile_id (str): Tile ID in format "r{row}_c{col}".

        Returns:
            tuple[float, float]: (lon, lat) of the tile center.
        """

        # Creates grid
        grid_gdf = self.create_grid()

        # Find tile by ID
        tile = grid_gdf[grid_gdf['tile_id'] == tile_id]
        if tile.empty:
            raise ValueError(f"Tile ID '{tile_id}' not found.")

        # Return center lon/lat for the tile
        return tile.iloc[0]['center_lon'], tile.iloc[0]['center_lat']

    def parse_tile_id(self, tile_id: str) -> tuple[int, int]:
        """
        Parse tile ID into row and column integers.

        Args:
            tile_id (str): Tile ID in format "r{row}_c{col}".

        Returns:
            tuple[int, int]: (row, col) as integers.
        """
        parts = tile_id.replace('r', '').replace('c', '').split('_')
        row, col = int(parts[0]), int(parts[1])
        return row, col

