from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.routers.task import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@patch("backend.routers.task.get_current_user")
@patch("backend.routers.task.create_task")
def test_create_task_success(mock_create_task, mock_get_current_user):
    mock_get_current_user.return_value = {"sub": 123, "role": "staff"}
    mock_create_task.return_value = None

    task_data = {"title": "Test Task", "description": "Test Description"}

    response = client.post("/api/tasks/createTask", json=task_data)

    assert response.status_code == 200
    mock_get_current_user.assert_called_once()
    mock_create_task.assert_called_once()

    args = mock_create_task.call_args[0]
    assert args[0] == 123
    assert args[1].title == "Test Task"
    assert args[1].description == "Test Description"
    assert len(str(args[2])) == 36


@patch("backend.routers.task.get_current_user")
def test_create_task_auth_error(mock_get_current_user):
    mock_get_current_user.side_effect = Exception("Invalid token")

    task_data = {"title": "Test Task", "description": "Test Description"}

    response = client.post("/api/tasks/createTask", json=task_data)

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


@patch("backend.routers.task.get_current_user")
@patch("backend.routers.task.update_task")
def test_update_task_success(mock_update_task, mock_get_current_user):
    mock_get_current_user.return_value = {"sub": 123, "role": "staff"}
    mock_update_task.return_value = None

    task_data = {
        "task_uuid": "abc-123-def",
        "title": "Updated Task",
        "description": "Updated Description",
    }

    response = client.put("/api/tasks/updateTask", json=task_data)

    assert response.status_code == 200
    mock_get_current_user.assert_called_once()
    mock_update_task.assert_called_once()

    args = mock_update_task.call_args[0]
    assert args[0] == 123
    assert args[1] == "abc-123-def"
    assert args[2].title == "Updated Task"
    assert args[2].description == "Updated Description"


@patch("backend.routers.task.get_current_user")
def test_update_task_auth_error(mock_get_current_user):
    mock_get_current_user.side_effect = Exception("Invalid token")

    task_data = {"task_uuid": "abc-123-def", "title": "Updated Task"}

    response = client.put("/api/tasks/updateTask", json=task_data)

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_create_task_validation_error():
    task_data = {"description": "Test Description"}

    response = client.post("/api/tasks/createTask", json=task_data)

    assert response.status_code == 422


def test_update_task_validation_error():
    task_data = {"title": "Updated Task"}

    response = client.put("/api/tasks/updateTask", json=task_data)

    assert response.status_code == 422
