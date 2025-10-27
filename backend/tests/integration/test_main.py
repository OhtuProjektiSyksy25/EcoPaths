""" Tests for main.py"""

import pytest
import importlib
import httpx
import src.main

from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import Mock


class MockAreaConfig:
    """Create mock area config"""

    def __init__(self):
        self.bbox = [13.30, 52.46, 13.51, 52.59]
        self.crs = "EPSG:25833"
        self.area = "berlin"


@pytest.fixture
def setup_mock_lifespan():
    """Set up mock lifespan"""
    app.state.area_config = MockAreaConfig()
    app.state.route_service = Mock()

    yield


client = TestClient(app)


def test_berlin():
    """ Test if GET to /berlin status is 200
        and response has correct berlin coordinates    
    """
    response = client.get("/berlin")
    assert response.status_code == 200

    assert response.json()["coordinates"] == [13.404954, 52.520008]


@pytest.fixture
def create_index_html(tmp_path, monkeypatch):
    """ Create a temporary build/index.html file for testing """
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    index_file = build_dir / "index.html"
    index_file.write_text("<html>SPA</html>")
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def create_static_dir(tmp_path, monkeypatch):
    """ Create a temporary build/static directory for testing """
    static_dir = tmp_path / "build" / "static"
    static_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    yield


@pytest.mark.usefixtures("create_index_html")
def test_spa_handler_serves_index_html():
    """ Test if the catch-all route serves index.html """
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
    """ Test geocode_forward endpoint with too short value """
    response = client.get("/api/geocode-forward/al")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_geocode_forward_valid_value(monkeypatch):
    """ Test geocode_forward endpoint with valid value """
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


def test_geocode_forward_http_error(monkeypatch):
    """ Test geocode_forward endpoint handling HTTP error """

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
