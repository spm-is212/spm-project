import pytest
from datetime import date, timedelta
from backend.utils.security import create_access_token


@pytest.fixture
def hr_admin_auth_headers():
    """Create authentication headers for HR & admin department user"""
    token_data = {
        "sub": "00000000-0000-0000-0000-000000000003",
        "role": "manager",
        "departments": ["HR & admin"]
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def non_hr_auth_headers():
    """Create authentication headers for non-HR user (should be denied)"""
    token_data = {
        "sub": "00000000-0000-0000-0000-000000000004",
        "role": "staff",
        "departments": ["Engineering"]
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def task_completion_request_data():
    """Sample task completion report request data"""
    return {
        "scope_type": "project",
        "scope_id": "00000000-0000-0000-0000-000000000001",
        "start_date": (date.today() - timedelta(days=30)).isoformat(),
        "end_date": (date.today() + timedelta(days=30)).isoformat(),
        "export_format": "xlsx"
    }


@pytest.fixture
def team_summary_request_data():
    """Sample team summary report request data"""
    return {
        "scope_type": "department",
        "scope_id": "Engineering",
        "time_frame": "weekly",
        "start_date": (date.today() - timedelta(days=7)).isoformat(),
        "end_date": date.today().isoformat(),
        "export_format": "xlsx"
    }


@pytest.fixture
def logged_time_request_data():
    """Sample logged time report request data"""
    return {
        "scope_type": "project",
        "scope_id": "00000000-0000-0000-0000-000000000001",
        "start_date": (date.today() - timedelta(days=30)).isoformat(),
        "end_date": date.today().isoformat(),
        "export_format": "xlsx"
    }
