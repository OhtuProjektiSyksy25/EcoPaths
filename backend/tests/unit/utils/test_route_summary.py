import pytest
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from src.utils.route_summary import (
    format_walk_time,
    calculate_total_length,
    calculate_aq_average,
    summarize_route,
)


@pytest.fixture
def sample_route():
    data = {
        "geometry": [
            LineString([(0, 0), (1, 1)]),
            LineString([(1, 1), (2, 2)]),
        ],
        "length_m": [1000, 500],
        "aqi": [40, 60],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


@pytest.fixture
def route_with_missing_aqi():
    data = {
        "geometry": [LineString([(0, 0), (1, 1)])],
        "length_m": [1000],
        "aqi": [None],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


def test_format_walk_time_short():
    assert format_walk_time(140) == "2 min"
    assert format_walk_time(0) == "0 min"
    assert format_walk_time(None) == "unknown"


def test_format_walk_time_long():
    assert format_walk_time(5040) == "1h 0 min"  # 1 hour exactly
    assert format_walk_time(5100) == "1h 1 min"  # 1 hour + 30 sec → round up


def test_calculate_total_length(sample_route):
    assert calculate_total_length(sample_route) == 1500


def test_calculate_aq_average(sample_route):
    # Weighted average: (1000×40 + 500×60) / 1500 = 46.67
    assert round(calculate_aq_average(sample_route), 2) == 46.67


def test_calculate_aq_average_missing(route_with_missing_aqi):
    assert calculate_aq_average(route_with_missing_aqi) is None


def test_summarize_route(sample_route):
    summary = summarize_route(sample_route)
    assert summary["total_length"] == 1.5
    assert summary["aq_average"] == 47  # rounded from 46.67
    assert summary["time_estimate"] == "18 min"


def test_summarize_route_missing(route_with_missing_aqi):
    summary = summarize_route(route_with_missing_aqi)
    assert summary["total_length"] == 1.0
    assert summary["aq_average"] is None
    assert summary["time_estimate"] == "12 min"
