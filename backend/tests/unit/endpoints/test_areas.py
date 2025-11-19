import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from src.app import create_app, lifespan_context


class MockAreaConfig:
    area = "berlin"
    bbox = [13.30, 52.46, 13.51, 52.59]
    focus_point = [13.404954, 52.520008]
    crs = "EPSG:25833"


@pytest.fixture
def setup_mock_lifespan():
    app = create_app(lifespan_context)
    app.state.area_config = MockAreaConfig()
    app.state.route_service = Mock()
    app.state.selected_area = "berlin"
    yield app  # palautetaan app fixtureksi


@pytest.fixture
def client(setup_mock_lifespan):
    return TestClient(setup_mock_lifespan)


def test_get_areas_returns_list(client):
    response = client.get("/api/areas")
    assert response.status_code == 200
    data = response.json()
    assert "areas" in data
    assert isinstance(data["areas"], list)
    assert len(data["areas"]) > 0


def test_select_area_success(client, monkeypatch):
    class MockRouteService:
        pass

    class MockAreaConfigInner:
        area = "berlin"
        bbox = [13.30, 52.46, 13.51, 52.59]
        focus_point = [13.404954, 52.520008]
        crs = "EPSG:25833"

    def mock_from_area(area_id):
        return MockRouteService(), MockAreaConfigInner()

    monkeypatch.setattr(
        "services.route_service.RouteServiceFactory.from_area",
        mock_from_area
    )

    response = client.post("/api/select-area/berlin")
    assert response.status_code == 200
    assert response.json() == "berlin"

    assert isinstance(client.app.state.route_service, MockRouteService)
    assert client.app.state.area_config.area == "berlin"
    assert client.app.state.selected_area == "berlin"


def test_select_area_invalid_area(client):
    response = client.post("/api/select-area/unknown")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "Area not found"


def test_get_area_config_returns_correct_data(client):
    client.app.state.area_config = MockAreaConfig()
    response = client.get("/api/get-area-config")
    assert response.status_code == 200
    data = response.json()
    assert data["area"] == "berlin"
    assert data["bbox"] == [13.30, 52.46, 13.51, 52.59]
    assert data["focus_point"] == [13.404954, 52.520008]
    assert data["crs"] == "EPSG:25833"


def test_get_area_config_no_selection(client):
    client.app.state.area_config = None
    response = client.get("/api/get-area-config")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "No area selected. Please select an area first."
