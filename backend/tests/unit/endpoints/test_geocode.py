import pytest
import httpx
from unittest.mock import Mock
from src.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)


def test_geocode_forward_too_short_value(client):
    response = client.get("/api/geocode-forward/al?bbox=1,2,3,4")
    assert response.status_code == 200
    assert response.json() == []


def test_geocode_forward_missing_bbox(client):
    """No bbox → empty result"""
    response = client.get("/api/geocode-forward/alex")
    assert response.status_code == 200
    assert response.json() == []


def test_geocode_forward_valid_value(monkeypatch, client):
    sample_response = {
        "features": [
            {
                "properties": {"name": "Unter den Linden", "city": "Berlin"},
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [13.39, 52.5167]},
            }
        ]
    }

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def json(self):
                return sample_response
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get("/api/geocode-forward/unt?bbox=1,2,3,4")

    assert response.status_code == 200
    js = response.json()
    assert len(js["features"]) == 1
    f = js["features"][0]
    assert "full_address" in f
    assert f["properties"]["name"] == "Unter den Linden"


def test_geocode_forward_http_error(monkeypatch, client):
    async def mock_get(*args, **kwargs):
        raise httpx.HTTPError("HTTP fail")

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get("/api/geocode-forward/test?bbox=1,2,3,4")
    assert response.status_code == 200
    assert response.json() == []


def test_geocode_forward_photon_url_correct(monkeypatch, client):
    captured_url = None

    async def mock_get(self, url, *args, **kwargs):
        nonlocal captured_url
        captured_url = url

        class MockResponse:
            def json(self):
                return {"features": []}

        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get(
        "/api/geocode-forward/alexander?bbox=13.3,52.46,13.51,52.59")
    assert response.status_code == 200

    assert captured_url is not None
    assert "alexander" in captured_url
    assert "bbox=13.3,52.46,13.51,52.59" in captured_url
    assert captured_url.startswith("https://photon.komoot.io/api/")
