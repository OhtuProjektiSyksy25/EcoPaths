import pytest
import geopandas as gpd
from shapely.geometry import LineString
from unittest.mock import patch, MagicMock
from pathlib import Path
from preprocessor.osm_preprocessing import OSMPreprocessor

def test_download_pbf_if_missing_downloads_file(tmp_path):
    """Test that PBF is downloaded if missing and URL is provided."""

    fake_area = "berlin"
    fake_pbf_path = tmp_path / "file.pbf"
    fake_output_path = tmp_path / "out.parquet"

    with patch("preprocessor.osm_preprocessing.AreaConfig") as MockConfig:
        mock_config = MockConfig.return_value
        mock_config.pbf_file = fake_pbf_path
        mock_config.output_file = fake_output_path
        mock_config.pbf_url = "http://example.com/file.pbf"
        mock_config.bbox = (0, 0, 1, 1)

        preprocessor = OSMPreprocessor(area=fake_area)

        with patch("preprocessor.osm_preprocessing.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"data"]
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            preprocessor.download_pbf_if_missing()

            mock_get.assert_called_once_with("http://example.com/file.pbf", timeout=10, stream=True)

            assert fake_pbf_path.exists()
            assert fake_pbf_path.read_bytes() == b"data"



@pytest.fixture
def dummy_graph():
    """Create a simple GeoDataFrame for reprojection testing."""
    data = {
        "geometry": [LineString([(0, 0), (1, 1)])],
        "length": [1.0],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")

def test_reproject_graph_la(dummy_graph):
    """Test that LA is reprojected to EPSG:2229."""
    processor = OSMPreprocessor(area="la")
    reprojected = processor._reproject_graph(dummy_graph)
    assert reprojected.crs.to_string() == "EPSG:2229"

def test_reproject_graph_berlin(dummy_graph):
    """Test that Berlin is reprojected to EPSG:25833."""
    processor = OSMPreprocessor(area="berlin")
    reprojected = processor._reproject_graph(dummy_graph)
    assert reprojected.crs.to_string() == "EPSG:25833"
