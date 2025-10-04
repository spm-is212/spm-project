import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from backend.main import app
from backend.utils.security import create_access_token
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing"""
    token_data = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "role": "manager"
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff_auth_headers():
    """Create authentication headers for staff user testing"""
    token_data = {
        "sub": "00000000-0000-0000-0000-000000000002",
        "role": "staff"
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_project(patch_crud_for_testing):
    """Create and cleanup a test project"""
    crud = SupabaseCRUD()

    # Create test project
    project_data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "project_name": "Test Project",
        "description": "Test project for integration tests",
        "owner_uuid": "00000000-0000-0000-0000-000000000001",
        "is_archived": False
    }

    try:
        crud.insert("projects", project_data)
    except Exception:
        pass  # Project might already exist

    yield project_data

    # Cleanup handled by patch_crud_for_testing teardown


@pytest.fixture
def sample_main_task():
    """Sample main task data"""
    return {
        "title": "Test Main Task",
        "description": "This is a test main task",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "status": "TO_DO",
        "priority": "HIGH",
        "assignee_ids": ["00000000-0000-0000-0000-000000000001"]
    }


@pytest.fixture
def sample_subtasks():
    """Sample subtasks data"""
    return [
        {
            "title": "Test Subtask 1",
            "description": "First test subtask",
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
            "status": "TO_DO",
            "priority": "MEDIUM",
            "assignee_ids": ["00000000-0000-0000-0000-000000000001"]
        },
        {
            "title": "Test Subtask 2",
            "description": "Second test subtask without assignees",
            "due_date": (date.today() + timedelta(days=5)).isoformat(),
            "status": "TO_DO",
            "priority": "LOW"
        }
    ]


@pytest.fixture
def patch_crud_for_testing(monkeypatch):
    """Monkeypatch SupabaseCRUD to use test tables instead of production tables"""

    # Store original methods
    original_select = SupabaseCRUD.select
    original_insert = SupabaseCRUD.insert
    original_update = SupabaseCRUD.update
    original_delete = SupabaseCRUD.delete
    original_count = SupabaseCRUD.count
    original_exists = SupabaseCRUD.exists

    def patched_select(self, table, columns="*", filters=None, limit=None, order_by=None, ascending=True):
        test_table = f"{table}_test"
        return original_select(self, test_table, columns, filters, limit, order_by, ascending)

    def patched_insert(self, table, data):
        test_table = f"{table}_test"
        return original_insert(self, test_table, data)

    def patched_update(self, table, data, filters):
        test_table = f"{table}_test"
        return original_update(self, test_table, data, filters)

    def patched_delete(self, table, filters):
        test_table = f"{table}_test"
        return original_delete(self, test_table, filters)

    def patched_count(self, table, filters=None):
        test_table = f"{table}_test"
        return original_count(self, test_table, filters)

    def patched_exists(self, table, filters):
        test_table = f"{table}_test"
        return original_exists(self, test_table, filters)

    # Apply patches to instance methods
    monkeypatch.setattr(SupabaseCRUD, "select", patched_select)
    monkeypatch.setattr(SupabaseCRUD, "insert", patched_insert)
    monkeypatch.setattr(SupabaseCRUD, "update", patched_update)
    monkeypatch.setattr(SupabaseCRUD, "delete", patched_delete)
    monkeypatch.setattr(SupabaseCRUD, "count", patched_count)
    monkeypatch.setattr(SupabaseCRUD, "exists", patched_exists)

    yield

    # Cleanup: Restore original methods first to avoid double _test suffix
    monkeypatch.undo()

    # Additional cleanup: ensure test tables are completely clear
    from backend.tests.utils.cleanup import clear_all_test_data
    try:
        clear_all_test_data(['users', 'tasks', 'projects'])
    except Exception:
        pass  # Cleanup is optional
