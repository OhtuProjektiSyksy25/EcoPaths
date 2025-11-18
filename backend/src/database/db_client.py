"""
Database client for managing spatial data operations.

Provides methods for connecting to the database, creating tables,
and saving GeoDataFrames to PostGIS using SQLAlchemy and GeoPandas.
"""

import geopandas as gpd
from sqlalchemy import text
from src.logging.logger import log
from config.columns import BASE_COLUMNS
from database.db_connection import get_engine, get_session, Base
from database.db_models import (
    create_edge_class,
    create_grid_class,
    create_node_class)


class DatabaseClient:
    """Client class for database operations with PostGIS."""

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

    def execute(self, sql: str):
        """
        Execute a raw SQL statement within a transactional context.

        Args:
            sql (str): A raw SQL string to be executed.

        Returns:
            CursorResult: The result of the executed SQL statement.
        """
        with self.engine.begin() as conn:
            return conn.execute(text(sql))

    def create_tables_for_area(self, area_name: str, network_type: str, base=None):
        """
        Ensure edge, grid, and node tables exist for a specific area and network type.

        Args:
            area_name (str): Name of the area (e.g., "berlin").
            network_type (str): Type of network (e.g., "walking", "cycling", "driving").
        """
        base = base or Base

        table_classes = [
            create_edge_class(area_name, network_type, base=base),
            create_grid_class(area_name, base=base),
            create_node_class(area_name, network_type, base=base),
        ]

        for table_class in table_classes:
            table_class.__table__.create(           # pylint: disable=no-member
                bind=self.engine, checkfirst=True)  # pylint: disable=no-member

        self._create_indexes(area_name, network_type)

        log.debug(
            f"Database tables ensured for area '{area_name}' ({network_type})",
            area=area_name, network_type=network_type)

    def _create_indexes(self, area: str, network_type: str):
        """
        Create spatial and attribute indexes for edge, grid, and node tables of 
        a specific area and network type.

        This method ensures that commonly queried columns in the edges, 
        grid, and nodes tables have appropriate indexes to improve query performance. 
        It creates B-tree indexes for identifier and foreign key columns, 
        and GIST indexes for geometry columns.

        Args:
            area (str): Name of the area (e.g., "berlin", "testarea").
            network_type (str): Type of network (e.g., "walking", "cycling", "driving").
        """

        with self.engine.begin() as conn:
            # EDGE
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_edge_id
                ON edges_{area}_{network_type} (edge_id);
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_tile_id
                ON edges_{area}_{network_type} (tile_id);
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_geometry
                ON edges_{area}_{network_type} USING GIST (geometry);
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_from_node
                ON edges_{area}_{network_type} (from_node);
            """))

            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_to_node
                ON edges_{area}_{network_type} (to_node);
            """))

            # GRID
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_grid_{area}_tile_id
                ON grid_{area} (tile_id);
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_grid_{area}_geometry
                ON grid_{area} USING GIST (geometry);
            """))

            # NODE
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_nodes_{area}_{network_type}_node_id
                ON nodes_{area}_{network_type} (node_id);
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_nodes_{area}_{network_type}_geometry
                ON nodes_{area}_{network_type} USING GIST (geometry);
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_nodes_{area}_{network_type}_tile_id
                ON nodes_{area}_{network_type} (tile_id);
            """))

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

        # Ensure all BASE_COLUMNS exist, except edge_id which is auto-generated
        for col in BASE_COLUMNS:
            if col not in gdf.columns and col != "edge_id":
                gdf[col] = None

        table_name = f"edges_{area.lower()}_{network_type.lower()}"
        gdf.to_postgis(
            name=table_name, con=self.engine,
            if_exists=if_exists, index=False, schema="public"
        )
        log.debug(
            "Saved edges to table", table=table_name, count=len(gdf))

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
        gdf.to_postgis(
            name=table_name, con=self.engine,
            if_exists=if_exists, index=False, schema="public"
        )
        log.debug(
            "Saved edges to table", table=table_name, count=len(gdf))

    def save_nodes(self, gdf: gpd.GeoDataFrame, area: str, network_type: str, if_exists="fail"):
        """
        Save a node GeoDataFrame to a PostGIS table.

        Args:
            gdf (gpd.GeoDataFrame): GeoDataFrame containing node points.
            area (str): Area name, used in the table name.
            network_type (str): Network type ('walking', 'cycling', etc.).
            if_exists (str, optional): How to behave if the table already exists.
                Defaults to "fail". Other valid values: "replace", "append".

        Raises:
            ValueError: If the GeoDataFrame is empty.
        """
        if gdf.empty:
            raise ValueError("Cannot save empty node GeoDataFrame.")
        table_name = f"nodes_{area.lower()}_{network_type.lower()}"
        gdf.to_postgis(
            name=table_name, con=self.engine,
            if_exists=if_exists, index=False, schema="public"
        )
        log.debug(
            "Saved edges to table", table=table_name, count=len(gdf))

    def load_edges(self, area: str, network_type: str) -> gpd.GeoDataFrame:
        """
        Load all edges from the database for a given area and network type.

        Args:
            area (str): Area name (e.g., "berlin").
            network_type (str): Network type (e.g., "walking").

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing all edge data.
        """
        table_name = f"edges_{area.lower()}_{network_type.lower()}"
        query = f"SELECT * FROM {table_name}"
        log.debug(
            "Loading all edges from table", table=table_name)

        try:
            return gpd.read_postgis(query, con=self.engine, geom_col="geometry")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load edges for area '{area}' and network '{network_type}': {e}"
            ) from e

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
        log.debug(
            "Loading grid from table:", table=table_name)

        try:
            return gpd.read_postgis(query, con=self.engine, geom_col="geometry")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load grid for area '{area}': {e}") from e

    def load_nodes(self, area: str, network_type: str) -> gpd.GeoDataFrame:
        """
        Load nodes from the database for a given area and network type.

        Args:
            area (str): Area name (e.g., "berlin").
            network_type (str): Network type (e.g., "walking").

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing node data.
        """
        table_name = f"nodes_{area.lower()}_{network_type.lower()}"
        query = f"SELECT * FROM {table_name}"
        gdf = gpd.read_postgis(query, con=self.engine, geom_col="geometry")
        log.debug(
            "Loaded edges from table", table=table_name, count=len(gdf))
        return gdf

    def load_edges_for_tiles(
        self,
        area: str,
        network_type: str = "walking",
        tile_ids: list[int] = None,
        include_columns: list[str] = None
    ) -> gpd.GeoDataFrame:
        """
        Load edges for a specific area/network type and optional list of tile IDs.

        Args:
            area (str): Area name (e.g., 'berlin').
            network_type (str): Network type ('walking', 'cycling', 'driving').
            tile_ids (list[int], optional): If provided, only edges with these tile_ids are loaded.
            include_columns (list[str], optional): If provided, only these columns are selected.

        Returns:
            GeoDataFrame: Edges from PostGIS matching the area, network type, and tile IDs.
        Raises:
            RuntimeError: If the edge table does not exist or query fails.
        """
        table_name = f"edges_{area}_{network_type}"

        # Build SELECT clause
        if include_columns:
            column_clause = ", ".join(include_columns)
        else:
            column_clause = "*"

        query = f"SELECT {column_clause} FROM {table_name}"
        params = {}

        # Add WHERE clause if tile_ids are provided
        if tile_ids:
            query += " WHERE tile_id = ANY(%(tile_ids)s)"
            params["tile_ids"] = tile_ids

        log.debug(
            f"Excecuting query {query}", query=query)
        try:
            return gpd.read_postgis(query, con=self.engine, geom_col="geometry", params=params)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load edges for area '{area}' and network '{network_type}': {e}"
            ) from e

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

    def get_nodes_by_tile_ids(
        self, area: str, network_type: str, tile_ids: list[str]
    ) -> gpd.GeoDataFrame:
        """
        Fetch nodes from the database that belong to the given tile_ids.

        Args:
            area (str): Area name (e.g., 'berlin').
            network_type (str): Network type (e.g., 'walking').
            tile_ids (list[str]): List of tile identifiers as strings.

        Returns:
            GeoDataFrame: Nodes with geometry and attributes.
        """
        if not tile_ids:
            return gpd.GeoDataFrame(columns=["node_id", "geometry", "tile_id"])

        table_name = f"nodes_{area.lower()}_{network_type.lower()}"
        query = f"""
            SELECT * FROM {table_name}
            WHERE tile_id = ANY(%(tile_ids)s)
        """
        params = {"tile_ids": tile_ids}

        try:
            return gpd.read_postgis(
                query,
                con=self.engine,
                geom_col="geometry",
                params=params
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load nodes for area '{area}', "
                f"network '{network_type}', tile_ids {tile_ids}: {e}"
            ) from e

    def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """
        Check whether a specific table exists in the given database schema.
        Args:
            table_name (str): Name of the table to check.
            schema (str, optional): Name of the schema. Defaults to "public".

        Returns:
            bool: True if the table exists, False otherwise.
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = :schema AND table_name = :table_name
                )
            """), {"schema": schema, "table_name": table_name})
            return result.scalar()

    def drop_table(self, table_name: str, schema: str = "public"):
        """
        Drop a table from the database if it exists.

        Args:
            table_name (str): Name of the table to drop.
            schema (str, optional): Name of the schema. Defaults to "public".
        """
        with self.engine.begin() as conn:
            full_name = f"{schema}.{table_name}"
            conn.execute(text(f"DROP TABLE IF EXISTS {full_name} CASCADE;"))
            log.debug(
                "Dropped table", table=full_name)
