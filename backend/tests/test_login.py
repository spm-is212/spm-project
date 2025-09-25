# import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils import security

client = TestClient(app)


# --- Dummy classes to fake Supabase responses ---
class DummyResult:
    def __init__(self, data):
        self.data = data


class DummySupabase:
    def __init__(self, data):
        self.client = self
        self._data = data

    def table(self, name): return self
    def select(self, *args, **kwargs): return self
    def eq(self, *args, **kwargs): return self
    def execute(self): return DummyResult(self._data)


# --- Tests ---
def test_login_success(monkeypatch):
    """User exists and password is correct -> should return token."""

    fake_user = [{
        "uuid": "1234-5678",
        "email": "admin@example.com",
        "password_hash": security.hash_password("supersecret"),
        "role": "admin"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
       data={"username": "admin@example.com", "password": "supersecret"}

    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_invalid_password(monkeypatch):
    """User exists but password is wrong -> should fail."""

    fake_user = [{
        "uuid": "1234-5678",
        "email": "admin@example.com",
        "password_hash": security.hash_password("supersecret"),
        "role": "admin"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "admin@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_user_not_found(monkeypatch):
    """No user with that email -> should fail."""

    fake_user = []  # empty DB result

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "ghost@example.com", "password": "irrelevant"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_logout():
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out (frontend should delete token)"}
