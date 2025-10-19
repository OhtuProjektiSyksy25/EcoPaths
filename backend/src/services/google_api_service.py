"""
Google API Service for AQ data retrieval.
"""
import os
import requests
import geopandas as gpd
from dotenv import load_dotenv
from utils.grid import Grid
from config.settings import AreaConfig


load_dotenv()


class GoogleAPIService:
    """
    Service for interacting with the Google API.
    """
    def __init__(self):
        """
        Initializes the GoogleAPIService with the API key.
        """
        self.api_key = os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file.")

        # Endpoint for current conditions
        self.endpoint = "https://airquality.googleapis.com/v1/currentConditions:lookup"



    def get_current_conditions(
        self,
        latitude: float,
        longitude: float

    ):
        """
        Fetch current air quality conditions for given coordinates.
        """
        payload = {
            "location": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"Error fetching data from Google API: {e}")
            return None




    def get_aq_data_for_tiles(self, tile_ids: list[str], area: str) -> gpd.GeoDataFrame:
        """
        Fetch air quality data for given tile IDs.
        """
        # load area config
        area_config = AreaConfig(area)
        # create grid instance
        grid = Grid(area_config)

        # will load grid from file if it exists
        grid_gdf = grid.create_grid()

        # filter to requested tiles and create a copy
        tiles = grid_gdf[grid_gdf["tile_id"].isin(tile_ids)].copy()

        # check if any tiles found
        if tiles.empty:
            print(f"No tiles found for IDs: {tile_ids}.")
            return gpd.GeoDataFrame(
                columns=["tile_id", "aqi", "geometry"],
                crs=area_config.crs
            )

        # fetch AQ data for tiles
        # loops through gdf rows
        for idx, tile in tiles.iterrows():
            lat = tile["center_lat"]
            lon = tile["center_lon"]

            # call method for Google API request
            aq_response = self.get_current_conditions(lat, lon)

            # parse AQI from response
            if aq_response:
                indexes = aq_response.get("indexes", [])
                aqi = indexes[0].get("aqi") if indexes else None
                tiles.at[idx, "aqi"] = aqi
            else:
                tiles.at[idx, "aqi"] = None

        # return gdf with aqi data
        result = tiles[["tile_id", "aqi", "geometry"]].copy()
        return result
