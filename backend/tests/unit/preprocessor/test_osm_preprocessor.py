import pytest
from pathlib import Path
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from preprocessor import osm_preprocessor
from preprocessor.osm_preprocessor import OSMPreprocessor
from preprocessor.edge_cleaner_sql import EdgeCleanerSQL
from src.config.columns import BASE_COLUMNS_DF, EXTRA_COLUMNS


@pytest.fixture
def preprocessor(monkeypatch):
    processor = OSMPreprocessor(area="testarea", network_type="walking")
    processor.crs = "EPSG:25833"

    monkeypatch.setattr(
        processor, "downloader",
        type("DummyDownloader", (), {
             "save_bbox_network_to_file": lambda nt: None})()
    )
    monkeypatch.setattr(
        processor, "load_raw_edges_in_batches", lambda *a, **kw: [])

    return processor


@pytest.fixture
def mock_path_exists(monkeypatch):
    def _mock(path, exists=True):
        monkeypatch.setattr(Path, "exists", lambda self: exists)
        return path
    return _mock


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
    assert result.index[0] == 0


@pytest.mark.parametrize("extra_cols_in_gdf", [False])
def test_filter_to_selected_columns(preprocessor, extra_cols_in_gdf):
    gdf_dict = {"geometry": [LineString([(0, 0), (1, 1)])]}
    gdf = gpd.GeoDataFrame(gdf_dict, crs="EPSG:25833")

    filtered = preprocessor.filter_to_selected_columns(gdf, "walking")

    expected_cols = set(
        BASE_COLUMNS_DF + EXTRA_COLUMNS["walking"] + ["geometry"])
    assert set(filtered.columns) == expected_cols

    for col in EXTRA_COLUMNS["walking"]:
        if col.endswith("_influence"):
            assert filtered[col].iloc[0] == 1.0
        else:
            assert filtered[col].iloc[0] is None


def test_load_raw_edges_file_not_found(monkeypatch, preprocessor):
    monkeypatch.setattr(preprocessor, "load_raw_edges_in_batches",
                        lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError))
    import pytest
    with pytest.raises(FileNotFoundError):
        list(preprocessor.load_raw_edges_in_batches())


def test_extract_edges_calls_all_methods(monkeypatch, preprocessor):
    calls = []

    monkeypatch.setattr(preprocessor, "load_raw_edges_in_batches",
                        lambda *a, **kw: [gpd.GeoDataFrame(
                            geometry=[LineString([(0, 0), (1, 1)])], crs="EPSG:25833")])
    monkeypatch.setattr(preprocessor, "prepare_raw_edges",
                        lambda gdf: calls.append("prepare") or gdf)
    monkeypatch.setattr(preprocessor, "filter_to_selected_columns",
                        lambda gdf, nt: calls.append("filter") or gdf)
    from src.database import db_client
    monkeypatch.setattr(db_client.DatabaseClient, "save_edges",
                        lambda self, gdf, area, nt, if_exists="fail": calls.append("save"))

    class DummyCleaner:
        def run_full_cleaning(self, a, n): return None
        def remove_disconnected_edges(self, a, n): return None

    monkeypatch.setattr(osm_preprocessor, "EdgeCleanerSQL",
                        lambda db: DummyCleaner())
    monkeypatch.setattr(preprocessor.downloader, "save_bbox_network_to_file",
                        lambda *args, **kwargs: None)

    preprocessor.extract_edges()
    assert calls == ["prepare", "filter", "save"]


def test_load_raw_edges_batches(preprocessor):
    gdf = gpd.GeoDataFrame({
        "geometry": [LineString([(0, 0), (1, 1)]) for _ in range(10)]
    }, crs="EPSG:25833")
    preprocessor.batch_size = 3
    preprocessor.load_raw_edges_in_batches = lambda *a, **kw: (
        gdf.iloc[i:i+3] for i in range(0, 10, 3))

    batches = list(preprocessor.load_raw_edges_in_batches())
    batch_lengths = [len(b) for b in batches]
    assert batch_lengths == [3, 3, 3, 1]
