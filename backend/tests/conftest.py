import pytest
from pathlib import Path
from unittest.mock import patch
from dotenv import load_dotenv
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

# Load environment variables for testing from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment - initialize database connections and verify test tables exist"""
    crud = SupabaseCRUD()

    # Verify test tables exist
    try:
        crud.client.table("tasks_test").select("*").limit(1).execute()
        crud.client.table("users_test").select("*").limit(1).execute()
        print("Test tables verified")
    except Exception as e:
        print("Test tables not found. Run: npx supabase db push")
        raise e

    # Create default test project if it doesn't exist (in the real projects table, not test)
    try:
        default_project = {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "Default Test Project",
            "description": "Default project for tests",
            "collaborator_ids": []  # Empty collaborators for test project
        }
        # Insert directly into projects table (not projects_test since it doesn't exist)
        # The tasks table has FK to projects, not projects_test
        # Use insert with on_conflict to handle if it already exists
        crud.client.table("projects").insert(default_project, upsert=True).execute()
        print("Default test project created/verified in projects table")
    except Exception as e:
        print(f"Warning: Could not create default test project: {e}")

    yield

    # Session cleanup - remove all test data
    try:
        crud.client.table("tasks_test").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        crud.client.table("users_test").delete().neq("uuid", "00000000-0000-0000-0000-000000000000").execute()
    except Exception:
        pass


@pytest.fixture
def clean_test_database():
    """Clean test database before and after each test"""
    crud = SupabaseCRUD()

    # Clean up test tables before test
    try:
        crud.client.table("tasks_test").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        crud.client.table("users_test").delete().neq("uuid", "00000000-0000-0000-0000-000000000000").execute()
    except Exception:
        pass

    yield

    # Clean up test tables after test
    try:
        crud.client.table("tasks_test").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        crud.client.table("users_test").delete().neq("uuid", "00000000-0000-0000-0000-000000000000").execute()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def mock_notification_service():
    """
    Automatically mock NotificationService for all tests to prevent real email sending.
    """
    with patch("backend.utils.task_crud.create.NotificationService") as MockNotifCreate, \
         patch("backend.utils.task_crud.update.NotificationService") as MockNotifUpdate:
        mock_instance = MockNotifCreate.return_value
        mock_instance.notify_task_event.return_value = None

        # Make both point to the same mock instance
        MockNotifUpdate.return_value = mock_instance

        yield mock_instance
