import pytest
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from preprocessor.osm_preprocessor import OSMPreprocessor
from src.config.columns import BASE_COLUMNS_DF, EXTRA_COLUMNS


@pytest.fixture
def preprocessor():
    return OSMPreprocessor(area="testarea", network_type="walking")


def test_prepare_raw_edges_explodes(preprocessor):
    raw = gpd.GeoDataFrame({
        "geometry": [
            LineString([(0, 0), (1, 1)]),
            MultiLineString([[(2, 2), (3, 3)], [(4, 4), (5, 5)]])
        ]
    }, crs="EPSG:4326")

    result = preprocessor.prepare_raw_edges(raw)

    assert str(result.crs) == preprocessor.crs
    assert all(geom.geom_type == "LineString" for geom in result.geometry)


@pytest.mark.parametrize("network_type", ["walking", "cycling", "driving"])
def test_filter_to_selected_columns(preprocessor, network_type):
    gdf = gpd.GeoDataFrame(
        {"geometry": [LineString([(0, 0), (1, 1)])]}, crs="EPSG:25833")

    filtered = preprocessor.filter_to_selected_columns(gdf, network_type)

    expected_cols = set(
        BASE_COLUMNS_DF + EXTRA_COLUMNS.get(network_type, []) + ["geometry"])
    assert set(filtered.columns) == expected_cols

    for col in EXTRA_COLUMNS.get(network_type, []):
        if col.endswith("_influence"):
            assert filtered[col].iloc[0] == 1.0


def test_prepare_geometries_removes_invalid(preprocessor):
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (0, 0)])]
    }, crs="EPSG:4326")
    result = preprocessor.prepare_geometries(gdf)
    assert len(result) == 0


def test_filter_required_columns_adds_defaults(preprocessor):
    gdf = gpd.GeoDataFrame(
        {"geometry": [LineString([(0, 0), (1, 1)])]}, crs="EPSG:25833")
    required = ["geometry", "foo"]
    result = preprocessor.filter_required_columns(
        gdf, required, defaults={"foo": 42})
    assert "foo" in result.columns
    assert result["foo"].iloc[0] == 42


def test_prepare_green_area_batch_detects_type(preprocessor):
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "natural": ["forest"]
    }, crs="EPSG:25833")
    result = preprocessor.prepare_green_area_batch(gdf)
    assert "green_type" in result.columns
    assert result["green_type"].iloc[0] != "unknown"
