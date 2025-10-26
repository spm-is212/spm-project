from fastapi.testclient import TestClient
from backend.main import app
from backend.utils import security
from datetime import datetime

client = TestClient(app)


# --- Dummy classes to fake Supabase responses ---
class DummyResult:
    def __init__(self, data):
        self.data = data


class DummySupabase:
    def __init__(self, data, update_data=None, delete_success=True):
        self.client = self
        self._data = data
        self._update_data = update_data
        self._delete_success = delete_success
        self._last_table = None
        self._filters = {}

    def table(self, name):
        self._last_table = name
        return self

    def select(self, *args, **kwargs):
        return self

    def insert(self, data, **kwargs):
        self._insert_data = data
        return self

    def update(self, data):
        self._update_data = data
        return self

    def delete(self):
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def or_(self, condition):
        return self

    def execute(self):
        if self._last_table == "tasks" and hasattr(self, '_filters'):
            # Return empty tasks for testing
            return DummyResult([])
        if hasattr(self, '_update_data') and self._update_data:
            return DummyResult([{**self._data[0], **self._update_data}] if self._data else [])
        if hasattr(self, '_insert_data'):
            # Return inserted data with generated ID
            return DummyResult([{**self._insert_data, 'id': 'test-project-id'}])
        return DummyResult(self._data)


def create_mock_user(uuid="user-123", role="user", departments=None):
    """Helper to create mock user for authentication"""
    if departments is None:
        departments = []
    return {
        "sub": uuid,
        "role": role,
        "departments": departments
    }


# --- Tests for Create Project ---
def test_create_project_success(monkeypatch):
    """Test successful project creation"""
    mock_user = create_mock_user(uuid="creator-123", role="user")

    # Mock get_current_user
    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)

    # Mock SupabaseCRUD
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase([]))

    # Create mock token
    token = security.create_access_token(mock_user)

    response = client.post(
        "/api/projects/create",
        json={
            "name": "Test Project",
            "description": "A test project",
            "collaborator_ids": ["user-1", "user-2"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project"
    assert "user-1" in data["collaborator_ids"]
    assert "user-2" in data["collaborator_ids"]


def test_create_project_without_collaborators(monkeypatch):
    """Test project creation fails without collaborators"""
    mock_user = create_mock_user(uuid="creator-123", role="user")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)

    token = security.create_access_token(mock_user)

    response = client.post(
        "/api/projects/create",
        json={
            "name": "Test Project",
            "description": "A test project",
            "collaborator_ids": []
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # Should fail validation due to empty collaborators
    assert response.status_code == 422


def test_create_project_without_name(monkeypatch):
    """Test project creation fails without name"""
    mock_user = create_mock_user(uuid="creator-123", role="user")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)

    token = security.create_access_token(mock_user)

    response = client.post(
        "/api/projects/create",
        json={
            "description": "A test project",
            "collaborator_ids": ["user-1"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


# --- Tests for List Projects ---
def test_list_projects_as_admin(monkeypatch):
    """Test admin can see all projects"""
    mock_user = create_mock_user(uuid="admin-123", role="admin")

    fake_projects = [
        {
            "id": "proj-1",
            "name": "Project 1",
            "description": "First project",
            "collaborator_ids": ["user-1"],
            "created_by": "user-1",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "proj-2",
            "name": "Project 2",
            "description": "Second project",
            "collaborator_ids": ["user-2"],
            "created_by": "user-2",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Project 1"
    assert data[1]["name"] == "Project 2"


def test_list_projects_as_collaborator(monkeypatch):
    """Test user only sees projects they're collaborating on"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    fake_projects = [
        {
            "id": "proj-1",
            "name": "My Project",
            "description": "I'm a collaborator",
            "collaborator_ids": ["user-123", "user-2"],
            "created_by": "user-2",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "proj-2",
            "name": "Other Project",
            "description": "Not a collaborator",
            "collaborator_ids": ["user-2", "user-3"],
            "created_by": "user-2",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router

    class CustomDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._call_count = 0

        def execute(self):
            self._call_count += 1
            if self._last_table == "projects":
                return DummyResult(self._data)
            elif self._last_table == "tasks":
                # Return empty tasks result
                return DummyResult([])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: CustomDummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "My Project"
    assert "user-123" in data[0]["collaborator_ids"]


def test_list_projects_empty(monkeypatch):
    """Test listing projects when none exist"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == []


# --- Tests for Get Project ---
def test_get_project_success(monkeypatch):
    """Test getting a specific project by ID"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    fake_project = [{
        "id": "proj-1",
        "name": "Test Project",
        "description": "A test project",
        "collaborator_ids": ["user-123"],
        "created_by": "user-123",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase(fake_project))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/proj-1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "proj-1"
    assert data["name"] == "Test Project"


def test_get_project_not_found(monkeypatch):
    """Test getting a non-existent project"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/nonexistent-id",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


# --- Tests for Update Project ---
def test_update_project_as_collaborator(monkeypatch):
    """Test updating project as a collaborator"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    existing_project = [{
        "id": "proj-1",
        "name": "Old Name",
        "description": "Old description",
        "collaborator_ids": ["user-123", "user-2"],
        "created_by": "user-2",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router

    class UpdateDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._is_update = False

        def update(self, data):
            self._is_update = True
            self._update_payload = data
            return self

        def execute(self):
            if self._is_update:
                updated = {**self._data[0], **self._update_payload}
                return DummyResult([updated])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: UpdateDummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/proj-1",
        json={
            "name": "Updated Name",
            "description": "Updated description"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


def test_update_project_not_collaborator(monkeypatch):
    """Test updating project when not a collaborator (should fail)"""
    mock_user = create_mock_user(uuid="user-999", role="user")

    existing_project = [{
        "id": "proj-1",
        "name": "Old Name",
        "description": "Old description",
        "collaborator_ids": ["user-123", "user-2"],
        "created_by": "user-2",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/proj-1",
        json={
            "name": "Hacked Name"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only project collaborators can update the project"


def test_update_project_as_admin(monkeypatch):
    """Test admin can update any project"""
    mock_user = create_mock_user(uuid="admin-123", role="admin")

    existing_project = [{
        "id": "proj-1",
        "name": "Old Name",
        "description": "Old description",
        "collaborator_ids": ["user-123", "user-2"],
        "created_by": "user-2",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router

    class UpdateDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._is_update = False

        def update(self, data):
            self._is_update = True
            self._update_payload = data
            return self

        def execute(self):
            if self._is_update:
                updated = {**self._data[0], **self._update_payload}
                return DummyResult([updated])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: UpdateDummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/proj-1",
        json={
            "name": "Admin Updated"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Admin Updated"


def test_update_project_not_found(monkeypatch):
    """Test updating a non-existent project"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/nonexistent",
        json={
            "name": "New Name"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_update_project_empty_collaborators(monkeypatch):
    """Test updating project with empty collaborators list (should fail validation)"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/proj-1",
        json={
            "collaborator_ids": []
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # Should fail pydantic validation
    assert response.status_code == 422


# --- Tests for Delete Project ---
def test_delete_project_success(monkeypatch):
    """Test successful project deletion"""
    mock_user = create_mock_user(uuid="user-123", role="admin")

    existing_project = [{
        "id": "proj-1",
        "name": "Project to Delete",
        "description": "Will be deleted",
        "collaborator_ids": ["user-123"],
        "created_by": "user-123",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router

    class DeleteDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._is_delete = False

        def delete(self):
            self._is_delete = True
            return self

        def execute(self):
            if self._is_delete:
                return DummyResult([])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DeleteDummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    response = client.delete(
        "/api/projects/proj-1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Project deleted successfully"


def test_delete_project_not_found(monkeypatch):
    """Test deleting a non-existent project"""
    mock_user = create_mock_user(uuid="user-123", role="admin")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.delete(
        "/api/projects/nonexistent",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


# --- Tests for Authentication/Authorization ---
def test_create_project_unauthorized():
    """Test creating project without authentication"""
    response = client.post(
        "/api/projects/create",
        json={
            "name": "Unauthorized Project",
            "description": "Should fail",
            "collaborator_ids": ["user-1"]
        }
    )

    assert response.status_code == 403


def test_list_projects_unauthorized():
    """Test listing projects without authentication"""
    response = client.get("/api/projects/list")

    assert response.status_code == 403


def test_get_project_unauthorized():
    """Test getting project without authentication"""
    response = client.get("/api/projects/proj-1")

    assert response.status_code == 403


def test_update_project_unauthorized():
    """Test updating project without authentication"""
    response = client.put(
        "/api/projects/proj-1",
        json={"name": "Hacked"}
    )

    assert response.status_code == 403


def test_delete_project_unauthorized():
    """Test deleting project without authentication"""
    response = client.delete("/api/projects/proj-1")

    assert response.status_code == 403


# --- Tests for Error Handling and Edge Cases ---
def test_create_project_database_error(monkeypatch):
    """Test creating project when database insert fails"""
    mock_user = create_mock_user(uuid="creator-123", role="user")

    import backend.routers.project as project_router

    class ErrorDummySupabase(DummySupabase):
        def execute(self):
            # Return empty data to simulate insert failure
            return DummyResult([])

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: ErrorDummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.post(
        "/api/projects/create",
        json={
            "name": "Test Project",
            "description": "A test project",
            "collaborator_ids": ["user-1"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 500
    assert "Failed to create project" in response.json()["detail"]


def test_create_project_general_exception(monkeypatch):
    """Test creating project with unexpected exception"""
    mock_user = create_mock_user(uuid="creator-123", role="user")

    import backend.routers.project as project_router

    class ExceptionDummySupabase(DummySupabase):
        def execute(self):
            raise Exception("Unexpected database error")

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: ExceptionDummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.post(
        "/api/projects/create",
        json={
            "name": "Test Project",
            "description": "A test project",
            "collaborator_ids": ["user-1"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_list_projects_connection_error(monkeypatch):
    """Test listing projects with connection error"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    import backend.routers.project as project_router

    class ConnectionErrorDummySupabase(DummySupabase):
        def execute(self):
            raise ConnectionError("Database connection failed")

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: ConnectionErrorDummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 503
    assert "Database connection unavailable" in response.json()["detail"]


def test_list_projects_timeout_error(monkeypatch):
    """Test listing projects with timeout error"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    import backend.routers.project as project_router

    class TimeoutErrorDummySupabase(DummySupabase):
        def execute(self):
            raise TimeoutError("Database request timed out")

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: TimeoutErrorDummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 504
    assert "Database request timed out" in response.json()["detail"]


def test_list_projects_user_with_tasks(monkeypatch):
    """Test listing projects where user has tasks assigned (not just collaborator)"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    fake_projects = [
        {
            "id": "proj-1",
            "name": "Project with Task",
            "description": "User has task here",
            "collaborator_ids": ["user-2"],  # User NOT a collaborator
            "created_by": "user-2",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "proj-2",
            "name": "Other Project",
            "description": "User has no access",
            "collaborator_ids": ["user-3"],
            "created_by": "user-3",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router

    class TaskAssignedDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._call_count = 0

        def execute(self):
            self._call_count += 1
            if self._last_table == "projects":
                return DummyResult(self._data)
            elif self._last_table == "tasks":
                # Return task with project_id for proj-1
                return DummyResult([{"project_id": "proj-1"}])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: TaskAssignedDummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Project with Task"
    assert data[0]["id"] == "proj-1"


def test_list_projects_user_both_collaborator_and_task(monkeypatch):
    """Test listing projects where user is both collaborator and has tasks"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    fake_projects = [
        {
            "id": "proj-1",
            "name": "Collaborator Project",
            "description": "User is collaborator",
            "collaborator_ids": ["user-123", "user-2"],
            "created_by": "user-2",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router

    class BothAccessDummySupabase(DummySupabase):
        def execute(self):
            if self._last_table == "projects":
                return DummyResult(self._data)
            elif self._last_table == "tasks":
                # User also has tasks in proj-1
                return DummyResult([{"project_id": "proj-1"}])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: BothAccessDummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Should not duplicate
    assert data[0]["name"] == "Collaborator Project"


def test_list_projects_without_role(monkeypatch):
    """Test listing projects when user doesn't have role field"""
    mock_user = {"sub": "user-123", "departments": []}  # No role field

    fake_projects = [
        {
            "id": "proj-1",
            "name": "My Project",
            "description": "I'm a collaborator",
            "collaborator_ids": ["user-123"],
            "created_by": "user-123",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router

    class NoRoleDummySupabase(DummySupabase):
        def execute(self):
            if self._last_table == "projects":
                return DummyResult(self._data)
            elif self._last_table == "tasks":
                return DummyResult([])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: NoRoleDummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_project_general_exception(monkeypatch):
    """Test getting project with unexpected exception"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    import backend.routers.project as project_router

    class ExceptionDummySupabase(DummySupabase):
        def execute(self):
            raise Exception("Unexpected error")

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: ExceptionDummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/proj-1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_update_project_database_failure(monkeypatch):
    """Test updating project when database update fails"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    existing_project = [{
        "id": "proj-1",
        "name": "Old Name",
        "description": "Old description",
        "collaborator_ids": ["user-123"],
        "created_by": "user-123",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router

    class FailedUpdateDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._is_update = False

        def update(self, data):
            self._is_update = True
            return self

        def execute(self):
            if self._is_update:
                return DummyResult([])  # Empty result = failed update
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: FailedUpdateDummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/proj-1",
        json={
            "name": "New Name"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 500
    assert "Failed to update project" in response.json()["detail"]


def test_update_project_partial_update(monkeypatch):
    """Test updating only some fields of a project"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    existing_project = [{
        "id": "proj-1",
        "name": "Old Name",
        "description": "Old description",
        "collaborator_ids": ["user-123"],
        "created_by": "user-123",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router

    class PartialUpdateDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._is_update = False

        def update(self, data):
            self._is_update = True
            self._update_payload = data
            return self

        def execute(self):
            if self._is_update:
                updated = {**self._data[0], **self._update_payload}
                return DummyResult([updated])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: PartialUpdateDummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    # Only update description, not name
    response = client.put(
        "/api/projects/proj-1",
        json={
            "description": "New description only"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Old Name"  # Should remain unchanged
    assert data["description"] == "New description only"


def test_update_project_general_exception(monkeypatch):
    """Test updating project with unexpected exception"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    import backend.routers.project as project_router

    class ExceptionDummySupabase(DummySupabase):
        def execute(self):
            raise Exception("Unexpected update error")

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: ExceptionDummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/proj-1",
        json={
            "name": "New Name"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_delete_project_general_exception(monkeypatch):
    """Test deleting project with unexpected exception"""
    mock_user = create_mock_user(uuid="admin-123", role="admin")

    import backend.routers.project as project_router

    class ExceptionDummySupabase(DummySupabase):
        def execute(self):
            raise Exception("Unexpected delete error")

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: ExceptionDummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.delete(
        "/api/projects/proj-1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_list_projects_admin_uppercase_role(monkeypatch):
    """Test admin with uppercase ADMIN role can see all projects"""
    mock_user = create_mock_user(uuid="admin-123", role="ADMIN")  # Uppercase

    fake_projects = [
        {
            "id": "proj-1",
            "name": "Project 1",
            "description": "First project",
            "collaborator_ids": ["user-1"],
            "created_by": "user-1",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_list_projects_task_without_project_id(monkeypatch):
    """Test listing projects when task has no project_id"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    fake_projects = [
        {
            "id": "proj-1",
            "name": "My Project",
            "description": "I'm a collaborator",
            "collaborator_ids": ["user-123"],
            "created_by": "user-123",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router

    class TaskNoProjectIdDummySupabase(DummySupabase):
        def execute(self):
            if self._last_table == "projects":
                return DummyResult(self._data)
            elif self._last_table == "tasks":
                # Task without project_id
                return DummyResult([{"id": "task-1"}])  # No project_id field
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: TaskNoProjectIdDummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Should still show collaborator project


def test_create_project_with_long_name(monkeypatch):
    """Test creating project with maximum length name"""
    mock_user = create_mock_user(uuid="creator-123", role="user")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase([]))

    token = security.create_access_token(mock_user)

    long_name = "A" * 200  # Max length from schema

    response = client.post(
        "/api/projects/create",
        json={
            "name": long_name,
            "description": "Testing max length",
            "collaborator_ids": ["user-1"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == long_name


def test_create_project_name_too_long(monkeypatch):
    """Test creating project with name exceeding max length"""
    mock_user = create_mock_user(uuid="creator-123", role="user")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)

    token = security.create_access_token(mock_user)

    too_long_name = "A" * 201  # Exceeds max length

    response = client.post(
        "/api/projects/create",
        json={
            "name": too_long_name,
            "description": "Testing",
            "collaborator_ids": ["user-1"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422  # Validation error


def test_list_projects_without_collaborator_ids_field(monkeypatch):
    """Test listing projects when some projects don't have collaborator_ids field"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    fake_projects = [
        {
            "id": "proj-1",
            "name": "Project without collaborators field",
            "description": "No collaborator_ids",
            "created_by": "user-123",
            "created_at": datetime.utcnow().isoformat()
            # Missing collaborator_ids field
        },
        {
            "id": "proj-2",
            "name": "Normal Project",
            "description": "Has collaborators",
            "collaborator_ids": ["user-123"],
            "created_by": "user-123",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router

    class NoCollabDummySupabase(DummySupabase):
        def execute(self):
            if self._last_table == "projects":
                return DummyResult(self._data)
            elif self._last_table == "tasks":
                return DummyResult([])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: NoCollabDummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Should only return proj-2 which has user-123 in collaborator_ids
    assert len(data) == 1
    assert data[0]["id"] == "proj-2"


def test_update_project_all_none_values(monkeypatch):
    """Test updating project with all fields set to None"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    existing_project = [{
        "id": "proj-1",
        "name": "Original Name",
        "description": "Original description",
        "collaborator_ids": ["user-123"],
        "created_by": "user-123",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router

    class NoneUpdateDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._is_update = False
            self._update_payload = None

        def update(self, data):
            self._is_update = True
            self._update_payload = data
            return self

        def execute(self):
            if self._is_update:
                # Should only update updated_at when all fields are None
                updated = {**self._data[0], **self._update_payload}
                return DummyResult([updated])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: NoneUpdateDummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    # Send update with all None values
    response = client.put(
        "/api/projects/proj-1",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Original values should be preserved
    assert data["name"] == "Original Name"
    assert data["description"] == "Original description"


def test_create_project_with_duplicate_collaborators(monkeypatch):
    """Test creating project with duplicate collaborator IDs"""
    mock_user = create_mock_user(uuid="creator-123", role="user")

    import backend.routers.project as project_router
    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: DummySupabase([]))

    token = security.create_access_token(mock_user)

    response = client.post(
        "/api/projects/create",
        json={
            "name": "Duplicate Collaborators Project",
            "description": "Testing duplicates",
            "collaborator_ids": ["user-1", "user-1", "user-2", "user-2"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # Should succeed - validation doesn't check for duplicates
    assert response.status_code == 201
    data = response.json()
    assert "user-1" in data["collaborator_ids"]


def test_list_projects_with_multiple_task_project_ids(monkeypatch):
    """Test listing projects where user has tasks in multiple projects"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    fake_projects = [
        {
            "id": "proj-1",
            "name": "Project 1",
            "description": "First project",
            "collaborator_ids": ["user-2"],
            "created_by": "user-2",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "proj-2",
            "name": "Project 2",
            "description": "Second project",
            "collaborator_ids": ["user-3"],
            "created_by": "user-3",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "proj-3",
            "name": "Project 3",
            "description": "Third project",
            "collaborator_ids": ["user-4"],
            "created_by": "user-4",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    import backend.routers.project as project_router

    class MultipleTasksDummySupabase(DummySupabase):
        def execute(self):
            if self._last_table == "projects":
                return DummyResult(self._data)
            elif self._last_table == "tasks":
                # User has tasks in proj-1 and proj-2
                return DummyResult([
                    {"project_id": "proj-1"},
                    {"project_id": "proj-2"},
                    {"project_id": "proj-1"}  # Duplicate
                ])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: MultipleTasksDummySupabase(fake_projects))

    token = security.create_access_token(mock_user)

    response = client.get(
        "/api/projects/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    project_ids = [p["id"] for p in data]
    assert "proj-1" in project_ids
    assert "proj-2" in project_ids


def test_update_project_only_name(monkeypatch):
    """Test updating only the project name"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    existing_project = [{
        "id": "proj-1",
        "name": "Old Name",
        "description": "Original description",
        "collaborator_ids": ["user-123", "user-2"],
        "created_by": "user-123",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router

    class NameOnlyUpdateDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._is_update = False

        def update(self, data):
            self._is_update = True
            self._update_payload = data
            return self

        def execute(self):
            if self._is_update:
                updated = {**self._data[0], **self._update_payload}
                return DummyResult([updated])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: NameOnlyUpdateDummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/proj-1",
        json={"name": "Updated Name Only"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name Only"
    assert data["description"] == "Original description"
    assert data["collaborator_ids"] == ["user-123", "user-2"]


def test_update_project_only_collaborators(monkeypatch):
    """Test updating only the collaborator list"""
    mock_user = create_mock_user(uuid="user-123", role="user")

    existing_project = [{
        "id": "proj-1",
        "name": "Project Name",
        "description": "Project description",
        "collaborator_ids": ["user-123"],
        "created_by": "user-123",
        "created_at": datetime.utcnow().isoformat()
    }]

    import backend.routers.project as project_router

    class CollabUpdateDummySupabase(DummySupabase):
        def __init__(self, data):
            super().__init__(data)
            self._is_update = False

        def update(self, data):
            self._is_update = True
            self._update_payload = data
            return self

        def execute(self):
            if self._is_update:
                updated = {**self._data[0], **self._update_payload}
                return DummyResult([updated])
            return DummyResult(self._data)

    monkeypatch.setattr(project_router, "get_current_user", lambda: mock_user)
    monkeypatch.setattr(project_router, "SupabaseCRUD", lambda: CollabUpdateDummySupabase(existing_project))

    token = security.create_access_token(mock_user)

    response = client.put(
        "/api/projects/proj-1",
        json={"collaborator_ids": ["user-123", "user-2", "user-3"]},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Project Name"
    assert len(data["collaborator_ids"]) == 3
    assert "user-2" in data["collaborator_ids"]
    assert "user-3" in data["collaborator_ids"]
