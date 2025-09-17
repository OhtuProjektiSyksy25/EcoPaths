from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_berlin():
    response = client.get("/berlin")
    assert response.status_code == 200
    assert response.json()["coordinates"] == [52.520008, 13.404954]