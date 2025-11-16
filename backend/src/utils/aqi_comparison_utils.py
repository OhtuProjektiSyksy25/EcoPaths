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

    for mode in modes:
        mode_aqi = summaries[mode]["aq_average"]

        for compared_mode in modes:
            if mode == compared_mode:
                continue

            compared_mode_aqi = summaries[compared_mode]["aq_average"]

            if mode_aqi is None or compared_mode_aqi is None or compared_mode_aqi == 0:
                aqi_diff = None
                percentage_diff = None
            else:
                aqi_diff = compared_mode_aqi - mode_aqi
                percentage_diff = round((aqi_diff / compared_mode_aqi * 100), 2)

            comparison_text = format_comparison_text(percentage_diff, compared_mode)

            comparisons[mode][compared_mode] = {
                "aqi_difference": aqi_diff,
                "percentage_difference": percentage_diff,
                "comparison_text": comparison_text
            }
    
    return comparisons

def format_comparison_text(percentage_diff: float | None, compared_mode: str) -> str:
    """
    Format the AQI into a string.

    Args:
        percentage_diff (float | None): Percentage difference in AQI or None if unavailable.
        compared_mode (str): The route mode being compared against.

    Returns:
        str: Formatted comparison text.
    """
    mode_names = {
        "fastest": "Fastest Route",
        "best_aq": "Best Air Quality Route",
        "balanced": "Your Route"
    }

    mode_label = mode_names[compared_mode]

    if percentage_diff is None:
        return f"AQI comparison with {mode_label} not available"

    if percentage_diff > 0:
        return f"{abs(percentage_diff)}% better AQI than {mode_label}"
    elif percentage_diff < 0:
        return f"{abs(percentage_diff)}% worse AQI than {mode_label}"
    else:
        return f"Same AQI as {mode_label}"