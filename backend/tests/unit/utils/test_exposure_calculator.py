import pandas as pd
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

    assert result.loc[0, "pm25_exposure"] == 10 * 100
    assert result.loc[1, "pm10_exposure"] == 10 * 200

    assert result.loc[0, "distance_cumulative"] == 100
    assert result.loc[1, "distance_cumulative"] == 300

    assert result.loc[1, "pm25_cumulative"] == (10*100 + 20*200)
