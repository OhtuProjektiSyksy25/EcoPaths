# db/db_manager.py

"""
DatabaseManager module for handling PostGIS read/write operations.
"""


import geopandas as gpd
from sqlalchemy import create_engine
from config.settings import POSTGIS_URL


class DatabaseManager:
    """
    Handles reading and writing GeoDataFrames to a PostGIS database.
    """

    def __init__(self, table_name: str):
        self.engine = create_engine(POSTGIS_URL)
        self.table_name = table_name

    def save(self, gdf: gpd.GeoDataFrame, if_exists: str = "replace"):
        """
        Save GeoDataFrame to PostGIS.

        Args:
            gdf (GeoDataFrame): Data to save.
            if_exists (str): What to do if table exists ("replace", "append", "fail").
        """
        gdf.to_postgis(self.table_name, con=self.engine,
                       if_exists=if_exists, index=False)

    def load(self) -> gpd.GeoDataFrame:
        """
        Load GeoDataFrame from PostGIS.

        Returns:
            GeoDataFrame: Loaded data.
        """
        return gpd.read_postgis(
            f"SELECT * FROM {self.table_name}",
            con=self.engine,
            geom_col="geometry"
        )
