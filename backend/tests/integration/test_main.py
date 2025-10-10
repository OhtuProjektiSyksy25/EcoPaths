""" Tests for main.py"""

import pytest
import importlib
import src.main

from fastapi.testclient import TestClient
from src.main import app

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


def test_getroute(monkeypatch):
    """Test GET /getroute/{from_coords}/{to_coords} returns mocked route"""

    def mock_get_route(self, from_tuple, to_tuple):
        assert from_tuple == (24.94, 60.17)
        assert to_tuple == (13.40, 52.52)
        return ["mocked_route_point1", "mocked_route_point2"]

    monkeypatch.setattr("services.route_service.RouteService.get_route", mock_get_route)

    response = client.get("/getroute/24.94,60.17/13.40,52.52")
    assert response.status_code == 200
    data = response.json()
    assert "route" in data
    assert data["route"] == ["mocked_route_point1", "mocked_route_point2"]
