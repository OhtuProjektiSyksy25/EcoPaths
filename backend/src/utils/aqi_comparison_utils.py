"""
Util for calculating AQI difference between different route modes.
"""
from collections import defaultdict

def calculate_aqi_difference(summaries: dict) -> dict:
    """
    Calculate differences in AQI between different route types.

    Args:
        summaries (dict): Route summaries containing AQI averages for each mode.

    Returns:
        dict: Differences in AQI between route modes.
    """

    modes = ["fastest", "best_aq", "balanced"]
    comparisons = defaultdict(dict)

    baseline_mode = "fastest"
    baseline_aqi = summaries["fastest"]["aq_average"]

    for mode in modes:
        if mode == baseline_mode:
            continue

        mode_aqi = summaries[mode]["aq_average"]

        if mode_aqi is None or baseline_aqi is None or baseline_aqi == 0:
            aqi_diff = None
            percentage_diff = None
        else:
            aqi_diff = baseline_aqi - mode_aqi
            percentage_diff = round((aqi_diff / baseline_aqi * 100), 2)

        comparison_text = format_comparison_text(percentage_diff)

        comparisons[mode][baseline_mode] = {
            "aqi_difference": aqi_diff,
            "percentage_difference": percentage_diff,
            "comparison_text": comparison_text
        }

    return comparisons

def format_comparison_text(percentage_diff: float | None) -> str:
    """
    Format the AQI into a string.

    Args:
        percentage_diff (float | None): Percentage difference in AQI or None if unavailable.

    Returns:
        str: Formatted comparison text.
    """

    if percentage_diff is None:
        return "Exposure comparison with Fastest Route not available"

    if percentage_diff > 0:
        return f"{abs(percentage_diff)}% less exposure than Fastest Route"

    return "Exposure level is the same as Fastest Route"
