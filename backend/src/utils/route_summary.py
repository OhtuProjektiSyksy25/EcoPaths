"""
Utilities for summarizing route data, 
including total distance, average air quality, and estimated walking time.
"""

from typing import Union
import geopandas as gpd
import pandas as pd


def format_walk_time(length_m: float) -> str:
    """
    Formats estimated walking time based on distance in meters.
    Assumes an average walking speed of 1.4 meters per second.

    Args:
        length_m (float): Distance in meters.

    Returns:
        str: Formatted time estimate (e.g., "1h 5 min" or "15 min 30 s").
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


def calculate_total_length(route: Union[gpd.GeoDataFrame, dict]) -> float:
    """
    Calculates the total route length in meters.

    Args:
        route (GeoDataFrame or FeatureCollection): Route represented as edge-level geometry.

    Returns:
        float: Total length in meters.
    """
    if isinstance(route, gpd.GeoDataFrame):
        return float(route["length_m"].sum())
    if isinstance(route, dict) and route.get("type") == "FeatureCollection":
        return sum(
            f["properties"].get("length_m", 0)
            for f in route["features"]
            if "length_m" in f["properties"]
        )
    raise ValueError("Unsupported route format")


def calculate_aq_average(route: Union[gpd.GeoDataFrame, dict]) -> float | None:
    """
    Calculates the average air quality value along the route.

    Args:
        route (GeoDataFrame or FeatureCollection): Route represented as edge-level geometry.

    Returns:
        float | None: Average AQI, or None if no values are available.
    """
    if isinstance(route, gpd.GeoDataFrame):
        # collect (aqi, length_m) tuples
        aqi_both = list(
            zip(
                route["aqi"].dropna().tolist(),
                route["length_m"].dropna().tolist(
                ) if "length_m" in route else []
            )
        )

    elif isinstance(route, dict) and route.get("type") == "FeatureCollection":
        aqi_both = [
            (f["properties"]["aqi"], f["properties"]["length_m"])
            for f in route["features"]
            if (
                "aqi" in f["properties"]
                and "length_m" in f["properties"]
                and f["properties"]["aqi"] is not None
                and f["properties"]["length_m"] is not None
            )
        ]

    else:
        raise ValueError("Unsupported route format")

    total_length = sum(length for _, length in aqi_both)
    if total_length == 0:
        return None

    weighted_avg = sum(aqi * length for aqi, length in aqi_both) / total_length
    return weighted_avg


def summarize_route(route: Union[gpd.GeoDataFrame, dict]) -> dict:
    """
    Summarizes a route by calculating total length, average air quality, and estimated walking time.

    Args:
        route (GeoDataFrame or FeatureCollection): Route represented as edge-level geometry.

    Returns:
        dict: Summary containing 'total_length', 'aq_average', and 'time_estimate'.
    """
    length_m = calculate_total_length(route)
    total_length = round(length_m/1000, 2)
    aq_avg = round(calculate_aq_average(route), 0)
    time_estimate = format_walk_time(length_m)
    return {
        "total_length": total_length,
        "time_estimate": time_estimate,
        "aq_average": aq_avg
    }
