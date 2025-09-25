""" Tests for main.py"""

import pytest

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

@pytest.fixture(autouse=True)
def create_index_html(tmp_path, monkeypatch):
    """ Create a temporary build/index.html file for testing """
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    index_file = build_dir / "index.html"
    index_file.write_text("<html>SPA</html>")
    monkeypatch.chdir(tmp_path)
    yield

def test_spa_handler_serves_index_html():
    """ Test if the catch-all route serves index.html """
    response = client.get("/some/random/path")
    assert response.status_code == 200
    assert response.text == "<html>SPA</html>"
    assert response.headers["content-type"].startswith("text/html")