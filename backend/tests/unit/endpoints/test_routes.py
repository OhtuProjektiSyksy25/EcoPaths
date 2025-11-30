import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from src.main import app

import src.endpoints.routes as routes_module


@pytest.fixture
def client():
    return TestClient(app)


def test_getroute_missing_required_fields(client):
    response = client.post("/api/getroute", json={"features": []})
    assert response.status_code == 400
    assert response.json() == {
        "error": "Missing required fields: 'area' or two 'features'"}


def test_getroute_invalid_balanced_weight(client):
    body = {
        "area": "berlin",
        "features": [
            {"properties": {"role": "start"}, "geometry": {}},
            {"properties": {"role": "end"}, "geometry": {}},
        ],
        "balanced_weight": -1.5,
    }

    response = client.post("/api/getroute", json=body)
    assert response.status_code == 400
    assert response.json() == {
        "error": "balanced_weight must be a number between 0 and 1"
    }


def test_getroute_missing_start_or_end_feature(client):
    body = {
        "area": "berlin",
        "features": [
            {"properties": {"role": "start_missing"}, "geometry": {}},
            {"properties": {"role": "end"}, "geometry": {}},
        ],
    }

    response = client.post("/api/getroute", json=body)
    assert response.status_code == 400
    assert response.json() == {"error": "Missing start or end feature"}


def test_getroute_route_service_chain(monkeypatch, client):

    class MockAreaConfig:
        crs = "EPSG:25833"

    class MockRouteService:
        def get_route(self, origin, dest, weight):
            return {"routes": {"fastest": {}}, "summaries": {"fastest": {}}}

    def mock_from_area(area):
        return MockRouteService(), MockAreaConfig()

    monkeypatch.setattr(
        routes_module.RouteServiceFactory,
        "from_area",
        staticmethod(mock_from_area)
    )

    class MockGeoTransformer:
        @staticmethod
        def geojson_to_projected_gdf(geom, crs):
            return {"mock": geom}

    monkeypatch.setattr(
        routes_module,
        "GeoTransformer",
        MockGeoTransformer
    )

    body = {
        "area": "berlin",
        "balanced_weight": 0.5,
        "features": [
            {
                "properties": {"role": "start"},
                "geometry": {"type": "Point", "coordinates": [0, 0]},
            },
            {
                "properties": {"role": "end"},
                "geometry": {"type": "Point", "coordinates": [1, 1]},
            },
        ],
    }

    response = client.post("/api/getroute", json=body)

    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert "summaries" in data
    assert "fastest" in data["routes"]


def test_getroute_calls_get_route_correctly(monkeypatch, client):
    """New behavior: always calls get_route(), never compute_balanced_route_only()."""

    # --- Mock area_config + service returned by factory ---
    class MockAreaConfig:
        crs = "EPSG:25833"

    mock_service = Mock()
    mock_service.get_route.return_value = {"ok": True}

    def mock_from_area(area):
        return mock_service, MockAreaConfig()

    monkeypatch.setattr(
        routes_module.RouteServiceFactory,
        "from_area",
        staticmethod(mock_from_area)
    )

    # --- Mock GeoTransformer ---
    class MockGT:
        @staticmethod
        def geojson_to_projected_gdf(geom, crs):
            return geom  # passthrough

    monkeypatch.setattr(routes_module, "GeoTransformer", MockGT)

    body = {
        "area": "berlin",
        "balanced_weight": 0.7,
        "features": [
            {"properties": {"role": "start"},
             "geometry": {"type": "Point", "coordinates": [5, 5]}},
            {"properties": {"role": "end"},
             "geometry": {"type": "Point", "coordinates": [6, 6]}},
        ]
    }

    response = client.post("/api/getroute", json=body)

    assert response.status_code == 200

    # Ensure correct function was called
    mock_service.get_route.assert_called_once()

    args, kwargs = mock_service.get_route.call_args
    assert len(args) == 3
    assert args[2] == 0.7   # balanced_weight forwarded properly
