import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from preprocessor.osm_downloader import OSMDownloader


@pytest.fixture
def mock_area_config(tmp_path):
    config = MagicMock()
    config.pbf_file = tmp_path / "test.pbf"
    config.pbf_url = "http://example.com/test.pbf"
    config.bbox = [0, 0, 1, 1]
    return config


def test_download_skips_if_file_exists(mock_area_config):
    mock_area_config.pbf_file.write_text("already downloaded")

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("test-area")
        downloader.download_if_missing()

    assert mock_area_config.pbf_file.exists()
    assert mock_area_config.pbf_file.read_text() == "already downloaded"


def test_download_raises_if_url_missing(mock_area_config):
    mock_area_config.pbf_url = None

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("test-area")
        with pytest.raises(ValueError, match="No PBF URL configured"):
            downloader.download_if_missing()


@patch("requests.get")
def test_download_makes_request(mock_get, mock_area_config):
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("test-area")
        downloader.download_if_missing()

    assert mock_area_config.pbf_file.exists()
    assert mock_area_config.pbf_file.read_bytes() == b"chunk1chunk2"


@patch("preprocessor.osm_downloader.OSM")
def test_get_osm_instance_calls_osm(mock_osm, mock_area_config):
    mock_area_config.pbf_file.write_text("dummy")
    with patch("preprocessor.osm_downloader.AreaConfig", return_value=mock_area_config):
        downloader = OSMDownloader("test-area")
        instance = downloader.get_osm_instance()

    mock_osm.assert_called_once_with(
        str(mock_area_config.pbf_file), bounding_box=mock_area_config.bbox)
