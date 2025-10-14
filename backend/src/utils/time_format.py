"""
Utility module for formatting estimated walking time based on distance in meters.
Assumes average walking speed of 1.4 meters per second.
"""
import pandas as pd


def format_walk_time(length_m: float) -> str:
    """
    Format estimated walking time from distance in meters.

    Args:
        length_m (float): Distance in meters

    Returns:
        str: Formatted time estimate (e.g., "1h 5 min" or "15 min 30 s")
    """
    if length_m is None or pd.isna(length_m):
        return "unknown"
    avg_speed_mps = 1.4
    seconds = length_m / avg_speed_mps

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes} min"
    return f"{minutes} min {remaining_seconds} s"
