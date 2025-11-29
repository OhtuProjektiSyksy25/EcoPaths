import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from src.main import app

# Import the module where getroute is defined so monkeypatch paths match
import src.endpoints.routes as routes_module


@pytest.fixture
def client():
    return TestClient(app)


def test_getroute_missing_required_fields(client):
    """Missing area or wrong number of features -> 400"""
    response = client.post("/api/getroute", json={"features": []})
    assert response.status_code == 400
    assert response.json() == {"error": "Missing required fields"}


def test_getroute_invalid_balanced_weight(client):
    """balanced_weight must be 0..1"""
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
