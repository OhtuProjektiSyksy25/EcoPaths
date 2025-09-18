""" Tests for main.py"""

from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_read_main():
    """ Test if GET to / status is 200 and content is:
    {"message": "Hello World"} """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_berlin():
    """ Test if GET to /berlin status is 200
        and response has correct berlin coordinates    
    """
    response = client.get("/berlin")
    assert response.status_code == 200
    assert response.json()["coordinates"] == [52.520008, 13.404954]
