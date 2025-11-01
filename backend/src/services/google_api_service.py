"""
Google API Service for AQ data retrieval.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import geopandas as gpd
import numpy as np

from config.settings import get_settings
from database.db_client import DatabaseClient


class GoogleAPIService:
    """Service for fetching air quality data from Google API."""

    def __init__(self):
        settings = get_settings("testarea")  # area can be anything
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file.")
        self.api_key = settings.google_api_key
        self.endpoint = "https://airquality.googleapis.com/v1/currentConditions:lookup"

    def _fetch_single_tile(self, lat: float, lon: float) -> dict:
        """Fetch AQI for a single coordinate pair; other pollutants as placeholders."""
        payload = {"location": {"latitude": lat, "longitude": lon}}
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            indexes = data.get("indexes", [])
            aqi = indexes[0].get("aqi") if indexes else None
            return {
                "aqi": aqi,
                "pm2_5": None,  # placeholder
                "no2": None     # placeholder
            }
        except requests.RequestException:
            return {"aqi": None, "pm2_5": None, "no2": None}

    def get_aq_data_for_tiles(self, tile_ids: list[str], area: str) -> gpd.GeoDataFrame:
        """Fetch air quality data for given tile IDs using parallel requests."""
        area_config = get_settings(area).area
        db = DatabaseClient()
        grid_gdf = db.load_grid(area)

        # Filter to the requested tiles
        tiles = grid_gdf.loc[
            grid_gdf["tile_id"].isin(tile_ids),
            ["tile_id", "geometry", "center_lat", "center_lon"]
        ].copy()

        # Return empty GeoDataFrame if no tiles found
        if tiles.empty:
            return gpd.GeoDataFrame(
                columns=["tile_id", "raw_aqi", "pm2_5", "no2", "geometry"],
                crs=area_config.crs
            )

        print(f"Fetching AQ data for {len(tiles)} tiles...")

        # Run parallel API calls for each tile
        results = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(
                    self._fetch_single_tile, row.center_lat, row.center_lon
                ): row.tile_id
                for _, row in tiles.iterrows()
            }
            for future in as_completed(futures):
                tile_id = futures[future]
                results[tile_id] = future.result()

        # Merge results into GeoDataFrame
        tiles["raw_aqi"] = tiles["tile_id"].map(
            lambda tid: results[tid]["aqi"])
        tiles["pm2_5"] = np.nan  # placeholder
        tiles["no2"] = np.nan    # placeholder

        # Return result with correct CRS
        return tiles[["tile_id", "raw_aqi", "pm2_5", "no2", "geometry"]].set_crs(area_config.crs)
