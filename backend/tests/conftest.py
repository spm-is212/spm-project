import pytest
from pathlib import Path
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
