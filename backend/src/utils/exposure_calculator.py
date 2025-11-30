"""
Utility function for computing instantaneous and cumulative pollution exposure
(PM2.5, PM10) along a GeoDataFrame route.
"""
import geopandas as gpd


def compute_exposure(route: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Adds cumulative PM2.5, PM10 and distance exposures to each edge in a route.

    Returns the *same* GeoDataFrame with new columns:
        - pm25_exposure
        - pm10_exposure
        - pm25_cumulative
        - pm10_cumulative
        - distance_cumulative
    """

    df = route.copy()

    # Instant exposure per edge (µg/m³ * meters)
    df["pm25_exposure"] = df["pm2_5"] * df["length_m"]
    df["pm10_exposure"] = df["pm10"] * df["length_m"]

    # Cumulative progress
    df["distance_cumulative"] = df["length_m"].cumsum()
    df["pm25_cumulative"] = df["pm25_exposure"].cumsum()
    df["pm10_cumulative"] = df["pm10_exposure"].cumsum()

    return df
