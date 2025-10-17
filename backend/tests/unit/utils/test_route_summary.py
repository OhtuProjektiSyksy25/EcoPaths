from src.utils.route_summary import format_walk_time


def test_short_distance():
    assert format_walk_time(140) == "1 min 40 s"


def test_exactly_one_hour():
    assert format_walk_time(5040) == "1h 0 min"


def test_multiple_hours():
    assert format_walk_time(10080) == "2h 0 min"


def test_zero_distance():
    assert format_walk_time(0) == "0 min 0 s"


def test_none_input():
    assert format_walk_time(None) == "unknown"


def test_nan_input():
    import pandas as pd
    assert format_walk_time(pd.NA) == "unknown"
    assert format_walk_time(float("nan")) == "unknown"
