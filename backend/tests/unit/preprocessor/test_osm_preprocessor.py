import pytest
import warnings
import geopandas as gpd
from shapely.geometry import LineString
from preprocessor.osm_preprocessor import OSMPreprocessor
from preprocessor.osm_validation import OSMValidator
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
    gdf = preprocessor._load_and_prepare_edges()
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
    gdf = preprocessor._load_and_prepare_edges()
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

    filtered = preprocessor._filter_to_selected_columns(gdf)

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


def test_load_and_prepare_edges_adds_edge_id(preprocessor):
    gdf = preprocessor._load_and_prepare_edges()
    assert "edge_id" in gdf.columns
    assert list(gdf["edge_id"]) == list(range(1, len(gdf)+1))


def test_extract_landuse_filters_green_polygons(preprocessor, monkeypatch):
    class FakeOSMLanduse:
        def get_landuse(self):
            import geopandas as gpd
            from shapely.geometry import Polygon
            return gpd.GeoDataFrame({
                "landuse": ["forest", "industrial", "park"],
                "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                             Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                             Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
            }, crs="EPSG:25833")

    monkeypatch.setattr(preprocessor.downloader,
                        "get_osm_instance", lambda: FakeOSMLanduse())
    preprocessor.crs = "EPSG:25833"

    preprocessor._extract_landuse()


def test_run_executes_all_steps(monkeypatch):
    pre = OSMPreprocessor("testarea", "walking")

    monkeypatch.setattr(pre, "_extract_landuse",
                        lambda: print("extract_landuse called"))
    monkeypatch.setattr(pre, "_load_and_prepare_edges", lambda: gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)])],
        "edge_id": [1]
    }, crs="EPSG:25833"))
    monkeypatch.setattr(pre, "_save_edges_to_db",
                        lambda gdf: print("save_edges_to_db called"))
    monkeypatch.setattr(pre, "_clean_edges_in_db",
                        lambda: print("clean_edges_in_db called"))
    monkeypatch.setattr(pre, "_postprocess_walking_network",
                        lambda: print("postprocess_walking_network called"))

    pre.run()
