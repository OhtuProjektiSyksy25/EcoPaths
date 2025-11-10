import pytest
import warnings
from unittest.mock import Mock
from fastapi.testclient import TestClient
from src.main import app


class MockAreaConfig:
    crs = "EPSG:25833"
    area = "test_area"
    bbox = [13.30, 52.46, 13.51, 52.59]
    focus_point = [13.404954, 52.520008]


@pytest.fixture
def setup_mock_lifespan():
    app.state.area_config = MockAreaConfig()
    app.state.route_service = Mock()
    app.state.selected_area = "test_area"
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_getroute_no_area_selected(client):
    client.app.state.area_config = None
    client.app.state.route_service = None

    response = client.post("/api/getroute", json={"features": []})
    assert response.status_code == 400
    assert response.json() == {
        "error": "No area selected. Please select an area first."}


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getroute_invalid_features_count(client):
    response = client.post(
        "/api/getroute", json={"features": [{"properties": {"role": "start"}}]})
    assert response.status_code == 400
    assert response.json() == {"error": "GeoJSON must contain two features"}


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getroute_missing_start_or_end(client):
    response = client.post("/api/getroute", json={
        "features": [
            {"properties": {"role": "end"}, "geometry": {}},
            {"properties": {"role": "start_missing"}, "geometry": {}}
        ]
    })
    assert response.status_code == 400
    assert response.json() == {"error": "Missing start or end feature"}


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getroute_invalid_balanced_weight(client):
    features = [
        {"properties": {"role": "start"}, "geometry": {}},
        {"properties": {"role": "end"}, "geometry": {}}
    ]
    response = client.post(
        "/api/getroute", json={"features": features, "balanced_weight": 1.5})
    assert response.status_code == 400
    assert response.json() == {
        "error": "balanced_weight must be a number between 0 and 1"}


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getroute_success(monkeypatch, client):
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    features = [
        {"properties": {"role": "start"}, "geometry": {
            "type": "Point", "coordinates": [0, 0]}},
        {"properties": {"role": "end"}, "geometry": {
            "type": "Point", "coordinates": [1, 1]}}
    ]

    mock_response = {
        "routes": {"fastest": {}, "best_aq": {}, "balanced": {}},
        "summaries": {"fastest": {}, "best_aq": {}, "balanced": {}}
    }

    class MockRouteService:
        def get_route(self, origin, dest, weight):
            return mock_response

    class MockGeoTransformer:
        @staticmethod
        def geojson_to_projected_gdf(geom, crs):
            return geom

    monkeypatch.setattr(
        "src.endpoints.routes.GeoTransformer", MockGeoTransformer)
    client.app.state.route_service = MockRouteService()

    response = client.post("/api/getroute", json={"features": features})
    assert response.status_code == 200
    assert response.json() == mock_response
