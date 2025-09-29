import pytest
from unittest.mock import patch, MagicMock
from src.core.osm_preprocessing import OSMPreprocessor

def test_download_pbf_if_missing_downloads_file(tmp_path):
    """Test that PBF is downloaded if missing and URL is provided."""

    fake_area = "la"
    fake_pbf_path = tmp_path / "file.pbf"
    
    # Mock AreaConfig to return test paths
    with patch("src.core.osm_preprocessing.AreaConfig") as MockConfig:
        MockConfig.return_value.pbf_file = str(fake_pbf_path)
        MockConfig.return_value.output_file = str(tmp_path / "out.parquet")
        MockConfig.return_value.pbf_url = "http://example.com/file.pbf"
        MockConfig.return_value.bbox = (0, 0, 1, 1)

        preprocessor = OSMPreprocessor(area=fake_area)

        # Mock requests.get to avoid real HTTP call
        with patch("src.core.osm_preprocessing.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"data"]
            mock_get.return_value = mock_response

            preprocessor.download_pbf_if_missing()
            # Check that requests.get was called
            mock_get.assert_called_once_with("http://example.com/file.pbf", timeout=10, stream=True)


