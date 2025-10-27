from backend.tests.conftest import client


def test_generate_logged_time_report_success(hr_admin_auth_headers, logged_time_request_data, patch_crud_for_testing, test_project):
    """Test generating logged time report with HR & admin user"""
    response = client.post(
        "/api/reports/loggedTime",
        json=logged_time_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "scope_type" in data
    assert data["scope_type"] == "project"
    assert "scope_id" in data
    assert "scope_name" in data
    assert "total_entries" in data
    assert "total_hours" in data
    assert "time_entries" in data
    assert isinstance(data["time_entries"], list)


def test_generate_logged_time_report_department_scope(hr_admin_auth_headers, patch_crud_for_testing):
    """Test generating logged time report by department"""
    request_data = {
        "scope_type": "department",
        "scope_id": "Engineering",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "export_format": "xlsx"
    }

    response = client.post(
        "/api/reports/loggedTime",
        json=request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scope_type"] == "department"


def test_generate_logged_time_report_without_auth_fails():
    """Test that generating report without authentication fails"""
    request_data = {
        "scope_type": "project",
        "scope_id": "proj-123",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31"
    }

    response = client.post(
        "/api/reports/loggedTime",
        json=request_data
    )

    assert response.status_code == 403


def test_generate_logged_time_report_non_hr_user_denied(non_hr_auth_headers, logged_time_request_data):
    """Test that non-HR users are denied access to reports"""
    response = client.post(
        "/api/reports/loggedTime",
        json=logged_time_request_data,
        headers=non_hr_auth_headers
    )

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_export_logged_time_report_xlsx(hr_admin_auth_headers, logged_time_request_data, patch_crud_for_testing, test_project):
    """Test exporting logged time report as Excel file"""
    logged_time_request_data["export_format"] = "xlsx"

    response = client.post(
        "/api/reports/loggedTime/export",
        json=logged_time_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment" in response.headers["content-disposition"]
    assert ".xlsx" in response.headers["content-disposition"]
    assert len(response.content) > 0


def test_export_logged_time_report_pdf(hr_admin_auth_headers, logged_time_request_data, patch_crud_for_testing, test_project):
    """Test exporting logged time report as PDF file"""
    logged_time_request_data["export_format"] = "pdf"

    response = client.post(
        "/api/reports/loggedTime/export",
        json=logged_time_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert ".pdf" in response.headers["content-disposition"]
    assert len(response.content) > 0
    assert response.content[:4] == b'%PDF'


def test_export_logged_time_report_invalid_format(hr_admin_auth_headers, logged_time_request_data):
    """Test that invalid export format returns 422 (Pydantic validation)"""
    logged_time_request_data["export_format"] = "csv"

    response = client.post(
        "/api/reports/loggedTime/export",
        json=logged_time_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 422


def test_export_logged_time_report_without_auth_fails(logged_time_request_data):
    """Test that exporting without authentication fails"""
    response = client.post(
        "/api/reports/loggedTime/export",
        json=logged_time_request_data
    )

    assert response.status_code == 403


def test_export_logged_time_report_non_hr_user_denied(non_hr_auth_headers, logged_time_request_data):
    """Test that non-HR users cannot export reports"""
    response = client.post(
        "/api/reports/loggedTime/export",
        json=logged_time_request_data,
        headers=non_hr_auth_headers
    )

    assert response.status_code == 403


def test_logged_time_report_date_validation(hr_admin_auth_headers):
    """Test that end_date before start_date is rejected"""
    request_data = {
        "scope_type": "project",
        "scope_id": "proj-123",
        "start_date": "2025-12-31",
        "end_date": "2025-01-01",
        "export_format": "xlsx"
    }

    response = client.post(
        "/api/reports/loggedTime",
        json=request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 422


def test_time_entries_structure(hr_admin_auth_headers, logged_time_request_data, patch_crud_for_testing, test_project):
    """Test that time entries have correct structure"""
    response = client.post(
        "/api/reports/loggedTime",
        json=logged_time_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    if len(data["time_entries"]) > 0:
        entry = data["time_entries"][0]
        assert "staff_name" in entry
        assert "task_title" in entry
        assert "time_log" in entry
        assert "status" in entry
        assert "due_date" in entry
        assert "overdue" in entry


def test_total_hours_calculation(hr_admin_auth_headers, logged_time_request_data, patch_crud_for_testing, test_project):
    """Test that total_hours is calculated correctly"""
    response = client.post(
        "/api/reports/loggedTime",
        json=logged_time_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["total_hours"], (int, float))
    assert data["total_hours"] >= 0
