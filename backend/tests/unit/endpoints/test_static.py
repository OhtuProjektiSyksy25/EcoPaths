"""
Test for the static SPA handler endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import create_app, lifespan_context
from src.endpoints import static


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app(lifespan_context)
    return TestClient(app)


def test_spa_handler_cache_control_headers(client, tmp_path, monkeypatch):
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "index.html").write_text("<html></html>")

    monkeypatch.setattr(static, "ROOT_DIR", tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["expires"] == "0"