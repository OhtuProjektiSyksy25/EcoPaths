import pytest
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from unittest.mock import MagicMock, patch
from pathlib import Path
from preprocessor.osm_downloader import OSMDownloader


@pytest.fixture
def mock_area_config(tmp_path):
    config = MagicMock()
    config.pbf_file = tmp_path / "test.pbf"
    config.pbf_url = "http://example.com/test.pbf"
    config.bbox = [0, 0, 1, 1]
    config.area = "testarea"
    config.get_raw_file_path.return_value = tmp_path / "output.gpkg"
    return config


def test_download_skips_if_file_exists(mock_area_config):
    mock_area_config.pbf_file.write_text("already downloaded")

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("testarea")
        downloader.download_if_missing()

    assert mock_area_config.pbf_file.exists()
    assert mock_area_config.pbf_file.read_text() == "already downloaded"


def test_download_raises_if_url_missing(mock_area_config):
    mock_area_config.pbf_url = None

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("testarea")
        with pytest.raises(ValueError, match="No PBF URL configured"):
            downloader.download_if_missing()


@patch("requests.get")
def test_download_makes_request(mock_get, mock_area_config):
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("testarea")
        downloader.download_if_missing()

    assert mock_area_config.pbf_file.exists()
    assert mock_area_config.pbf_file.read_bytes() == b"chunk1chunk2"


@patch("requests.get")
def test_download_handles_http_error(mock_get, mock_area_config):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")
    mock_get.return_value = mock_response

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("testarea")
        with pytest.raises(Exception, match="404 Not Found"):
            downloader.download_if_missing()


@patch("preprocessor.osm_downloader.OSM")
def test_extract_and_save_network_saves_gpkg(mock_osm_class, mock_area_config, tmp_path):
    mock_edges = MagicMock()
    mock_edges.empty = False
    mock_edges.to_file = MagicMock()
    mock_osm = MagicMock()
    mock_osm.get_network.return_value = mock_edges
    mock_osm_class.return_value = mock_osm

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("testarea")
        downloader.download_if_missing = MagicMock()
        output_path = downloader.extract_and_save_network("gpkg")

    mock_edges.to_file.assert_called_once_with(output_path, driver="GPKG")
    assert output_path.name == "output.gpkg"


@patch("preprocessor.osm_downloader.OSM")
def test_extract_and_save_green_areas_saves_gpkg(mock_osm_class, mock_area_config, tmp_path):

    landuse = gpd.GeoDataFrame(
        {"landuse": ["forest"], "geometry": [Point(0, 0)]},
        crs="EPSG:25833"
    )
    leisure = gpd.GeoDataFrame(
        {"leisure": ["park"], "geometry": [Point(1, 1)]},
        crs="EPSG:25833"
    )
    natural = gpd.GeoDataFrame(
        {"natural": ["wood"], "geometry": [Point(2, 2)]},
        crs="EPSG:25833"
    )

    mock_osm = MagicMock()
    mock_osm.get_landuse.return_value = landuse
    mock_osm.get_pois.side_effect = [leisure, natural]
    mock_osm_class.return_value = mock_osm

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("testarea")
        downloader.download_if_missing = MagicMock()
        output_path = downloader.extract_and_save_green_areas("gpkg")

    assert output_path.name == "output.gpkg"
