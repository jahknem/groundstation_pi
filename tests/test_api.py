# tests/test_api.py
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"message": "Status requested"}
