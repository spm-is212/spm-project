from backend.tests.conftest import client


def test_generate_task_completion_report_success(hr_admin_auth_headers, task_completion_request_data, patch_crud_for_testing, test_project):
    """Test generating task completion report with HR & admin user"""
    response = client.post(
        "/api/reports/taskCompletion",
        json=task_completion_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "scope_type" in data
    assert data["scope_type"] == "project"
    assert "scope_id" in data
    assert "scope_name" in data
    assert "total_tasks" in data
    assert "tasks" in data
    assert isinstance(data["tasks"], list)


def test_generate_task_completion_report_staff_scope(hr_admin_auth_headers, patch_crud_for_testing):
    """Test generating task completion report by staff member"""
    request_data = {
        "scope_type": "staff",
        "scope_id": "00000000-0000-0000-0000-000000000001",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "export_format": "xlsx"
    }

    response = client.post(
        "/api/reports/taskCompletion",
        json=request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scope_type"] == "staff"


def test_generate_task_completion_report_without_auth_fails():
    """Test that generating report without authentication fails"""
    request_data = {
        "scope_type": "project",
        "scope_id": "proj-123",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31"
    }

    response = client.post(
        "/api/reports/taskCompletion",
        json=request_data
    )

    assert response.status_code == 403


def test_generate_task_completion_report_non_hr_user_denied(non_hr_auth_headers, task_completion_request_data):
    """Test that non-HR users are denied access to reports"""
    response = client.post(
        "/api/reports/taskCompletion",
        json=task_completion_request_data,
        headers=non_hr_auth_headers
    )

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_export_task_completion_report_xlsx(hr_admin_auth_headers, task_completion_request_data, patch_crud_for_testing, test_project):
    """Test exporting task completion report as Excel file"""
    task_completion_request_data["export_format"] = "xlsx"

    response = client.post(
        "/api/reports/taskCompletion/export",
        json=task_completion_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment" in response.headers["content-disposition"]
    assert ".xlsx" in response.headers["content-disposition"]
    assert len(response.content) > 0


def test_export_task_completion_report_pdf(hr_admin_auth_headers, task_completion_request_data, patch_crud_for_testing, test_project):
    """Test exporting task completion report as PDF file"""
    task_completion_request_data["export_format"] = "pdf"

    response = client.post(
        "/api/reports/taskCompletion/export",
        json=task_completion_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert ".pdf" in response.headers["content-disposition"]
    assert len(response.content) > 0
    assert response.content[:4] == b'%PDF'


def test_export_task_completion_report_invalid_format(hr_admin_auth_headers, task_completion_request_data):
    """Test that invalid export format returns 422 (Pydantic validation)"""
    task_completion_request_data["export_format"] = "csv"

    response = client.post(
        "/api/reports/taskCompletion/export",
        json=task_completion_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 422


def test_export_task_completion_report_without_auth_fails(task_completion_request_data):
    """Test that exporting without authentication fails"""
    response = client.post(
        "/api/reports/taskCompletion/export",
        json=task_completion_request_data
    )

    assert response.status_code == 403


def test_export_task_completion_report_non_hr_user_denied(non_hr_auth_headers, task_completion_request_data):
    """Test that non-HR users cannot export reports"""
    response = client.post(
        "/api/reports/taskCompletion/export",
        json=task_completion_request_data,
        headers=non_hr_auth_headers
    )

    assert response.status_code == 403


def test_task_completion_report_date_validation(hr_admin_auth_headers):
    """Test that end_date before start_date is rejected"""
    request_data = {
        "scope_type": "project",
        "scope_id": "proj-123",
        "start_date": "2025-12-31",
        "end_date": "2025-01-01",
        "export_format": "xlsx"
    }

    response = client.post(
        "/api/reports/taskCompletion",
        json=request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 422
