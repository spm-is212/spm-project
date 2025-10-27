from backend.tests.conftest import client


def test_generate_team_summary_report_success(hr_admin_auth_headers, team_summary_request_data, patch_crud_for_testing):
    """Test generating team summary report with HR & admin user"""
    response = client.post(
        "/api/reports/teamSummary",
        json=team_summary_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "scope_type" in data
    assert data["scope_type"] == "department"
    assert "scope_id" in data
    assert "scope_name" in data
    assert "time_frame" in data
    assert data["time_frame"] == "weekly"
    assert "total_staff" in data
    assert "staff_summaries" in data
    assert isinstance(data["staff_summaries"], list)


def test_generate_team_summary_report_project_scope(hr_admin_auth_headers, patch_crud_for_testing, test_project):
    """Test generating team summary report by project"""
    request_data = {
        "scope_type": "project",
        "scope_id": "00000000-0000-0000-0000-000000000001",
        "time_frame": "monthly",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "export_format": "xlsx"
    }

    response = client.post(
        "/api/reports/teamSummary",
        json=request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scope_type"] == "project"
    assert data["time_frame"] == "monthly"


def test_generate_team_summary_report_without_auth_fails():
    """Test that generating report without authentication fails"""
    request_data = {
        "scope_type": "department",
        "scope_id": "Engineering",
        "time_frame": "weekly",
        "start_date": "2025-01-01",
        "end_date": "2025-01-07"
    }

    response = client.post(
        "/api/reports/teamSummary",
        json=request_data
    )

    assert response.status_code == 403


def test_generate_team_summary_report_non_hr_user_denied(non_hr_auth_headers, team_summary_request_data):
    """Test that non-HR users are denied access to reports"""
    response = client.post(
        "/api/reports/teamSummary",
        json=team_summary_request_data,
        headers=non_hr_auth_headers
    )

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_export_team_summary_report_xlsx(hr_admin_auth_headers, team_summary_request_data, patch_crud_for_testing):
    """Test exporting team summary report as Excel file"""
    team_summary_request_data["export_format"] = "xlsx"

    response = client.post(
        "/api/reports/teamSummary/export",
        json=team_summary_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment" in response.headers["content-disposition"]
    assert ".xlsx" in response.headers["content-disposition"]
    assert len(response.content) > 0


def test_export_team_summary_report_pdf(hr_admin_auth_headers, team_summary_request_data, patch_crud_for_testing):
    """Test exporting team summary report as PDF file"""
    team_summary_request_data["export_format"] = "pdf"

    response = client.post(
        "/api/reports/teamSummary/export",
        json=team_summary_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert ".pdf" in response.headers["content-disposition"]
    assert len(response.content) > 0
    assert response.content[:4] == b'%PDF'


def test_export_team_summary_report_invalid_format(hr_admin_auth_headers, team_summary_request_data):
    """Test that invalid export format returns 422 (Pydantic validation)"""
    team_summary_request_data["export_format"] = "csv"

    response = client.post(
        "/api/reports/teamSummary/export",
        json=team_summary_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 422


def test_export_team_summary_report_without_auth_fails(team_summary_request_data):
    """Test that exporting without authentication fails"""
    response = client.post(
        "/api/reports/teamSummary/export",
        json=team_summary_request_data
    )

    assert response.status_code == 403


def test_export_team_summary_report_non_hr_user_denied(non_hr_auth_headers, team_summary_request_data):
    """Test that non-HR users cannot export reports"""
    response = client.post(
        "/api/reports/teamSummary/export",
        json=team_summary_request_data,
        headers=non_hr_auth_headers
    )

    assert response.status_code == 403


def test_team_summary_report_date_validation(hr_admin_auth_headers):
    """Test that end_date before start_date is rejected"""
    request_data = {
        "scope_type": "department",
        "scope_id": "Engineering",
        "time_frame": "weekly",
        "start_date": "2025-12-31",
        "end_date": "2025-01-01",
        "export_format": "xlsx"
    }

    response = client.post(
        "/api/reports/teamSummary",
        json=request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 422


def test_staff_summaries_structure(hr_admin_auth_headers, team_summary_request_data, patch_crud_for_testing):
    """Test that staff summaries have correct structure"""
    response = client.post(
        "/api/reports/teamSummary",
        json=team_summary_request_data,
        headers=hr_admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    if len(data["staff_summaries"]) > 0:
        summary = data["staff_summaries"][0]
        assert "staff_name" in summary
        assert "blocked" in summary
        assert "in_progress" in summary
        assert "completed" in summary
        assert "overdue" in summary
        assert "total_tasks" in summary
