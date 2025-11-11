"""
Unit tests for Google API service.
"""

import pytest
import geopandas as gpd
from requests.exceptions import RequestException
from unittest.mock import Mock, patch
from src.services.google_api_service import GoogleAPIService


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API key for testing."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")


@pytest.fixture
def api_service(mock_api_key):
    """Create GoogleAPIService instance with mocked API key."""
    return GoogleAPIService()


@pytest.fixture
def mock_load_grid(monkeypatch):
    """Mock DatabaseClient.load_grid to return dummy GeoDataFrame."""
    dummy_gdf = gpd.GeoDataFrame({
        "tile_id": ["t1", "t2"],
        "geometry": [None, None],
        "center_lat": [52.52, 52.53],
        "center_lon": [13.405, 13.406]
    }, crs="EPSG:25833")

    monkeypatch.setattr(
        "database.db_client.DatabaseClient.load_grid",
        lambda self, area: dummy_gdf
    )


class TestGoogleAPIService:
    """Unit tests for GoogleAPIService."""

    def test_init_with_api_key(self, mock_api_key):
        """Service initializes correctly with API key."""
        service = GoogleAPIService()
        assert service.api_key == "test_api_key"
        assert service.endpoint == "https://airquality.googleapis.com/v1/currentConditions:lookup"

    @patch("src.services.google_api_service.requests.post")
    def test_fetch_single_tile_success(self, mock_post, api_service):
        """_fetch_single_tile returns valid AQI structure (mocked or test mode)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"indexes": [{"aqi": 42}]}
        mock_post.return_value = mock_response

        result = api_service._fetch_single_tile(52.52, 13.405)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"aqi", "pm2_5", "no2"}
        assert isinstance(result["aqi"], (int, type(None)))
        if isinstance(result["aqi"], int):
            assert 0 < result["aqi"] <= 150

    @patch("src.services.google_api_service.requests.post", side_effect=RequestException("API down"))
    def test_fetch_single_tile_failure(self, mock_post, api_service):
        """Handles failed requests gracefully, even in test mode."""
        result = api_service._fetch_single_tile(52.52, 13.405)

        assert set(result.keys()) == {"aqi", "pm2_5", "no2"}
        assert isinstance(result["aqi"], (int, type(None)))

    @patch("src.services.google_api_service.requests.post")
    def test_get_aq_data_for_tiles(self, mock_post, api_service, mock_load_grid):
        """get_aq_data_for_tiles returns GeoDataFrame with correct columns."""
        def side_effect(url, json, params, headers, timeout):
            tile_lat = json["location"]["latitude"]
            if tile_lat == 52.52:
                return Mock(status_code=200, json=lambda: {"indexes": [{"aqi": 10}]})
            return Mock(status_code=200, json=lambda: {"indexes": [{"aqi": 20}]})
        mock_post.side_effect = side_effect

        tile_ids = ["t1", "t2"]
        gdf = api_service.get_aq_data_for_tiles(tile_ids, "berlin")

        assert set(gdf.columns) == {"tile_id", "raw_aqi", "pm2_5", "no2", "geometry"}
        assert set(gdf["tile_id"]) == set(tile_ids)
        assert gdf.crs.to_string() == "EPSG:25833"

        for val in gdf["raw_aqi"]:
            assert isinstance(val, (int, type(None)))
            if isinstance(val, int):
                assert 0 < val <= 150

    @patch("src.services.google_api_service.requests.post")
    def test_get_aq_data_for_tiles_empty_result(self, mock_post, api_service, mock_load_grid):
        """Returns empty GeoDataFrame if none of the requested tiles exist."""
        gdf = api_service.get_aq_data_for_tiles(["nonexistent_tile"], "berlin")
        assert gdf.empty
        assert set(gdf.columns) == {"tile_id", "raw_aqi", "pm2_5", "no2", "geometry"}
