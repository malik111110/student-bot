from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_professors():
    response = client.get("/api/v1/professors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "name" in data[0]
    assert "email" in data[0]

def test_get_courses():
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "name" in data[0]
    assert "code" in data[0]

def test_get_schedule():
    response = client.get("/api/v1/schedule")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "monday" in data
