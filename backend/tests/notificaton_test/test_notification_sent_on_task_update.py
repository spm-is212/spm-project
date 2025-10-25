import json


def test_notification_sent_on_task_update(
    client, auth_headers, sample_main_task, mock_notification_service,
    patch_crud_for_testing, test_project
):
    """Ensure a notification is triggered when a task is updated"""
    # --- Step 1: Create a task first ---
    create_payload = {"main_task": sample_main_task}
    create_resp = client.post(
        "/api/tasks/createTask",
        data={"task_data": json.dumps(create_payload)},
        headers=auth_headers
    )
    assert create_resp.status_code == 200
    created_task = create_resp.json()["main_task"]

    # --- Step 2: Update the task ---
    update_payload = {
        "main_task_id": created_task["id"],
        "main_task": {
            "title": "Updated Task Title",
            "status": "IN_PROGRESS"
        }
    }

    update_resp = client.put(
        "/api/tasks/updateTask",
        data={"task_data": json.dumps(update_payload)},
        headers=auth_headers
    )

    print(update_resp.status_code, update_resp.text)
    assert update_resp.status_code == 200

    # --- Step 3: Verify notification call ---
    # Verify the notification service was called
    mock_notification_service.notify_task_event.assert_called()

    # Get all calls and find the one with action="updated"
    calls = mock_notification_service.notify_task_event.call_args_list
    update_call = None
    for call in calls:
        if call.kwargs.get("action") == "updated":
            update_call = call
            break

    # Verify we found an update notification
    assert update_call is not None, f"No notification with action='updated' was found. Actions: {[c.kwargs.get('action') for c in calls]}"

    # Verify the update notification details
    assert "task" in update_call.kwargs
    assert update_call.kwargs["task"]["id"] == created_task["id"]
    assert update_call.kwargs["task"]["title"] == "Updated Task Title"
