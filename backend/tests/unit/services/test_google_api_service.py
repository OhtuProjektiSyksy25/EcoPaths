"""
Unit tests for Google API service.
"""

import pytest
from unittest.mock import Mock, patch
from src.services.google_api_service import GoogleAPIService

class TestGoogleAPIServices:
    """Unit tests for Google API service."""
    @pytest.fixture
    def mock_api_key(self, monkeypatch):
        """Mock API key for testing."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test_api_key")

    @pytest.fixture
    def api_service(self, mock_api_key):
        """Create instance with mocked API key"""
        return GoogleAPIService()

    def test_init_with_api_key(self, mock_api_key):
        """Test successful initialization with API key"""
        service = GoogleAPIService()
        assert service.api_key == "test_api_key"
        assert service.endpoint == "https://airquality.googleapis.com/v1/currentConditions:lookup"

    def test_init_without_api_key(self, monkeypatch):
        """Test fail without API key"""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with pytest.raises(ValueError, match="GOOGLE_API_KEY not found in .env file"):
            GoogleAPIService()

    @patch("src.services.google_api_service.requests.post")
    def test_get_current_conditions_success(self, mock_post, api_service):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dateTime": "2025-10-17T12:00:00Z",
            "regionCode": "de",
            "indexes": [
                {
                    "code": "uaqi",
                    "displayName": "Universal AQI",
                    "aqi": 45,
                    "aqiDisplay": "45",
                    "color": {"green": 230, "red": 123, "blue": 0},
                    "category": "Good air quality",
                    "dominantPollutant": "pm25"
                }
            ]
        }
        mock_post.return_value = mock_response

        # make request
        result = api_service.get_current_conditions(52.52, 13.405)

        # assertions
        assert result is not None
        assert result["regionCode"] == "de"
        assert result["indexes"][0]["aqi"] == 45


        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args.kwargs["json"] == {
            "location": {"latitude": 52.52, "longitude": 13.405}
        }
        assert call_args.kwargs["params"] == {"key": "test_api_key"}
        assert call_args.kwargs["headers"] == {"Content-Type": "application/json"}
