import pytest
from unittest.mock import Mock
from datetime import date, timedelta


@pytest.fixture
def mock_crud():
    """Mock SupabaseCRUD for unit testing report generators"""
    mock = Mock()

    # Default return values
    mock.select.return_value = []
    mock.insert.return_value = {}
    mock.update.return_value = []
    mock.delete.return_value = []

    return mock


@pytest.fixture
def sample_project():
    """Sample project data"""
    return {
        "id": "proj-123",
        "name": "Test Project",
        "description": "A test project",
        "created_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_users():
    """Sample user data for testing"""
    return [
        {
            "uuid": "user-1",
            "email": "user1@test.com",
            "departments": ["Engineering", "IT"]
        },
        {
            "uuid": "user-2",
            "email": "user2@test.com",
            "departments": ["Engineering"]
        },
        {
            "uuid": "user-3",
            "email": "user3@test.com",
            "departments": ["Marketing"]
        }
    ]


@pytest.fixture
def sample_tasks():
    """Sample task data for testing"""
    today = date.today()
    return [
        {
            "id": "task-1",
            "title": "Task 1",
            "description": "First task",
            "status": "COMPLETED",
            "priority": 5,
            "due_date": (today - timedelta(days=2)).isoformat(),
            "project_id": "proj-123",
            "owner_user_id": "user-1",
            "assignee_ids": ["user-1", "user-2"],
            "time_log": 5.5,
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "task-2",
            "title": "Task 2",
            "description": "Second task",
            "status": "IN_PROGRESS",
            "priority": 8,
            "due_date": (today + timedelta(days=3)).isoformat(),
            "project_id": "proj-123",
            "owner_user_id": "user-2",
            "assignee_ids": ["user-2"],
            "time_log": 3.0,
            "created_at": "2025-01-02T00:00:00Z"
        },
        {
            "id": "task-3",
            "title": "Task 3",
            "description": "Third task",
            "status": "TO_DO",
            "priority": 3,
            "due_date": (today - timedelta(days=5)).isoformat(),
            "project_id": "proj-456",
            "owner_user_id": "user-1",
            "assignee_ids": ["user-1"],
            "time_log": None,
            "created_at": "2025-01-03T00:00:00Z"
        },
        {
            "id": "task-4",
            "title": "Task 4",
            "description": "Fourth task",
            "status": "BLOCKED",
            "priority": 7,
            "due_date": (today + timedelta(days=1)).isoformat(),
            "project_id": "proj-123",
            "owner_user_id": "user-3",
            "assignee_ids": ["user-3"],
            "time_log": 2.5,
            "created_at": "2025-01-04T00:00:00Z"
        }
    ]


@pytest.fixture
def date_range():
    """Sample date range for testing"""
    today = date.today()
    return {
        "start_date": today - timedelta(days=30),
        "end_date": today + timedelta(days=30)
    }


@pytest.fixture
def narrow_date_range():
    """Narrow date range that filters out most tasks"""
    today = date.today()
    return {
        "start_date": today + timedelta(days=1),
        "end_date": today + timedelta(days=5)
    }
