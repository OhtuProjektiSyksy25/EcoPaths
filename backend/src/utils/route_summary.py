"""
Utilities for summarizing route data,
including total distance, average air quality, and estimated walking time.
"""

import geopandas as gpd
import pandas as pd


def format_walk_time(length_m: float) -> str:
    """
    Formats estimated walking time based on distance in meters.
    Assumes an average walking speed of 1.4 meters per second.

    Args:
        length_m (float): Distance in meters.

    Returns:
        str: Formatted time estimate (e.g., "1h 5 min" or "15 min").
    """
    if length_m is None or pd.isna(length_m):
        return "unknown"

    avg_speed_mps = 1.4
    seconds = length_m / avg_speed_mps

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)

    if remaining_seconds > 30:
        minutes += 1

    if hours > 0:
        return f"{hours}h {minutes} min"
    return f"{minutes} min"


def calculate_total_length(route: gpd.GeoDataFrame) -> float:
    """
    Calculates the total route length in meters.

    Args:
        route (GeoDataFrame): Route represented as edge-level geometry.

    Returns:
        float: Total length in meters.
    """
    return float(route["length_m"].sum())


def calculate_aq_average(route: gpd.GeoDataFrame) -> float | None:
    """
    Calculates the average air quality value along the route.

    Args:
        route (GeoDataFrame): Route represented as edge-level geometry.

    Returns:
        float | None: Average AQI, or None if no values are available.
    """
    valid = route.dropna(subset=["aqi", "length_m"])
    if valid.empty or valid["length_m"].sum() == 0:
        return None

    weighted_sum = (valid["aqi"] * valid["length_m"]).sum()
    total_length = valid["length_m"].sum()
    return weighted_sum / total_length


def summarize_route(route: gpd.GeoDataFrame) -> dict:
    """
    Summarizes a route by calculating total length, average air quality, and estimated walking time.

    Args:
        route (GeoDataFrame): Route represented as edge-level geometry.

    Returns:
        dict: Summary containing 'total_length', 'aq_average', and 'time_estimate'.
    """
    length_m = calculate_total_length(route)
    aq_avg = calculate_aq_average(route)

    return {
        "total_length": round(length_m / 1000, 2),
        "time_estimate": format_walk_time(length_m),
        "aq_average": round(aq_avg, 0) if aq_avg is not None else None,
    }
