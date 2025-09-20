def test_read_table_success(client, mock_supabase_crud):
    mock_supabase_crud.select.return_value = [{"id": 1, "name": "test"}]

    response = client.post("/api/crud/read", json={
        "table_name": "users",
        "columns": "*"
    })

    assert response.status_code == 200
    assert response.json() == {"data": [{"id": 1, "name": "test"}]}
    mock_supabase_crud.select.assert_called_once_with(
        table="users",
        columns="*",
        filters=None,
        limit=None,
        order_by=None,
        ascending=True
    )


def test_read_table_with_filters(client, mock_supabase_crud):
    mock_supabase_crud.select.return_value = [{"id": 1, "name": "test"}]

    response = client.post("/api/crud/read", json={
        "table_name": "users",
        "filters": {"status": "active"},
        "limit": 10
    })

    assert response.status_code == 200
    mock_supabase_crud.select.assert_called_once_with(
        table="users",
        columns="*",
        filters={"status": "active"},
        limit=10,
        order_by=None,
        ascending=True
    )


def test_create_record_success(client, mock_supabase_crud):
    mock_supabase_crud.insert.return_value = {"id": 1, "name": "new user"}

    response = client.post("/api/crud/create", json={
        "table_name": "users",
        "data": {"name": "new user", "email": "test@example.com"}
    })

    assert response.status_code == 200
    assert response.json() == {"data": {"id": 1, "name": "new user"}}
    mock_supabase_crud.insert.assert_called_once_with(
        table="users",
        data={"name": "new user", "email": "test@example.com"}
    )


def test_update_record_success(client, mock_supabase_crud):
    mock_supabase_crud.update.return_value = [{"id": 1, "name": "updated user"}]

    response = client.post("/api/crud/update", json={
        "table_name": "users",
        "data": {"name": "updated user"},
        "filters": {"id": 1}
    })

    assert response.status_code == 200
    assert response.json() == {"data": [{"id": 1, "name": "updated user"}]}
    mock_supabase_crud.update.assert_called_once_with(
        table="users",
        data={"name": "updated user"},
        filters={"id": 1}
    )


def test_delete_record_success(client, mock_supabase_crud):
    mock_supabase_crud.delete.return_value = [{"id": 1, "name": "deleted user"}]

    response = client.post("/api/crud/delete", json={
        "table_name": "users",
        "filters": {"id": 1}
    })

    assert response.status_code == 200
    assert response.json() == {"data": [{"id": 1, "name": "deleted user"}]}
    mock_supabase_crud.delete.assert_called_once_with(
        table="users",
        filters={"id": 1}
    )


def test_count_records_success(client, mock_supabase_crud):
    mock_supabase_crud.count.return_value = 5

    response = client.post("/api/crud/count", json={
        "table_name": "users"
    })

    assert response.status_code == 200
    assert response.json() == {"count": 5}
    mock_supabase_crud.count.assert_called_once_with(
        table="users",
        filters=None
    )


def test_count_records_with_filters(client, mock_supabase_crud):
    mock_supabase_crud.count.return_value = 2

    response = client.post("/api/crud/count", json={
        "table_name": "users",
        "filters": {"status": "active"}
    })

    assert response.status_code == 200
    assert response.json() == {"count": 2}
    mock_supabase_crud.count.assert_called_once_with(
        table="users",
        filters={"status": "active"}
    )


def test_read_table_error(client, mock_supabase_crud):
    mock_supabase_crud.select.side_effect = Exception("Database error")

    response = client.post("/api/crud/read", json={
        "table_name": "users"
    })

    assert response.status_code == 500
    assert "Error reading users" in response.json()["detail"]


def test_create_record_error(client, mock_supabase_crud):
    mock_supabase_crud.insert.side_effect = Exception("Insert failed")

    response = client.post("/api/crud/create", json={
        "table_name": "users",
        "data": {"name": "test"}
    })

    assert response.status_code == 500
    assert "Error creating record in users" in response.json()["detail"]
