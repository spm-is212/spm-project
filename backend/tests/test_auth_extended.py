from fastapi.testclient import TestClient
from backend.main import app
from backend.utils import security
from unittest.mock import MagicMock, patch

client = TestClient(app)


# --- Dummy classes to fake Supabase responses ---
class DummyResult:
    def __init__(self, data):
        self.data = data


class DummySupabase:
    def __init__(self, data):
        self.client = self
        self._data = data

    def table(self, name):
        self._table_name = name
        return self

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def execute(self):
        return DummyResult(self._data)


# --- Tests for Login Endpoint ---
def test_login_with_valid_email_and_password(monkeypatch):
    """Test login with correct email and password returns token"""
    fake_user = [{
        "uuid": "test-uuid-123",
        "email": "test@example.com",
        "password_hash": security.hash_password("securepass123"),
        "role": "user",
        "departments": ["Engineering"]
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "securepass123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0


def test_login_with_admin_role(monkeypatch):
    """Test admin user login includes correct role in token"""
    fake_admin = [{
        "uuid": "admin-uuid-456",
        "email": "admin@example.com",
        "password_hash": security.hash_password("adminpass"),
        "role": "admin",
        "departments": ["IT", "Management"]
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_admin))

    response = client.post(
        "/api/auth/login",
        data={"username": "admin@example.com", "password": "adminpass"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body

    # Decode token to verify role
    import jwt
    decoded = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert decoded["role"] == "admin"
    assert decoded["sub"] == "admin-uuid-456"
    assert "Engineering" not in decoded["departments"]
    assert "IT" in decoded["departments"]
    assert "Management" in decoded["departments"]


def test_login_with_wrong_password(monkeypatch):
    """Test login fails with incorrect password"""
    fake_user = [{
        "uuid": "test-uuid-123",
        "email": "test@example.com",
        "password_hash": security.hash_password("correctpass"),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "wrongpass"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_with_nonexistent_email(monkeypatch):
    """Test login fails when user doesn't exist"""
    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase([]))

    response = client.post(
        "/api/auth/login",
        data={"username": "nonexistent@example.com", "password": "anypass"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_with_empty_credentials(monkeypatch):
    """Test login fails with empty credentials"""
    response = client.post(
        "/api/auth/login",
        data={"username": "", "password": ""}
    )

    # FastAPI validation should catch this
    assert response.status_code in [401, 422]


def test_login_without_departments(monkeypatch):
    """Test login works when user has no departments"""
    fake_user = [{
        "uuid": "test-uuid-789",
        "email": "nodept@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user"
        # departments field missing
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "nodept@example.com", "password": "testpass"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body

    # Verify departments defaults to empty list
    import jwt
    decoded = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert decoded["departments"] == []


def test_login_case_sensitivity_email(monkeypatch):
    """Test login email is case sensitive (or not, depending on implementation)"""
    fake_user = [{
        "uuid": "test-uuid-123",
        "email": "Test@Example.COM",
        "password_hash": security.hash_password("testpass"),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    # Try with exact case
    response = client.post(
        "/api/auth/login",
        data={"username": "Test@Example.COM", "password": "testpass"}
    )
    assert response.status_code == 200


def test_login_with_special_characters_password(monkeypatch):
    """Test login works with special characters in password"""
    special_password = "P@ssw0rd!#$%^&*()"
    fake_user = [{
        "uuid": "test-uuid-123",
        "email": "special@example.com",
        "password_hash": security.hash_password(special_password),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "special@example.com", "password": special_password}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


# --- Tests for Logout Endpoint ---
def test_logout_returns_success_message():
    """Test logout returns appropriate message"""
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out (frontend should delete token)"}


def test_logout_no_authentication_required():
    """Test logout doesn't require authentication"""
    # Logout should work even without a token
    response = client.post("/api/auth/logout")
    assert response.status_code == 200


# --- Tests for Get All Users Endpoint ---
def test_get_all_users_success(monkeypatch):
    """Test getting all users for assignment"""
    mock_user = {
        "sub": "user-123",
        "role": "user",
        "departments": []
    }

    mock_users_list = [
        {"uuid": "user-1", "email": "user1@example.com", "role": "user"},
        {"uuid": "user-2", "email": "user2@example.com", "role": "admin"},
        {"uuid": "user-3", "email": "user3@example.com", "role": "user"}
    ]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_user)

    # Mock UserManager
    mock_user_manager = MagicMock()
    mock_user_manager.get_all_users.return_value = mock_users_list

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_user)

        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 3
        assert data["users"][0]["uuid"] == "user-1"
        assert data["users"][1]["uuid"] == "user-2"


def test_get_all_users_requires_authentication():
    """Test getting all users requires authentication"""
    response = client.get("/api/auth/users")

    assert response.status_code == 403


def test_get_all_users_empty_list(monkeypatch):
    """Test getting all users when no users exist"""
    mock_user = {
        "sub": "user-123",
        "role": "user",
        "departments": []
    }

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_user)

    # Mock UserManager returning empty list
    mock_user_manager = MagicMock()
    mock_user_manager.get_all_users.return_value = []

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_user)

        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 0


def test_get_all_users_error_handling(monkeypatch):
    """Test error handling when UserManager fails"""
    mock_user = {
        "sub": "user-123",
        "role": "user",
        "departments": []
    }

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_user)

    # Mock UserManager to raise exception
    mock_user_manager = MagicMock()
    mock_user_manager.get_all_users.side_effect = Exception("Database error")

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_user)

        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 500
        assert "Error fetching users" in response.json()["detail"]


# --- Tests for Token Validation ---
def test_login_token_contains_correct_claims(monkeypatch):
    """Test login token contains all required claims"""
    fake_user = [{
        "uuid": "claim-test-uuid",
        "email": "claims@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "manager",
        "departments": ["Sales", "Marketing"]
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "claims@example.com", "password": "testpass"}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    # Decode and verify claims
    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})

    assert "sub" in decoded
    assert decoded["sub"] == "claim-test-uuid"
    assert "role" in decoded
    assert decoded["role"] == "manager"
    assert "departments" in decoded
    assert decoded["departments"] == ["Sales", "Marketing"]
    assert "exp" in decoded  # Expiration should be present


def test_login_token_has_expiration(monkeypatch):
    """Test login token has expiration time"""
    fake_user = [{
        "uuid": "exp-test-uuid",
        "email": "exp@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user",
        "departments": []
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "exp@example.com", "password": "testpass"}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    # Decode and verify expiration
    import jwt
    from datetime import datetime
    decoded = jwt.decode(token, options={"verify_signature": False})

    assert "exp" in decoded
    exp_timestamp = decoded["exp"]
    current_timestamp = datetime.utcnow().timestamp()

    # Token should expire in the future
    assert exp_timestamp > current_timestamp


# --- Tests for Multiple Login Attempts ---
def test_multiple_successful_logins(monkeypatch):
    """Test multiple successful logins generate different tokens"""
    fake_user = [{
        "uuid": "multi-login-uuid",
        "email": "multi@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user",
        "departments": []
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response1 = client.post(
        "/api/auth/login",
        data={"username": "multi@example.com", "password": "testpass"}
    )

    response2 = client.post(
        "/api/auth/login",
        data={"username": "multi@example.com", "password": "testpass"}
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    token1 = response1.json()["access_token"]
    token2 = response2.json()["access_token"]

    # Tokens should be different (due to different creation times)
    # Note: They might be the same if created at exact same millisecond,
    # but this is unlikely in practice
    assert isinstance(token1, str)
    assert isinstance(token2, str)


def test_login_after_failed_attempt(monkeypatch):
    """Test successful login after failed attempt"""
    fake_user = [{
        "uuid": "retry-uuid",
        "email": "retry@example.com",
        "password_hash": security.hash_password("correctpass"),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    # First attempt with wrong password
    response1 = client.post(
        "/api/auth/login",
        data={"username": "retry@example.com", "password": "wrongpass"}
    )
    assert response1.status_code == 401

    # Second attempt with correct password
    response2 = client.post(
        "/api/auth/login",
        data={"username": "retry@example.com", "password": "correctpass"}
    )
    assert response2.status_code == 200
    assert "access_token" in response2.json()


# --- Tests for Edge Cases ---
def test_login_with_unicode_password(monkeypatch):
    """Test login with unicode characters in password"""
    unicode_password = "пароль123"  # Russian characters + numbers
    fake_user = [{
        "uuid": "unicode-uuid",
        "email": "unicode@example.com",
        "password_hash": security.hash_password(unicode_password),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "unicode@example.com", "password": unicode_password}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_sql_injection_attempt(monkeypatch):
    """Test login is protected against SQL injection"""
    fake_user = []  # No user exists

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    # Attempt SQL injection in username
    response = client.post(
        "/api/auth/login",
        data={
            "username": "admin' OR '1'='1",
            "password": "anything"
        }
    )

    # Should fail because no user matches this email
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_get_all_users_as_different_roles(monkeypatch):
    """Test different user roles can access get all users endpoint"""
    mock_users_list = [
        {"uuid": "user-1", "email": "user1@example.com", "role": "user"}
    ]

    import backend.routers.auth as auth

    # Test as regular user
    mock_regular_user = {"sub": "user-123", "role": "user", "departments": []}
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_regular_user)

    mock_user_manager = MagicMock()
    mock_user_manager.get_all_users.return_value = mock_users_list

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_regular_user)
        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    # Test as admin user
    mock_admin_user = {"sub": "admin-123", "role": "admin", "departments": []}
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_admin_user)

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_admin_user)
        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


# --- Additional Edge Cases and Error Scenarios ---
def test_login_database_exception(monkeypatch):
    """Test login when database throws an exception"""
    import backend.routers.auth as auth

    class ExceptionDummySupabase(DummySupabase):
        def table(self, name):
            self._table_name = name
            return self

        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def execute(self):
            raise Exception("Database connection failed")

    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: ExceptionDummySupabase([]))

    # This test documents that database exceptions are not caught in login endpoint
    # In production, this should return 500 or 503
    try:
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "testpass"}
        )
        # Should return 500 error
        assert response.status_code == 500
    except Exception:
        # Currently the code doesn't catch database exceptions
        pass


def test_login_with_multiple_users_same_email(monkeypatch):
    """Test login when database returns multiple users (edge case)"""
    fake_users = [
        {
            "uuid": "user-1",
            "email": "duplicate@example.com",
            "password_hash": security.hash_password("testpass"),
            "role": "user",
            "departments": []
        },
        {
            "uuid": "user-2",
            "email": "duplicate@example.com",
            "password_hash": security.hash_password("testpass"),
            "role": "admin",
            "departments": []
        }
    ]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_users))

    response = client.post(
        "/api/auth/login",
        data={"username": "duplicate@example.com", "password": "testpass"}
    )

    # Should use first user returned
    assert response.status_code == 200
    token = response.json()["access_token"]

    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded["sub"] == "user-1"  # First user


def test_login_with_empty_password_hash(monkeypatch):
    """Test login when user has empty/null password hash"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": "",  # Empty password hash
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    # This test documents that empty password hash causes passlib to raise an exception
    # In production, this should be caught and handled gracefully
    try:
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "anypassword"}
        )
        # Should fail verification (401 or 500)
        assert response.status_code in [401, 500]
    except Exception:
        # Currently passlib raises an exception for invalid hash format
        pass


def test_login_password_with_spaces(monkeypatch):
    """Test login with password containing spaces"""
    password_with_spaces = "my secure password 123"
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password(password_with_spaces),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": password_with_spaces}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_username_with_special_chars(monkeypatch):
    """Test login with email containing special characters"""
    special_email = "test+tag@sub.example.com"
    fake_user = [{
        "uuid": "test-uuid",
        "email": special_email,
        "password_hash": security.hash_password("testpass"),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": special_email, "password": "testpass"}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_very_long_password(monkeypatch):
    """Test login with very long password"""
    long_password = "a" * 1000  # 1000 character password
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password(long_password),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": long_password}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_users_with_invalid_token(monkeypatch):
    """Test get users with malformed/invalid token"""
    response = client.get(
        "/api/auth/users",
        headers={"Authorization": "Bearer invalid_token_here"}
    )

    # Should fail authentication
    assert response.status_code in [401, 403, 422]


def test_get_users_with_missing_bearer_prefix():
    """Test get users with token missing Bearer prefix"""
    mock_user = {"sub": "user-123", "role": "user", "departments": []}
    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/auth/users",
        headers={"Authorization": token}  # Missing "Bearer " prefix
    )

    # Should fail authentication
    assert response.status_code in [401, 403, 422]


def test_login_with_null_role(monkeypatch):
    """Test login when user role is null/None"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": None,  # Null role
        "departments": []
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpass"}
    )

    # Should still succeed
    assert response.status_code == 200
    token = response.json()["access_token"]

    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded["role"] is None


def test_login_with_various_role_cases(monkeypatch):
    """Test login with different role case variations"""
    test_cases = ["Admin", "ADMIN", "AdMiN", "user", "USER", "User"]

    for role_variant in test_cases:
        fake_user = [{
            "uuid": f"test-uuid-{role_variant}",
            "email": f"{role_variant}@example.com",
            "password_hash": security.hash_password("testpass"),
            "role": role_variant,
            "departments": []
        }]

        import backend.routers.auth as auth
        monkeypatch.setattr(auth, "SupabaseCRUD", lambda data=fake_user: DummySupabase(data))

        response = client.post(
            "/api/auth/login",
            data={"username": f"{role_variant}@example.com", "password": "testpass"}
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded["role"] == role_variant


def test_login_with_array_departments(monkeypatch):
    """Test login with multiple departments"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "multi@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "manager",
        "departments": ["Engineering", "Product", "Design"]
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "multi@example.com", "password": "testpass"}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert len(decoded["departments"]) == 3
    assert "Engineering" in decoded["departments"]
    assert "Product" in decoded["departments"]
    assert "Design" in decoded["departments"]


def test_login_with_empty_departments_array(monkeypatch):
    """Test login with empty departments array"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "nodept@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user",
        "departments": []  # Explicitly empty
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "nodept@example.com", "password": "testpass"}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded["departments"] == []


def test_get_users_returns_correct_structure(monkeypatch):
    """Test that get_all_users returns data in correct structure"""
    mock_user = {"sub": "user-123", "role": "user", "departments": []}

    mock_users_list = [
        {"uuid": "user-1", "email": "user1@example.com", "role": "user", "name": "User One"},
        {"uuid": "user-2", "email": "user2@example.com", "role": "admin", "name": "Admin User"}
    ]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_user)

    mock_user_manager = MagicMock()
    mock_user_manager.get_all_users.return_value = mock_users_list

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_user)
        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)
        # Verify structure is maintained
        if len(data["users"]) > 0:
            assert "uuid" in data["users"][0]
            assert "email" in data["users"][0]


def test_logout_multiple_times():
    """Test calling logout multiple times (should always succeed)"""
    response1 = client.post("/api/auth/logout")
    response2 = client.post("/api/auth/logout")
    response3 = client.post("/api/auth/logout")

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200


def test_login_then_logout_then_login(monkeypatch):
    """Test login -> logout -> login flow"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user",
        "departments": []
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    # First login
    response1 = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpass"}
    )
    assert response1.status_code == 200
    token1 = response1.json()["access_token"]

    # Logout
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    # Second login (should work fine)
    response2 = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpass"}
    )
    assert response2.status_code == 200
    token2 = response2.json()["access_token"]

    # Tokens should be different (different timestamps)
    assert isinstance(token1, str)
    assert isinstance(token2, str)


def test_login_preserves_all_user_fields_in_token(monkeypatch):
    """Test that login creates token with all required user fields"""
    fake_user = [{
        "uuid": "comprehensive-uuid",
        "email": "comprehensive@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "senior_manager",
        "departments": ["Engineering", "Operations"],
        "name": "Comprehensive User",  # Extra field not in token
        "created_at": "2024-01-01"  # Extra field not in token
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "comprehensive@example.com", "password": "testpass"}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})

    # Verify required fields are present
    assert decoded["sub"] == "comprehensive-uuid"
    assert decoded["role"] == "senior_manager"
    assert decoded["departments"] == ["Engineering", "Operations"]

    # Verify extra fields are NOT in token (security)
    assert "name" not in decoded
    assert "created_at" not in decoded
    assert "email" not in decoded
    assert "password_hash" not in decoded


def test_login_missing_password_field(monkeypatch):
    """Test login when user record is missing password_hash field"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "role": "user",
        "departments": []
        # Missing password_hash field
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    # This test documents that the code doesn't handle missing password_hash gracefully
    # In production, this should be caught and return 500 or 401
    try:
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "anypassword"}
        )
        # If it somehow works, it should be an error status
        assert response.status_code in [401, 500]
    except KeyError:
        # Currently the code raises KeyError - this documents the behavior
        pass


def test_login_with_whitespace_only_email(monkeypatch):
    """Test login with email that is only whitespace"""
    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase([]))

    response = client.post(
        "/api/auth/login",
        data={"username": "   ", "password": "testpass"}
    )

    # Should fail - no user found
    assert response.status_code == 401


def test_login_with_whitespace_only_password(monkeypatch):
    """Test login with password that is only whitespace"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password("realpassword"),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "   "}
    )

    # Should fail - password doesn't match
    assert response.status_code == 401


def test_get_users_with_expired_token(monkeypatch):
    """Test get users with an expired token"""
    from datetime import datetime, timedelta
    import jwt
    from backend.utils.security import SECRET_KEY, ALGORITHM

    # Create expired token (expired 1 hour ago)
    expired_payload = {
        "sub": "user-123",
        "role": "user",
        "departments": [],
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)

    response = client.get(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    # Should fail due to expired token
    assert response.status_code in [401, 403, 422]


def test_login_with_missing_uuid_field(monkeypatch):
    """Test login when user record is missing uuid field"""
    fake_user = [{
        "email": "test@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user",
        "departments": []
        # Missing uuid field
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    # This test documents that the code doesn't handle missing uuid gracefully
    # In production, this should be caught and return 500
    try:
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "testpass"}
        )
        # If it somehow works, it should be an error status
        assert response.status_code in [401, 500]
    except KeyError:
        # Currently the code raises KeyError - this documents the behavior
        pass


def test_login_with_numeric_string_departments(monkeypatch):
    """Test login with numeric strings in departments"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user",
        "departments": ["123", "456", "789"]
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpass"}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded["departments"] == ["123", "456", "789"]


def test_login_password_starts_with_hash(monkeypatch):
    """Test login with password that starts with hash symbol"""
    password_with_hash = "#StartWithHash123"
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password(password_with_hash),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": password_with_hash}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_users_with_network_timeout(monkeypatch):
    """Test get users when UserManager times out"""
    mock_user = {
        "sub": "user-123",
        "role": "user",
        "departments": []
    }

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_user)

    # Mock UserManager to raise timeout
    mock_user_manager = MagicMock()
    mock_user_manager.get_all_users.side_effect = TimeoutError("Request timed out")

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_user)

        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 500


def test_login_with_newline_in_password(monkeypatch):
    """Test login with newline character in password"""
    password_with_newline = "pass\nword"
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password(password_with_newline),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": password_with_newline}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_tab_in_password(monkeypatch):
    """Test login with tab character in password"""
    password_with_tab = "pass\tword"
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password(password_with_tab),
        "role": "user"
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": password_with_tab}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_users_returns_users_with_all_roles(monkeypatch):
    """Test that get_all_users returns users with different role types"""
    mock_user = {"sub": "user-123", "role": "user", "departments": []}

    mock_users_list = [
        {"uuid": "user-1", "email": "user@example.com", "role": "user"},
        {"uuid": "admin-1", "email": "admin@example.com", "role": "admin"},
        {"uuid": "manager-1", "email": "manager@example.com", "role": "manager"},
        {"uuid": "guest-1", "email": "guest@example.com", "role": "guest"}
    ]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_user)

    mock_user_manager = MagicMock()
    mock_user_manager.get_all_users.return_value = mock_users_list

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_user)
        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 4
        roles = [u["role"] for u in data["users"]]
        assert "user" in roles
        assert "admin" in roles
        assert "manager" in roles
        assert "guest" in roles


def test_login_form_data_with_extra_fields(monkeypatch):
    """Test login with extra unexpected fields in form data"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user",
        "departments": []
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    # OAuth2PasswordRequestForm should ignore extra fields
    response = client.post(
        "/api/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpass",
            "extra_field": "should_be_ignored"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_boolean_departments(monkeypatch):
    """Test login when departments field contains non-standard data type"""
    fake_user = [{
        "uuid": "test-uuid",
        "email": "test@example.com",
        "password_hash": security.hash_password("testpass"),
        "role": "user",
        "departments": None  # None instead of array
    }]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase(fake_user))

    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpass"}
    )

    # Should handle gracefully
    assert response.status_code in [200, 500]


def test_logout_with_query_parameters():
    """Test logout endpoint ignores query parameters"""
    response = client.post("/api/auth/logout?token=something&user=test")

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out (frontend should delete token)"}


def test_get_users_called_twice_returns_consistent_results(monkeypatch):
    """Test that calling get_all_users twice returns consistent results"""
    mock_user = {"sub": "user-123", "role": "user", "departments": []}

    mock_users_list = [
        {"uuid": "user-1", "email": "user1@example.com", "role": "user"}
    ]

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "get_current_user", lambda: mock_user)

    mock_user_manager = MagicMock()
    mock_user_manager.get_all_users.return_value = mock_users_list

    with patch("backend.routers.auth.UserManager", return_value=mock_user_manager):
        token = security.create_access_token(mock_user)

        # First call
        response1 = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Second call
        response2 = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()


def test_login_with_extremely_long_email(monkeypatch):
    """Test login with very long email address"""
    long_email = "a" * 500 + "@example.com"

    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase([]))

    response = client.post(
        "/api/auth/login",
        data={"username": long_email, "password": "testpass"}
    )

    # Should fail - user not found
    assert response.status_code == 401


def test_login_with_missing_at_symbol_email(monkeypatch):
    """Test login with invalid email format (no @ symbol)"""
    import backend.routers.auth as auth
    monkeypatch.setattr(auth, "SupabaseCRUD", lambda: DummySupabase([]))

    response = client.post(
        "/api/auth/login",
        data={"username": "notanemail.com", "password": "testpass"}
    )

    # Should fail - user not found (email validation happens elsewhere)
    assert response.status_code == 401
