import pytest
from fastapi.testclient import TestClient
from main import app, create_access_token
from datetime import timedelta

@pytest.fixture
def client():
    return TestClient(app)

def get_token():
    # Replace 'testuser' with a username you control in your system or mock appropriately
    return create_access_token({"sub": "testuser"}, expires_delta=timedelta(minutes=15))

def test_login_for_access_token(client):
    response = client.post("/token", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_protected_route(client):
    token = get_token()
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "message" in response.json()

def test_admin_route_forbidden(client):
    token = get_token()
    response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (403, 401)

# More tests for coverage (missing/expired/invalid tokens etc.) can be added here.
