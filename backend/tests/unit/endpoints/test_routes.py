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
def test_getroute_missing_start(client):
    response = client.post("/api/getroute", json={
        "features": [
            {"properties": {"role": "end"}, "geometry": {}},
            {"properties": {"role": "start_missing"}, "geometry": {}}
        ],
    })
    assert response.status_code == 400
    assert response.json() == {"error": "Missing start feature"}


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


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getroute_calls_correct_function_according_to_balancedbool(monkeypatch, client):
    mock_service = Mock()
    mock_service.get_route.return_value = {"result": "ok"}
    mock_service.compute_balanced_route_only.return_value = {"result": "ok"}

    app.state.route_service = mock_service
    app.state.area_config = MockAreaConfig()
    monkeypatch.setattr(
        "src.endpoints.routes.GeoTransformer.geojson_to_projected_gdf", Mock())

    body = {
        "features": [
            {"type": "Feature", "properties": {"role": "start"},
                "geometry": {"type": "Point", "coordinates": [1, 2]}},
            {"type": "Feature", "properties": {"role": "end"},
                "geometry": {"type": "Point", "coordinates": [3, 4]}},
        ],
        "balanced_route": False,
        "balanced_weight": 0.5,
    }
    client.post("/api/getroute", json=body)

    mock_service.get_route.assert_called_once()
    mock_service.compute_balanced_route_only.assert_not_called()

    args, _ = mock_service.get_route.call_args
    assert len(args) == 3
    assert args[2] == 0.5
    mock_service.compute_balanced_route_only.assert_not_called()

    mock_service.reset_mock()

    new_body = {
        "features": [
            {"type": "Feature", "properties": {"role": "start"},
                "geometry": {"type": "Point", "coordinates": [1, 2]}},
            {"type": "Feature", "properties": {"role": "end"},
                "geometry": {"type": "Point", "coordinates": [3, 4]}},
        ],
        "balanced_route": True,
        "balanced_weight": 0.8,
    }

    client.post("/api/getroute", json=new_body)

    args, _ = mock_service.compute_balanced_route_only.call_args
    assert len(args) == 1
    assert args[0] == 0.8
    mock_service.get_route.assert_not_called()
    client.post("/api/getroute", json=new_body)
