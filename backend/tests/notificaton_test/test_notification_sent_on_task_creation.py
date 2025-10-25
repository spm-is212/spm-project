from backend.tests.conftest import client
import json

def test_notification_sent_on_task_creation(
    auth_headers, sample_main_task, mock_notification_service,
    patch_crud_for_testing, test_project
):
    """Ensure a notification is triggered when a task is created"""
    payload = {"main_task": sample_main_task}

    response = client.post(
        "/api/tasks/createTask",
        data={"task_data": json.dumps(payload)},
        headers=auth_headers
    )

    print(response.status_code, response.text)
    assert response.status_code == 200

    mock_notification_service.assert_called_once()
    call_args = mock_notification_service.call_args.kwargs

    assert call_args["action"] == "created"
    assert "task" in call_args
    assert call_args["task"]["title"] == sample_main_task["title"]
