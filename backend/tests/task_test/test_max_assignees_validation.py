from backend.tests.task_test.conftest import client
from backend.utils.task_crud.constants import make_future_due_date


def test_create_task_with_max_5_assignees_success(auth_headers, patch_crud_for_testing, test_project):
    """Test creating task with exactly 5 assignees succeeds"""
    payload = {
        "main_task": {
            "title": "Test Task",
            "description": "Test Description",
            "due_date": make_future_due_date(),
            "status": "TO_DO",
            "priority": 5,
            "assignee_ids": [
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002",
                "550e8400-e29b-41d4-a716-446655440003",
                "550e8400-e29b-41d4-a716-446655440004",
                "550e8400-e29b-41d4-a716-446655440005"
            ]  # Exactly 5 valid UUIDs
        }
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200


def test_create_task_with_6_assignees_fails(auth_headers, patch_crud_for_testing, test_project):
    """Test creating task with 6 assignees fails validation"""
    payload = {
        "main_task": {
            "title": "Test Task",
            "description": "Test Description",
            "due_date": make_future_due_date(),
            "status": "TO_DO",
            "priority": 5,
            "assignee_ids": [
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002",
                "550e8400-e29b-41d4-a716-446655440003",
                "550e8400-e29b-41d4-a716-446655440004",
                "550e8400-e29b-41d4-a716-446655440005",
                "550e8400-e29b-41d4-a716-446655440006"
            ]  # Too many!
        }
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 422
    assert "Maximum of 5 assignees allowed per task" in response.json()["detail"][0]["msg"]


def test_create_subtask_with_6_assignees_fails(auth_headers, patch_crud_for_testing, test_project):
    """Test creating subtask with 6 assignees fails validation"""
    payload = {
        "main_task": {
            "title": "Test Task",
            "description": "Test Description",
            "due_date": make_future_due_date(),
            "status": "TO_DO",
            "priority": 5,
            "assignee_ids": [
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002"
            ]
        },
        "subtasks": [
            {
                "title": "Test Subtask",
                "description": "Test Description",
                "due_date": make_future_due_date(),
                "status": "TO_DO",
                "priority": 5,
                "assignee_ids": [
                    "550e8400-e29b-41d4-a716-446655440001",
                    "550e8400-e29b-41d4-a716-446655440002",
                    "550e8400-e29b-41d4-a716-446655440003",
                    "550e8400-e29b-41d4-a716-446655440004",
                    "550e8400-e29b-41d4-a716-446655440005",
                    "550e8400-e29b-41d4-a716-446655440006"
                ]  # Too many!
            }
        ]
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 422
    assert "Maximum of 5 assignees allowed per subtask" in response.json()["detail"][0]["msg"]


def test_update_task_with_6_assignees_fails(auth_headers, patch_crud_for_testing):
    """Test updating task with 6 assignees fails validation"""
    payload = {
        "main_task_id": "550e8400-e29b-41d4-a716-446655440000",
        "main_task": {
            "title": "Updated Task",
            "assignee_ids": [
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002",
                "550e8400-e29b-41d4-a716-446655440003",
                "550e8400-e29b-41d4-a716-446655440004",
                "550e8400-e29b-41d4-a716-446655440005",
                "550e8400-e29b-41d4-a716-446655440006"
            ]  # Too many!
        }
    }

    response = client.put(
        "/api/tasks/updateTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 422
    assert "Maximum of 5 assignees allowed per task" in response.json()["detail"][0]["msg"]
