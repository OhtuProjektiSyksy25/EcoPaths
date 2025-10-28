"""
Database client for managing spatial data operations.

Provides methods for connecting to the database, creating tables,
and saving GeoDataFrames to PostGIS using SQLAlchemy and GeoPandas.
"""

import geopandas as gpd
from sqlalchemy import inspect, text
from database.db_connection import get_engine, get_session
from database.db_models import create_edge_class, create_grid_class


class DatabaseClient:
    """Simple client class for database operations."""

    def __init__(self):
        """Initialize database engine and session factory."""
        self.engine = get_engine()
        self.session_local = get_session()

    def get_session(self):
        """
        Create and return a new SQLAlchemy session.

        Returns:
            sqlalchemy.orm.Session: A new session connected to the database.
        """
        return self.session_local()

    def create_tables_for_area(self, area_name: str, network_type: str):
        """
        Create edge and grid tables for a specific area and network type.

        Args:
            area_name (str): Name of the area (e.g., "berlin").
            network_type (str): Type of network (e.g., "walking", "cycling", "driving").
        """
        inspector = inspect(self.engine)
        Edge = create_edge_class(area_name, network_type)
        Grid = create_grid_class(area_name)

        edge_table = Edge.__table__.name          # pylint: disable=no-member
        grid_table = Grid.__table__.name

        edge_exists_before = inspector.has_table(edge_table)
        grid_exists_before = inspector.has_table(grid_table)

        Edge.__table__.create(                      # pylint: disable=no-member
            bind=self.engine, checkfirst=True)
        Grid.__table__.create(
            bind=self.engine, checkfirst=True)

        edge_exists_after = inspector.has_table(edge_table)
        grid_exists_after = inspector.has_table(grid_table)

        print(
            f"Grid and edge tables for '{area_name}' ({network_type}) checked:")

        grid_status = (
            "created"
            if not edge_exists_before and grid_exists_after
            else "already exists"
        )
        print(f"- '{grid_table}': {grid_status}")

        edge_status = (
            "created"
            if not grid_exists_before and edge_exists_after
            else "already exists"
        )
        print(f"- '{edge_table}': {edge_status}")

    def save_edges(self, gdf: gpd.GeoDataFrame, area: str, network_type: str, if_exists="fail"):
        """
        Save an edge GeoDataFrame to a PostGIS table.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing edge geometries.
            area (str): Area name, used in the table name.
            if_exists (str, optional): How to behave if the table already exists.
                Defaults to "fail". Other valid values: "replace", "append".

        Raises:
            ValueError: If the GeoDataFrame is empty.
        """
        if gdf.empty:
            raise ValueError("Cannot save empty GeoDataFrame.")
        table_name = f"edges_{area.lower()}_{network_type.lower()}"
        gdf.to_postgis(name=table_name, con=self.engine,
                       if_exists=if_exists, index=False)
        print(f"Saved {len(gdf)} edges to table '{table_name}'")

    def save_grid(self, gdf: gpd.GeoDataFrame, area: str, if_exists="fail"):
        """
        Save a grid GeoDataFrame to a PostGIS table.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing grid polygons.
            area (str): Area name, used in the table name.
            if_exists (str, optional): How to behave if the table already exists.
                Defaults to "fail". Other valid values: "replace", "append".

        Raises:
            ValueError: If the GeoDataFrame is empty.
        """
        if gdf.empty:
            raise ValueError("Cannot save empty grid GeoDataFrame.")
        table_name = f"grid_{area.lower()}"
        gdf.to_postgis(name=table_name, con=self.engine,
                       if_exists=if_exists, index=False)
        print(f"Saved {len(gdf)} tiles to table '{table_name}'")

    def load_edges_for_tiles(
        self, area: str,
        network_type: str = "walking",
        tile_ids: list[int] = None
    ) -> gpd.GeoDataFrame:
        """
        Load edges for a specific area/network type and optional list of tile IDs.

        Args:
            area (str): Area name (e.g., 'berlin').
            network_type (str): Network type ('walking', 'cycling', 'driving').
            tile_ids (list[int], optional): If provided, only edges with these tile_ids are loaded.

        Returns:
            GeoDataFrame: Edges from PostGIS matching the area, network type, and tile IDs.
        Raises:
            RuntimeError: If the edge table does not exist or query fails.
        """
        table_name = f"edges_{area}_{network_type}"
        query = f"SELECT * FROM {table_name}"

        if tile_ids:
            placeholders = ", ".join([f"'{t}'" for t in tile_ids])
            query += f" WHERE tile_id IN ({placeholders})"

        print(f"Executing query: {query}")
        try:
            return gpd.read_postgis(query, con=self.engine, geom_col="geometry")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load edges for area '{area}' and network '{network_type}': {e}") from e

    def load_grid(self, area: str) -> gpd.GeoDataFrame:
        """
        Load grid tiles from PostGIS for a given area.

        Args:
            area (str): Area name (e.g., 'berlin').

        Returns:
            GeoDataFrame: Grid tiles with tile_id and geometry.

        Raises:
            RuntimeError: If grid table does not exist or query fails.
        """
        table_name = f"grid_{area.lower()}"
        query = f"SELECT * FROM {table_name}"
        print(f"Loading grid from table: {table_name}")

        try:
            return gpd.read_postgis(query, con=self.engine, geom_col="geometry")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load grid for area '{area}': {e}") from e

    def get_tile_ids_by_buffer(self, area: str, buffer_geom, grid_table_prefix="grid") -> list[int]:
        """
        Return tile_ids from grid table that intersect with the given buffer geometry.

        Args:
            area (str): Area name (e.g., 'berlin').
            buffer_geom (shapely.geometry.Polygon): Buffer geometry in correct CRS.
            grid_table_prefix (str): Optional prefix for grid table name.

        Returns:
            list[int]: List of tile_ids intersecting the buffer.
        """
        table_name = f"{grid_table_prefix}_{area.lower()}"
        sql = f"SELECT tile_id, geometry FROM {table_name}"
        grid_gdf = gpd.read_postgis(sql, con=self.engine, geom_col="geometry")

        buffer_geom = gpd.GeoSeries([buffer_geom], crs=grid_gdf.crs).iloc[0]

        intersecting = grid_gdf[grid_gdf.intersects(buffer_geom)]
        return intersecting["tile_id"].unique().tolist()

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name (str): Name of the table to check.

        Returns:
            bool: True if table exists, False otherwise.
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = :table_name
                )
            """), {"table_name": table_name})
            return result.scalar()
