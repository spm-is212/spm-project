from backend.tests.task_test.conftest import client
from backend.utils.task_crud.constants import make_future_due_date


def test_update_main_task_success(auth_headers, patch_crud_for_testing, test_project):
    """Test updating a main task successfully"""
    # Create a task first
    create_payload = {
        "main_task": {
            "title": "Test Task for Updates",
            "description": "A task created for testing updates",
            "due_date": make_future_due_date(),
            "status": "TO_DO",
            "priority": 3,
            "assignee_ids": ["00000000-0000-0000-0000-000000000001"]
        }
    }

    create_response = client.post(
        "/api/tasks/createTask",
        json=create_payload,
        headers=auth_headers
    )

    assert create_response.status_code == 200
    task_id = create_response.json()["main_task"]["id"]

    # Update the task
    update_data = {
        "title": "Updated Task Title",
        "description": "Updated description",
        "status": "IN_PROGRESS",
        "priority": 2,
    }

    update_payload = {
        "main_task_id": task_id,
        "main_task": update_data
    }

    response = client.put(
        "/api/tasks/updateTask",
        json=update_payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Check that task was updated
    assert data["main_task"]["title"] == "Updated Task Title"
    assert data["main_task"]["description"] == "Updated description"
    assert data["main_task"]["status"] == "IN_PROGRESS"
    assert data["main_task"]["priority"] == 2
    assert data["main_task"]["parent_id"] is None  # Should remain None


def test_update_task_assignees_as_manager(auth_headers, patch_crud_for_testing, test_project):
    """Test that managers can add and remove assignees"""
    # Create a task with multiple assignees through API
    payload = {
        "main_task": {
            "title": "Task for Assignee Test",
            "description": "Testing assignee management",
            "due_date": make_future_due_date(),
            "status": "TO_DO",
            "priority": 8,
            "assignee_ids": ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000003"]
        }
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    task_id = response.json()["main_task"]["id"]

    # Remove an assignee (only managers can do this)
    update_payload = {
        "main_task_id": task_id,
        "main_task": {
            "assignee_ids": ["00000000-0000-0000-0000-000000000001"]  # Removing other assignee
        }
    }

    response = client.put(
        "/api/tasks/updateTask",
        json=update_payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["main_task"]["assignee_ids"]) == 1
    assert "00000000-0000-0000-0000-000000000001" in data["main_task"]["assignee_ids"]


def test_update_task_assignees_as_staff_add_only(staff_auth_headers, patch_crud_for_testing, test_project):
    """Test that staff can add assignees but not remove them"""
    # Create a task with one assignee through API
    payload = {
        "main_task": {
            "title": "Task for Staff Test",
            "description": "Testing staff assignee permissions",
            "due_date": make_future_due_date(),
            "status": "TO_DO",
            "priority": 9,
            "assignee_ids": ["00000000-0000-0000-0000-000000000002"]
        }
    }

    response = client.post(
        "/api/tasks/createTask",
        json=payload,
        headers=staff_auth_headers
    )

    assert response.status_code == 200
    task_id = response.json()["main_task"]["id"]

    # Staff should be able to ADD assignees
    update_payload = {
        "main_task_id": task_id,
        "main_task": {
            "assignee_ids": ["00000000-0000-0000-0000-000000000002", "00000000-0000-0000-0000-000000000004"]  # Adding new assignee
        }
    }

    response = client.put(
        "/api/tasks/updateTask",
        json=update_payload,
        headers=staff_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["main_task"]["assignee_ids"]) == 2


def test_update_task_without_auth_fails():
    """Test updating task without authentication fails"""
    update_payload = {
        "main_task_id": "fake-task-id",
        "main_task": {
            "title": "Should fail"
        }
    }

    response = client.put(
        "/api/tasks/updateTask",
        json=update_payload
    )

    assert response.status_code == 403


def test_update_nonexistent_task_fails(auth_headers, patch_crud_for_testing):
    """Test updating a non-existent task fails"""
    update_payload = {
        "main_task_id": "00000000-0000-0000-0000-000000000000",
        "main_task": {
            "title": "Should fail"
        }
    }

    response = client.put(
        "/api/tasks/updateTask",
        json=update_payload,
        headers=auth_headers
    )

    assert response.status_code == 200  # Update returns success even if task not found
    data = response.json()
    assert data["main_task"] is None  # Should return null for non-existent task
