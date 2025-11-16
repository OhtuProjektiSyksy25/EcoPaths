import pytest
from src.utils.aqi_comparison_utils import calculate_aqi_difference, format_comparison_text

def test_calculate_aqi_difference_all_modes_diff_aqi():
    summaries = {
        "fastest": {"aq_average": 80},
        "best_aq": {"aq_average": 50},
        "balanced": {"aq_average": 65}
    }

    aqi_diffs = calculate_aqi_difference(summaries)

    assert aqi_diffs["best_aq"]["fastest"]["aqi_difference"] == 30
    assert aqi_diffs["best_aq"]["fastest"]["percentage_difference"] == 37.5
    assert aqi_diffs["best_aq"]["fastest"]["comparison_text"] == "37.5% less exposure than Fastest Route"

    assert aqi_diffs["balanced"]["fastest"]["aqi_difference"] == 15
    assert aqi_diffs["balanced"]["fastest"]["percentage_difference"] == 18.75
    assert aqi_diffs["balanced"]["fastest"]["comparison_text"] == "18.75% less exposure than Fastest Route"

def test_calculate_aqi_difference_all_modes_same_aqi():
    summaries = {
        "fastest": {"aq_average": 50},
        "best_aq": {"aq_average": 50},
        "balanced": {"aq_average": 50}
    }

    aqi_diffs = calculate_aqi_difference(summaries)

    assert aqi_diffs["best_aq"]["fastest"]["aqi_difference"] == 0
    assert aqi_diffs["best_aq"]["fastest"]["percentage_difference"] == 0.0
    assert aqi_diffs["best_aq"]["fastest"]["comparison_text"] == "Exposure level is the same as Fastest Route"

    assert aqi_diffs["balanced"]["fastest"]["aqi_difference"] == 0
    assert aqi_diffs["balanced"]["fastest"]["percentage_difference"] == 0.0
    assert aqi_diffs["balanced"]["fastest"]["comparison_text"] == "Exposure level is the same as Fastest Route"

def test_calculate_aqi_difference_with_none_values():
    summaries = {
        "fastest": {"aq_average": None},
        "best_aq": {"aq_average": 45},
        "balanced": {"aq_average": 50}
    }

    aqi_diffs = calculate_aqi_difference(summaries)

    assert aqi_diffs["best_aq"]["fastest"]["aqi_difference"] == None
    assert aqi_diffs["best_aq"]["fastest"]["percentage_difference"] == None
    assert aqi_diffs["best_aq"]["fastest"]["comparison_text"] == "Exposure comparison with Fastest Route not available"

    assert aqi_diffs["balanced"]["fastest"]["aqi_difference"] == None
    assert aqi_diffs["balanced"]["fastest"]["percentage_difference"] == None
    assert aqi_diffs["balanced"]["fastest"]["comparison_text"] == "Exposure comparison with Fastest Route not available"

def test_calculate_aqi_difference_with_zero_values():
    summaries = {
        "fastest": {"aq_average": 50},
        "best_aq": {"aq_average": 0},
        "balanced": {"aq_average": 50}
    }

    aqi_diffs = calculate_aqi_difference(summaries)

    assert aqi_diffs["best_aq"]["fastest"]["aqi_difference"] == 50
    assert aqi_diffs["best_aq"]["fastest"]["percentage_difference"] == 100.0
    assert aqi_diffs["best_aq"]["fastest"]["comparison_text"] == "100.0% less exposure than Fastest Route"

    assert aqi_diffs["balanced"]["fastest"]["aqi_difference"] == 0
    assert aqi_diffs["balanced"]["fastest"]["percentage_difference"] == 0.0
    assert aqi_diffs["balanced"]["fastest"]["comparison_text"] == "Exposure level is the same as Fastest Route"

def test_format_comparison_text_better_aqi():
    formatted_text = format_comparison_text(15.7)
    assert formatted_text == "15.7% less exposure than Fastest Route"

def test_format_comparison_text_same_aqi():
    formatted_text = format_comparison_text(0.0)
    assert formatted_text == "Exposure level is the same as Fastest Route"

def test_format_comparison_text_with_none_values():
    formatted_text = format_comparison_text(None)
    assert formatted_text == "Exposure comparison with Fastest Route not available"
