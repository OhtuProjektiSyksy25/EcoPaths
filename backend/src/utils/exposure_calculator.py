"""
Utility function for computing instantaneous and cumulative pollution exposure
(PM2.5, PM10) along a GeoDataFrame route simplified: only 'walk' mode.
"""

import geopandas as gpd
from logger.logger import log
from utils.route_summary import SPEEDS

# ventilation rate for walking (liters per minute)
VENTILATION_LPM_WALK = 8.0  # L/min


def compute_exposure(route: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculates instantaneous and cumulative exposure to PM2.5 and PM10 along the route
    for walking mode.
    """
    gdf = route.copy()

    # Ensure numeric
    gdf["pm2_5"] = gdf["pm2_5"].astype(float).fillna(0.0)
    gdf["pm10"] = gdf["pm10"].astype(float).fillna(0.0)
    gdf["length_m"] = gdf.get("length_m", 0.0).astype(float).fillna(0.0)

    gdf["distance_cumulative"] = gdf["length_m"].cumsum()
    gdf["distance_cumulative_km"] = gdf["distance_cumulative"] / 1000.0

    # Time per segment
    walk_speed = SPEEDS.get("walk", 1.0)
    gdf["time_s"] = gdf["length_m"] / max(walk_speed, 0.1)

    # Ventilation in m³/s
    vent_m3s = (VENTILATION_LPM_WALK / 1000.0) / 60.0

    # Instant inhaled dose (µg)
    gdf["pm25_inhaled"] = gdf["pm2_5"] * vent_m3s * gdf["time_s"]
    gdf["pm10_inhaled"] = gdf["pm10"] * vent_m3s * gdf["time_s"]

    # Cumulative dose
    gdf["pm25_inhaled_cumulative"] = gdf["pm25_inhaled"].cumsum()
    gdf["pm10_inhaled_cumulative"] = gdf["pm10_inhaled"].cumsum()

    log.debug(f"DEBUG compute_exposure columns: {gdf.columns.tolist()}")
    log.debug(
        gdf[
            [
                "length_m",
                "distance_cumulative_km",
                "time_s",
                "pm2_5",
                "pm10",
                "pm25_inhaled",
                "pm10_inhaled",
                "pm25_inhaled_cumulative",
                "pm10_inhaled_cumulative",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    return gdf
