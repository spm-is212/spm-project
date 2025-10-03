from backend.tests.task_test.conftest import client
from backend.utils.task_crud.constants import make_future_due_date


def test_create_main_task_only_success(auth_headers, sample_main_task, patch_crud_for_testing, test_project):
    """Test creating only a main task without subtasks"""
    payload = {
        "main_task": sample_main_task
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Check main task was created
    assert "main_task" in data
    assert data["main_task"]["title"] == sample_main_task["title"]
    assert data["main_task"]["parent_id"] is None
    assert data["main_task"]["owner_user_id"] == "00000000-0000-0000-0000-000000000001"

    # Check no subtasks were created
    assert "subtasks" in data
    assert len(data["subtasks"]) == 0


def test_create_task_with_subtasks_success(auth_headers, sample_main_task, sample_subtasks, patch_crud_for_testing, test_project):
    """Test creating a main task with subtasks"""
    payload = {
        "main_task": sample_main_task,
        "subtasks": sample_subtasks
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Check main task
    assert data["main_task"]["title"] == sample_main_task["title"]
    assert data["main_task"]["parent_id"] is None

    # Check subtasks
    assert len(data["subtasks"]) == 2
    for i, subtask in enumerate(data["subtasks"]):
        assert subtask["title"] == sample_subtasks[i]["title"]
        assert subtask["parent_id"] == data["main_task"]["id"]
        assert subtask["owner_user_id"] == "00000000-0000-0000-0000-000000000001"


def test_create_subtask_without_assignees(auth_headers, sample_main_task, patch_crud_for_testing, test_project):
    """Test creating subtask without assignee_ids (should default to empty array)"""
    subtask_without_assignees = {
        "title": "Unassigned Subtask",
        "description": "This subtask has no assignees",
        "due_date": make_future_due_date(),
        "status": "TO_DO",
        "priority": "LOW"
    }

    payload = {
        "main_task": sample_main_task,
        "subtasks": [subtask_without_assignees]
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Check subtask has creator auto-assigned
    assert len(data["subtasks"]) == 1
    assert data["subtasks"][0]["assignee_ids"] == ["00000000-0000-0000-0000-000000000001"]


def test_create_task_without_auth_fails(sample_main_task):
    """Test creating task without authentication fails"""
    payload = {
        "main_task": sample_main_task
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload
    )

    assert response.status_code == 403


def test_create_task_main_task_parent_id_ignored(auth_headers, sample_main_task, patch_crud_for_testing, test_project):
    """Test that parent_id in main_task is ignored and set to None"""
    # Try to set parent_id for main task (should be ignored)
    sample_main_task["parent_id"] = "some-fake-parent-id"

    payload = {
        "main_task": sample_main_task
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Parent ID should be None regardless of what was sent
    assert data["main_task"]["parent_id"] is None
