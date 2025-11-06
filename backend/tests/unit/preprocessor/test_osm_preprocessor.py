import pytest
import geopandas as gpd
from shapely.geometry import LineString
from preprocessor.osm_preprocessor import OSMPreprocessor
from src.config.columns import BASE_COLUMNS, EXTRA_COLUMNS


class FakeOSM:
    def get_network(self, network_type):
        return gpd.GeoDataFrame({
            "geometry": [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])],
            "highway": ["footway", "footway"]
        }, crs="EPSG:25833")


@pytest.fixture
def preprocessor(monkeypatch):
    processor = OSMPreprocessor(area="testarea", network_type="walking")
    monkeypatch.setattr(processor.downloader,
                        "get_osm_instance", lambda: FakeOSM())
    processor.crs = "EPSG:25833"
    return processor


def test_prepare_raw_edges_returns_valid_gdf(preprocessor):
    osm = preprocessor.downloader.get_osm_instance()
    gdf = preprocessor.prepare_raw_edges(osm)

    assert isinstance(gdf, gpd.GeoDataFrame)
    assert not gdf.empty
    assert str(gdf.crs) == str(preprocessor.crs)
    assert all(gdf.geometry.geom_type == "LineString")
    assert not any(gdf.geometry.geom_type == "MultiLineString")


def test_prepare_raw_edges_explodes_multilinestring(monkeypatch, preprocessor):
    class MultiLineFakeOSM:
        def get_network(self, network_type):
            return gpd.GeoDataFrame({
                "geometry": [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])],
                "highway": ["footway", "footway"]
            }, crs="EPSG:25833").explode(index_parts=False)

    monkeypatch.setattr(preprocessor.downloader,
                        "get_osm_instance", lambda: MultiLineFakeOSM())
    gdf = preprocessor.prepare_raw_edges(
        preprocessor.downloader.get_osm_instance())

    assert len(gdf) >= 2
    assert all(gdf.geometry.geom_type == "LineString")


def test_filter_to_selected_columns_filters_correctly(preprocessor):
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "highway": ["footway"],
        "access": ["yes"],
        "bicycle": ["no"],
        "tile_id": ["A1"],
        "length_m": [123.45],
        "extra_column": ["drop me"]
    }, crs="EPSG:25833")

    filtered = preprocessor.filter_to_selected_columns(gdf, "walking")

    assert isinstance(filtered, gpd.GeoDataFrame)
    assert filtered.geometry.name == "geometry"

    expected_columns = set(BASE_COLUMNS + EXTRA_COLUMNS["walking"])
    expected_columns.add("geometry")

    assert set(filtered.columns) == expected_columns

    for col in EXTRA_COLUMNS["walking"]:
        if col.endswith("_influence"):
            assert filtered[col].iloc[0] == 1.0

    for col in BASE_COLUMNS:
        if col not in gdf.columns and col != "geometry":
            assert filtered[col].iloc[0] is None
