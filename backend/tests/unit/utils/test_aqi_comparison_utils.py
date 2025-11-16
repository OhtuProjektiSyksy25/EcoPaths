import pytest
from src.utils.aqi_comparison_utils import calculate_aqi_difference, format_comparison_text

def test_calculate_aqi_difference_all_modes_diff_aqi():
    summaries = {
        "fastest": {"aq_average": 80},
        "best_aq": {"aq_average": 50},
        "balanced": {"aq_average": 65}
    }

    aqi_diffs = calculate_aqi_difference(summaries)

    assert aqi_diffs["fastest"]["best_aq"]["aqi_difference"] == -30
    assert aqi_diffs["fastest"]["best_aq"]["percentage_difference"] == -60.00
    assert aqi_diffs["fastest"]["best_aq"]["comparison_text"] == "60.0% worse AQI than Best Air Quality Route"

    assert aqi_diffs["fastest"]["balanced"]["aqi_difference"] == -15
    assert aqi_diffs["fastest"]["balanced"]["percentage_difference"] == -23.08
    assert aqi_diffs["fastest"]["balanced"]["comparison_text"] == "23.08% worse AQI than Your Route"

    assert aqi_diffs["best_aq"]["fastest"]["aqi_difference"] == 30
    assert aqi_diffs["best_aq"]["fastest"]["percentage_difference"] == 37.5
    assert aqi_diffs["best_aq"]["fastest"]["comparison_text"] == "37.5% better AQI than Fastest Route"

    assert aqi_diffs["best_aq"]["balanced"]["aqi_difference"] == 15
    assert aqi_diffs["best_aq"]["balanced"]["percentage_difference"] == 23.08
    assert aqi_diffs["best_aq"]["balanced"]["comparison_text"] == "23.08% better AQI than Your Route"

    assert aqi_diffs["balanced"]["fastest"]["aqi_difference"] == 15
    assert aqi_diffs["balanced"]["fastest"]["percentage_difference"] == 18.75
    assert aqi_diffs["balanced"]["fastest"]["comparison_text"] == "18.75% better AQI than Fastest Route"

    assert aqi_diffs["balanced"]["best_aq"]["aqi_difference"] == -15
    assert aqi_diffs["balanced"]["best_aq"]["percentage_difference"] == -30.00
    assert aqi_diffs["balanced"]["best_aq"]["comparison_text"] == "30.0% worse AQI than Best Air Quality Route"

def test_calculate_aqi_difference_all_modes_same_aqi():
    summaries = {
        "fastest": {"aq_average": 50},
        "best_aq": {"aq_average": 50},
        "balanced": {"aq_average": 50}
    }

    aqi_diffs = calculate_aqi_difference(summaries)

    assert aqi_diffs["fastest"]["best_aq"]["aqi_difference"] == 0
    assert aqi_diffs["fastest"]["best_aq"]["percentage_difference"] == 0.0
    assert aqi_diffs["fastest"]["best_aq"]["comparison_text"] == "Same AQI as Best Air Quality Route"

    assert aqi_diffs["fastest"]["balanced"]["aqi_difference"] == 0
    assert aqi_diffs["fastest"]["balanced"]["percentage_difference"] == 0.0
    assert aqi_diffs["fastest"]["balanced"]["comparison_text"] == "Same AQI as Your Route"

    assert aqi_diffs["best_aq"]["fastest"]["aqi_difference"] == 0
    assert aqi_diffs["best_aq"]["fastest"]["percentage_difference"] == 0.0
    assert aqi_diffs["best_aq"]["fastest"]["comparison_text"] == "Same AQI as Fastest Route"

    assert aqi_diffs["best_aq"]["balanced"]["aqi_difference"] == 0
    assert aqi_diffs["best_aq"]["balanced"]["percentage_difference"] == 0.0
    assert aqi_diffs["best_aq"]["balanced"]["comparison_text"] == "Same AQI as Your Route"

    assert aqi_diffs["balanced"]["fastest"]["aqi_difference"] == 0
    assert aqi_diffs["balanced"]["fastest"]["percentage_difference"] == 0.0
    assert aqi_diffs["balanced"]["fastest"]["comparison_text"] == "Same AQI as Fastest Route"

    assert aqi_diffs["balanced"]["best_aq"]["aqi_difference"] == 0
    assert aqi_diffs["balanced"]["best_aq"]["percentage_difference"] == 0.0
    assert aqi_diffs["balanced"]["best_aq"]["comparison_text"] == "Same AQI as Best Air Quality Route"

def test_calculate_aqi_difference_with_none_values():
    summaries = {
        "fastest": {"aq_average": None},
        "best_aq": {"aq_average": 45},
        "balanced": {"aq_average": 50}
    }

    aqi_diffs = calculate_aqi_difference(summaries)

    assert aqi_diffs["fastest"]["best_aq"]["aqi_difference"] == None
    assert aqi_diffs["fastest"]["best_aq"]["percentage_difference"] == None
    assert aqi_diffs["fastest"]["best_aq"]["comparison_text"] == "AQI comparison with Best Air Quality Route not available"

    assert aqi_diffs["fastest"]["balanced"]["aqi_difference"] == None
    assert aqi_diffs["fastest"]["balanced"]["percentage_difference"] == None
    assert aqi_diffs["fastest"]["balanced"]["comparison_text"] == "AQI comparison with Your Route not available"

    assert aqi_diffs["best_aq"]["fastest"]["aqi_difference"] == None
    assert aqi_diffs["best_aq"]["fastest"]["percentage_difference"] == None
    assert aqi_diffs["best_aq"]["fastest"]["comparison_text"] == "AQI comparison with Fastest Route not available"

    assert aqi_diffs["best_aq"]["balanced"]["aqi_difference"] == 5
    assert aqi_diffs["best_aq"]["balanced"]["percentage_difference"] == 10.0
    assert aqi_diffs["best_aq"]["balanced"]["comparison_text"] == "10.0% better AQI than Your Route"

    assert aqi_diffs["balanced"]["fastest"]["aqi_difference"] == None
    assert aqi_diffs["balanced"]["fastest"]["percentage_difference"] == None
    assert aqi_diffs["balanced"]["fastest"]["comparison_text"] == "AQI comparison with Fastest Route not available"

    assert aqi_diffs["balanced"]["best_aq"]["aqi_difference"] == -5
    assert aqi_diffs["balanced"]["best_aq"]["percentage_difference"] == -11.11
    assert aqi_diffs["balanced"]["best_aq"]["comparison_text"] == "11.11% worse AQI than Best Air Quality Route"

def test_calculate_aqi_difference_with_zero_values():
    summaries = {
        "fastest": {"aq_average": 50},
        "best_aq": {"aq_average": 0},
        "balanced": {"aq_average": 50}
    }

    aqi_diffs = calculate_aqi_difference(summaries)

    assert aqi_diffs["fastest"]["best_aq"]["aqi_difference"] == None
    assert aqi_diffs["fastest"]["best_aq"]["percentage_difference"] == None
    assert aqi_diffs["fastest"]["best_aq"]["comparison_text"] == "AQI comparison with Best Air Quality Route not available"

    assert aqi_diffs["fastest"]["balanced"]["aqi_difference"] == 0
    assert aqi_diffs["fastest"]["balanced"]["percentage_difference"] == 0.0
    assert aqi_diffs["fastest"]["balanced"]["comparison_text"] == "Same AQI as Your Route"

    assert aqi_diffs["best_aq"]["fastest"]["aqi_difference"] == 50
    assert aqi_diffs["best_aq"]["fastest"]["percentage_difference"] == 100.0
    assert aqi_diffs["best_aq"]["fastest"]["comparison_text"] == "100.0% better AQI than Fastest Route"

    assert aqi_diffs["best_aq"]["balanced"]["aqi_difference"] == 50
    assert aqi_diffs["best_aq"]["balanced"]["percentage_difference"] == 100.0
    assert aqi_diffs["best_aq"]["balanced"]["comparison_text"] == "100.0% better AQI than Your Route"

    assert aqi_diffs["balanced"]["fastest"]["aqi_difference"] == 0
    assert aqi_diffs["balanced"]["fastest"]["percentage_difference"] == 0.0
    assert aqi_diffs["balanced"]["fastest"]["comparison_text"] == "Same AQI as Fastest Route"

    assert aqi_diffs["balanced"]["best_aq"]["aqi_difference"] == None
    assert aqi_diffs["balanced"]["best_aq"]["percentage_difference"] == None
    assert aqi_diffs["balanced"]["best_aq"]["comparison_text"] == "AQI comparison with Best Air Quality Route not available"

def test_format_comparison_text_better_aqi():
    formatted_text = format_comparison_text(15.7, "fastest")
    assert formatted_text == "15.7% better AQI than Fastest Route"

    formatted_text = format_comparison_text(2.0, "best_aq")
    assert formatted_text == "2.0% better AQI than Best Air Quality Route"

    formatted_text = format_comparison_text(10.37, "balanced")
    assert formatted_text == "10.37% better AQI than Your Route"

def test_format_comparison_text_worse_aqi():
    formatted_text = format_comparison_text(-5.2, "fastest")
    assert formatted_text == "5.2% worse AQI than Fastest Route"

    formatted_text = format_comparison_text(-33.0, "best_aq")
    assert formatted_text == "33.0% worse AQI than Best Air Quality Route"

    formatted_text = format_comparison_text(-20.22, "balanced")
    assert formatted_text == "20.22% worse AQI than Your Route"

def test_format_comparison_text_same_aqi():
    formatted_text = format_comparison_text(0.0, "fastest")
    assert formatted_text == "Same AQI as Fastest Route"

    formatted_text = format_comparison_text(0.0, "best_aq")
    assert formatted_text == "Same AQI as Best Air Quality Route"

    formatted_text = format_comparison_text(0.0, "balanced")
    assert formatted_text == "Same AQI as Your Route"

def test_format_comparison_text_with_none_values():
    formatted_text = format_comparison_text(None, "fastest")
    assert formatted_text == "AQI comparison with Fastest Route not available"

    formatted_text = format_comparison_text(None, "best_aq")
    assert formatted_text == "AQI comparison with Best Air Quality Route not available"

    formatted_text = format_comparison_text(None, "balanced")
    assert formatted_text == "AQI comparison with Your Route not available"
