import pytest
import geopandas as gpd
from shapely.geometry import LineString

from src.utils.exposure_calculator import compute_exposure


def test_compute_exposure_basic():
    df = gpd.GeoDataFrame({
        "pm2_5": [10, 20],
        "pm10": [5, 10],
        "length_m": [100, 200],
        "geometry": [
            LineString([(0, 0), (1, 0)]),
            LineString([(1, 0), (2, 0)])
        ]
    })

    result = compute_exposure(df)

    WALK_SPEED = 1.4  # m/s as defined in utils.route_summary.SPEEDS
    VENT_LPM = 8.0
    vent_m3s = (VENT_LPM / 1000.0) / 60.0

    t0 = 100.0 / WALK_SPEED
    t1 = 200.0 / WALK_SPEED

    # expected inhaled doses (µg) = concentration (µg/m3) * inhaled_volume (m3)
    expected_pm25_0 = 10.0 * vent_m3s * t0
    expected_pm10_1 = 10.0 * vent_m3s * t1

    assert result.loc[0, "pm25_inhaled"] == pytest.approx(expected_pm25_0)
    assert result.loc[1, "pm10_inhaled"] == pytest.approx(expected_pm10_1)

    assert result.loc[0, "distance_cumulative"] == pytest.approx(100.0)
    assert result.loc[1, "distance_cumulative"] == pytest.approx(300.0)

    # cumulative pm25 inhaled (row1 should equal sum of row0 and row1 inhaled pm25)
    expected_pm25_cumulative_row1 = expected_pm25_0 + (20.0 * vent_m3s * t1)
    assert result.loc[1, "pm25_inhaled_cumulative"] == pytest.approx(
        expected_pm25_cumulative_row1)
