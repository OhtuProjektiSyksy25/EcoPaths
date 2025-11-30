import pytest
import httpx
from unittest.mock import Mock
from src.main import app
from fastapi.testclient import TestClient


class MockAreaConfig:
    bbox = [13.30, 52.46, 13.51, 52.59]
    crs = "EPSG:25833"
    area = "berlin"
    focus_point = [13.404954, 52.520008]


@pytest.fixture
def setup_mock_lifespan():
    app.state.area_config = MockAreaConfig()
    app.state.route_service = Mock()
    app.state.selected_area = "berlin"
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _bbox_str():
    cfg = app.state.area_config
    return ",".join(map(str, cfg.bbox))


def test_geocode_forward_too_short_value(client, setup_mock_lifespan):
    response = client.get(f"/api/geocode-forward/al?bbox={_bbox_str()}")
    assert response.status_code == 200
    assert response.json() == []


def test_geocode_forward_valid_value(client, setup_mock_lifespan, monkeypatch):
    sample_response = {
        "features": [
            {
                "properties": {"name": "Unter den Linden", "city": "Berlin"},
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [13.3900, 52.5167]}
            }
        ]
    }

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def json(self):
                return sample_response
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get(f"/api/geocode-forward/unt?bbox={_bbox_str()}")
    suggestions = response.json()

    assert response.status_code == 200
    assert "features" in suggestions
    assert len(suggestions["features"]) == 1
    feature = suggestions["features"][0]
    assert feature["properties"]["name"] == "Unter den Linden"
    assert feature["properties"]["city"] == "Berlin"
    assert "full_address" in feature
    assert feature["full_address"].strip() == "Unter den Linden Berlin"


def test_geocode_forward_with_all_fields(client, setup_mock_lifespan, monkeypatch):
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
                "geometry": {"type": "Point", "coordinates": [13.4132, 52.5219]}
            }
        ]
    }

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def json(self):
                return sample_response
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get(f"/api/geocode-forward/unt?bbox={_bbox_str()}")
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
    assert feature["full_address"].strip(
    ) == "Die Mitte Alexanderplatz 3 Berlin"


def test_geocode_forward_outside_bbox(client, setup_mock_lifespan, monkeypatch):
    sample_response = {"features": []}

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def json(self):
                return sample_response
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get(
        f"/api/geocode-forward/mannerheimintie?bbox={_bbox_str()}")
    suggestions = response.json()
    assert response.status_code == 200
    assert "features" in suggestions
    assert len(suggestions["features"]) == 0


def test_geocode_forward_http_error(client, monkeypatch, setup_mock_lifespan):
    async def mock_get(*args, **kwargs):
        mock_request = Mock()
        mock_request.url = "fake-url"
        error = httpx.HTTPError("HTTP error")
        error._request = mock_request
        raise error

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = client.get(f"/api/geocode-forward/test?bbox={_bbox_str()}")
    assert response.status_code == 200
    assert response.json() == []


def test_geocode_forward_check_photon_url(client, setup_mock_lifespan, monkeypatch):
    test_photon_url = None

    async def mock_get(self, url, *args, **kwargs):
        nonlocal test_photon_url
        test_photon_url = str(url)

        class MockResponse:
            def json(self):
                return {"features": []}
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    value = "alexander"
    response = client.get(f"/api/geocode-forward/{value}?bbox={_bbox_str()}")

    assert response.status_code == 200
    assert test_photon_url is not None

    bbox_str = "13.3,52.46,13.51,52.59"

    assert value in test_photon_url
    assert bbox_str in test_photon_url
    assert test_photon_url.startswith("https://photon.komoot.io/api/?q=")
    assert test_photon_url.endswith(f"{value}&limit=4&bbox={bbox_str}")
    assert test_photon_url == f"https://photon.komoot.io/api/?q={value}&limit=4&bbox={bbox_str}"
