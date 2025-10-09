
"""
DatabaseManager module for handling PostGIS read/write operations.
"""
import geopandas as gpd
from sqlalchemy import create_engine, inspect
from config.settings import POSTGIS_URL


class DatabaseManager:
    """
    Handles reading and writing GeoDataFrames to a PostGIS database.
    """

    def __init__(self, table_name: str, schema: str = None):
        """
        Initialize DatabaseManager.

        Args:
            table_name (str): Name of the table to read/write
            schema (str, optional): Optional database schema
        """
        self.engine = create_engine(POSTGIS_URL)
        self.table_name = table_name
        self.schema = schema

    def save(self, gdf: gpd.GeoDataFrame, if_exists: str = "replace"):
        """
        Save GeoDataFrame to PostGIS.

        Args:
            gdf (GeoDataFrame): Data to save.
            if_exists (str): "replace", "append", or "fail"
        """
        gdf.to_postgis(
            self.table_name,
            con=self.engine,
            schema=self.schema,
            if_exists=if_exists,
            index=False
        )

    def load(self) -> gpd.GeoDataFrame:
        """
        Load GeoDataFrame from PostGIS.

        Returns:
            GeoDataFrame: Loaded data.
        """
        full_table_name = f"{self.schema}.{self.table_name}" if self.schema else self.table_name
        return gpd.read_postgis(
            f"SELECT * FROM {full_table_name}",
            con=self.engine,
            geom_col="geometry"
        )

    def exists(self) -> bool:
        """
        Check if the table exists in the database.

        Returns:
            bool: True if table exists, False otherwise
        """
        inspector = inspect(self.engine)
        return inspector.has_table(self.table_name, schema=self.schema)
