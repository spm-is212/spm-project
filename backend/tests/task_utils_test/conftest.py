import pytest
from unittest.mock import Mock
from datetime import date, timedelta


@pytest.fixture
def mock_crud():
    """Mock SupabaseCRUD for unit testing"""
    return Mock()


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "title": "Test Task",
        "description": "Test description",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "status": "TO_DO",
        "priority": "HIGH",
        "owner_user_id": "00000000-0000-0000-0000-000000000001",
        "assignee_ids": ["00000000-0000-0000-0000-000000000001"],
        "parent_id": None,
        "comments": [],
        "attachments": [],
        "is_archived": False
    }


@pytest.fixture
def sample_subtask_data():
    """Sample subtask data for testing"""
    return {
        "title": "Test Subtask",
        "description": "Test subtask description",
        "due_date": (date.today() + timedelta(days=3)).isoformat(),
        "status": "TO_DO",
        "priority": "MEDIUM",
        "assignee_ids": ["00000000-0000-0000-0000-000000000001"]
    }


@pytest.fixture
def mock_task_in_db():
    """Mock task that exists in database"""
    return {
        "id": "test-task-id-123",
        "title": "Existing Task",
        "description": "Existing description",
        "due_date": "2025-10-01",
        "status": "TO_DO",
        "priority": "HIGH",
        "owner_user_id": "00000000-0000-0000-0000-000000000001",
        "assignee_ids": ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"],
        "parent_id": None,
        "comments": [],
        "attachments": [],
        "is_archived": False,
        "created_at": "2025-09-22T00:00:00Z",
        "updated_at": "2025-09-22T00:00:00Z"
    }
