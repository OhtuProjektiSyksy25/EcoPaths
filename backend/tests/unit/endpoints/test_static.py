"""
Test for the static SPA handler endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import create_app, lifespan_context
import os


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app(lifespan_context)
    return TestClient(app)


def test_spa_handler_cache_control_headers(client, tmp_path):
    """
    Test that SPA handler serves index.html with proper no-cache headers.
    """
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    index_file = build_dir / "index.html"
    index_file.write_text("<html></html>")

    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        response = client.get("/")

    finally:
        os.chdir(cwd)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["expires"] == "0"