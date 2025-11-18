import pytest
import geopandas as gpd
from shapely.geometry import Point
from unittest.mock import MagicMock, patch
from preprocessor.osm_pipeline_runner import OSMPipelineRunner


def make_gdf(n=3):
    return gpd.GeoDataFrame({"geometry": [Point(i, i) for i in range(n)]}, crs="EPSG:25833")


def test_run_calls_all_stages(monkeypatch):
    runner = OSMPipelineRunner("testarea")
    runner._process_grid = MagicMock()
    runner._process_green_areas = MagicMock()
    runner._process_network = MagicMock()

    runner.run()

    runner._process_grid.assert_called_once()
    runner._process_green_areas.assert_called_once()
    # network called twice: driving + walking
    assert runner._process_network.call_count == 2
    runner._process_network.assert_any_call("driving")
    runner._process_network.assert_any_call("walking")


def test_process_grid_saves_grid(monkeypatch):
    runner = OSMPipelineRunner("testarea")
    mock_grid = MagicMock()
    mock_grid.create_grid.return_value = make_gdf()
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.Grid", lambda area: mock_grid)
    runner.db.save_grid = MagicMock()

    runner._process_grid()

    mock_grid.create_grid.assert_called_once()
    runner.db.save_grid.assert_called_once()


def test_process_in_batches_calls_prepare_and_save():
    runner = OSMPipelineRunner("testarea")
    gdf = make_gdf(5)
    prepare_fn = MagicMock(side_effect=lambda b: b)
    save_fn = MagicMock()

    runner.batch_size = 2
    runner._process_in_batches(gdf, prepare_fn, save_fn, "extra")

    # 3 batches: 2+2+1
    assert prepare_fn.call_count == 3
    assert save_fn.call_count == 3
    for call in save_fn.call_args_list:
        df_arg, extra_arg = call[0][:2]
        assert extra_arg == "extra"
        assert call[1]["if_exists"] == "append"


@patch("preprocessor.osm_pipeline_runner.gpd.read_file")
def test_process_green_areas_calls_cleaner(mock_read_file, monkeypatch):
    runner = OSMPipelineRunner("testarea")
    mock_preproc = MagicMock()
    mock_preproc.downloader.extract_and_save_green_areas.return_value = "dummy.gpkg"
    mock_preproc.prepare_green_area_batch.side_effect = lambda b: b
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.OSMPreprocessor", lambda *args, **kwargs: mock_preproc)
    mock_read_file.return_value = make_gdf(2)
    runner.db.save_green_areas = MagicMock()
    mock_cleaner = MagicMock()
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.GreenCleanerSQL", lambda db: mock_cleaner)

    runner._process_green_areas()

    runner.db.save_green_areas.assert_called()
    mock_cleaner.run.assert_called_once_with("testarea")


@patch("preprocessor.osm_pipeline_runner.gpd.read_file")
def test_process_network_calls_cleaning_and_nodes(mock_read_file, monkeypatch):
    runner = OSMPipelineRunner("testarea")
    mock_preproc = MagicMock()
    mock_preproc.downloader.extract_and_save_network.return_value = "dummy.gpkg"
    mock_preproc.prepare_raw_edges.side_effect = lambda b: b
    mock_preproc.filter_to_selected_columns.side_effect = lambda b, nt: b
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.OSMPreprocessor", lambda *args, **kwargs: mock_preproc)
    mock_read_file.return_value = make_gdf(2)
    runner.db.save_edges = MagicMock()
    mock_cleaner = MagicMock()
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.EdgeCleanerSQL", lambda db: mock_cleaner)
    mock_builder = MagicMock()
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.NodeBuilder", lambda db, *args, **kwargs: mock_builder)
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.TrafficInfluenceBuilder", lambda db, a: MagicMock())
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.GreenInfluenceBuilder", lambda db, a: MagicMock())
    monkeypatch.setattr(
        "preprocessor.osm_pipeline_runner.EnvInfluenceBuilder", lambda db, a: MagicMock())

    runner._process_network("walking")

    runner.db.save_edges.assert_called()
    mock_cleaner.run_full_cleaning.assert_called_once()
    mock_builder.build_nodes_and_attach_to_edges.assert_called_once()
    mock_builder.remove_unused_nodes.assert_called_once()
    mock_builder.assign_tile_ids.assert_called_once()
