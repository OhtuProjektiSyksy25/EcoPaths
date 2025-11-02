""" Tests for main.py"""

import pytest
import importlib
import httpx
import src.main

from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import Mock


class MockAreaConfig:
    """Create mock area config."""

    def __init__(self):
        self.bbox = [13.30, 52.46, 13.51, 52.59]
        self.crs = "EPSG:25833"
        self.area = "berlin"
        self.focus_point = [13.404954, 52.520008]


@pytest.fixture
def setup_mock_lifespan():
    """Set up mock lifespan."""
    app.state.area_config = MockAreaConfig()
    app.state.route_service = Mock()

    yield


client = TestClient(app)


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_berlin():
    """ Test if GET to /berlin status is 200
        and response has correct berlin coordinates.
    """
    response = client.get("/berlin")
    assert response.status_code == 200

    assert response.json()["coordinates"] == [13.404954, 52.520008]


@pytest.fixture
def create_index_html(tmp_path, monkeypatch):
    """Create a temporary build/index.html file for testing."""
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    index_file = build_dir / "index.html"
    index_file.write_text("<html>SPA</html>")
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def create_static_dir(tmp_path, monkeypatch):
    """Create a temporary build/static directory for testing."""
    static_dir = tmp_path / "build" / "static"
    static_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    yield


@pytest.mark.usefixtures("create_index_html")
def test_spa_handler_serves_index_html():
    """Test if the catch-all route serves index.html."""
    response = client.get("/some/random/path")
    assert response.status_code == 200
    assert response.text == "<html>SPA</html>"
    assert response.headers["content-type"].startswith("text/html")


def test_static_mount_not_present(monkeypatch):
    """Test that /static is not mounted if build/static does not exist."""
    monkeypatch.setattr("os.path.isdir", lambda path: False)

    importlib.reload(src.main)

    app = src.main.app
    routes = [route.path for route in app.routes]

    assert "/static" not in routes


@pytest.mark.usefixtures("create_static_dir")
def test_static_mount_present():
    """Test that /static is mounted if build/static does exist."""
    importlib.reload(src.main)

    app = src.main.app
    routes = [route.path for route in app.routes]

    assert "/static" in routes


def test_geocode_forward_too_short_value():
    """Test geocode_forward endpoint with too short value."""
    response = client.get("/api/geocode-forward/al")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_geocode_forward_valid_value(monkeypatch):
    """Test geocode_forward endpoint with valid value."""
    sample_response = {
        "features": [
            {
                "properties": {
                    "name": "Unter den Linden",
                    "city": "Berlin"
                },
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [13.3900, 52.5167]
                }
            }
        ]
    }

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def json(self):
                return sample_response

        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get("/api/geocode-forward/unt")
    suggestions = response.json()

    assert response.status_code == 200

    assert "features" in suggestions
    assert len(suggestions["features"]) == 1

    feature = suggestions["features"][0]

    assert feature["properties"]["name"] == "Unter den Linden"
    assert feature["properties"]["city"] == "Berlin"
    assert "full_address" in feature
    assert feature["full_address"] == "Unter den Linden Berlin "


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_geocode_forward_with_all_fields(monkeypatch):
    """Test geocode_forward endpoint with all fields present in response."""
    sample_response = {
        "features": [
            {
                "properties": {
                    "name": "Die Mitte",
                    "street": "Alexanderplatz",
                    "housenumber": "3",
                    "city": "Berlin"
                },
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [13.4132, 52.5219]
                }
            }
        ]
    }

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def json(self):
                return sample_response

        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get("/api/geocode-forward/unt")
    suggestions = response.json()

    assert response.status_code == 200

    assert "features" in suggestions
    assert len(suggestions["features"]) == 1

    feature = suggestions["features"][0]

    assert feature["properties"]["name"] == "Die Mitte"
    assert feature["properties"]["street"] == "Alexanderplatz"
    assert feature["properties"]["housenumber"] == "3"
    assert feature["properties"]["city"] == "Berlin"
    assert "full_address" in feature
    assert feature["full_address"] == "Die Mitte Alexanderplatz 3 Berlin "


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_geocode_forward_outside_bbox(monkeypatch):
    """Test geocode_forward endpoint with a value outside the bbox."""
    sample_response = {
        "features": []
    }

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def json(self):
                return sample_response

        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get("/api/geocode-forward/mannerheimintie")
    suggestions = response.json()

    assert response.status_code == 200
    assert "features" in suggestions
    assert len(suggestions["features"]) == 0


def test_geocode_forward_http_error(monkeypatch):
    """Test geocode_forward endpoint handling HTTP error."""
    async def mock_get(*args, **kwargs):
        mock_request = Mock()
        mock_request.url = "fake-url"

        error = httpx.HTTPError("HTTP error")
        error._request = mock_request
        raise error

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get("/api/geocode-forward/test")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_geocode_forward_check_photon_url(monkeypatch):
    """Test that the Photon URL is set correctly."""
    test_photon_url = None

    async def mock_get(self, url, *args, **kwargs):
        nonlocal test_photon_url
        test_photon_url = str(url)

        class MockResponse:
            def json(self):
                return {"features": []}
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get("/api/geocode-forward/alexander")

    assert response.status_code == 200
    assert test_photon_url is not None

    value = "alexander"
    bbox_str = "13.3,52.46,13.51,52.59"

    assert value in test_photon_url
    assert bbox_str in test_photon_url
    assert test_photon_url.startswith("https://photon.komoot.io/api/?q=")
    assert test_photon_url.endswith(f"{value}&limit=4&bbox={bbox_str}")
    assert test_photon_url == f"https://photon.komoot.io/api/?q={value}&limit=4&bbox={bbox_str}"


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_get_area_config_returns_correct_data():
    """Test that get_area_config returns the correct area configuration."""
    response = client.get("/get-area-config")

    assert response.status_code == 200

    data = response.json()

    assert data["area"] == "berlin"
    assert data["bbox"] == [13.30, 52.46, 13.51, 52.59]
    assert data["focus_point"] == [13.404954, 52.520008]
    assert data["crs"] == "EPSG:25833"
