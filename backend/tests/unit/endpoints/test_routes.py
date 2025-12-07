import pytest
import warnings
from unittest.mock import Mock
from fastapi.testclient import TestClient
from src.main import app

warnings.filterwarnings("ignore", category=DeprecationWarning, module="pyproj")


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

    # Test with balanced_route=True
    mock_service.reset_mock()
    new_body = body.copy()
    new_body["balanced_route"] = True
    new_body["balanced_weight"] = 0.8

    client.post("/api/getroute", json=new_body)
    mock_service.compute_balanced_route_only.assert_called_once_with(0.8)
    mock_service.get_route.assert_not_called()


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getloop_stream_no_area_selected(client):
    client.app.state.area_config = None

    response = client.get(
        "/api/getloop/stream?lat=52.52&lon=13.40&distance=2.5")
    assert response.status_code == 400
    assert response.json() == {"error": "No area selected."}


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getloop_stream_success(monkeypatch, client):
    """Test successful SSE stream with three loop variants."""

    class MockLoopRouteService:
        def __init__(self, area):
            self.area = area

        def get_round_trip(self, origin_gdf, distance_m):
            for i in range(1, 4):
                loop_key = f"loop{i}"
                yield {
                    "routes": {loop_key: {"type": "FeatureCollection", "features": [{}]}},
                    "summaries": {loop_key: {"distance": 2500 + i * 100, "duration": 600 + i*50, "aq_average": 50+i}}
                }

    monkeypatch.setattr(
        "endpoints.routes.LoopRouteService", MockLoopRouteService
    )

    response = client.get(
        "/api/getloop/stream?lat=52.52&lon=13.40&distance=2.5")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    content = response.text
    assert 'event: loop' in content
    assert 'event: complete' in content


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getloop_stream_loop_error(monkeypatch, client):
    """Test handling of error emitted by service."""

    class MockLoopRouteService:
        def __init__(self, area):
            self.area = area

        def get_round_trip(self, origin_gdf, distance_m):
            raise RuntimeError("Test loop-error")

    monkeypatch.setattr(
        "endpoints.routes.LoopRouteService", MockLoopRouteService
    )

    response = client.get(
        "/api/getloop/stream?lat=52.52&lon=13.40&distance=2.5")
    assert response.status_code == 200
    content = response.text
    assert 'event: error' in content
    assert 'Test loop-error' in content


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getloop_stream_general_error(monkeypatch, client):
    """Test that unexpected exceptions emit event: error."""

    class MockLoopRouteService:
        def __init__(self, area):
            self.area = area

        def get_round_trip(self, origin_gdf, distance_m):
            raise ValueError("Unexpected bug")

    monkeypatch.setattr(
        "endpoints.routes.LoopRouteService", MockLoopRouteService
    )

    response = client.get(
        "/api/getloop/stream?lat=52.52&lon=13.40&distance=2.5")
    content = response.text
    assert 'event: error' in content
    assert 'Internal error while computing loops' in content


@pytest.mark.usefixtures("setup_mock_lifespan")
def test_getloop_stream_distance_capping(monkeypatch, client):
    """Test that distance is capped at 10km."""

    captured_distance = {}

    class MockLoopRouteService:
        def __init__(self, area):
            self.area = area

        def get_round_trip(self, origin_gdf, distance_m):
            captured_distance['value'] = distance_m
            yield {"routes": {"loop1": {"type": "FeatureCollection", "features": []}},
                   "summaries": {"loop1": {"distance": 2500}}}

    monkeypatch.setattr(
        "endpoints.routes.LoopRouteService", MockLoopRouteService
    )

    client.get("/api/getloop/stream?lat=52.52&lon=13.40&distance=10")
    assert captured_distance['value'] == 10000
