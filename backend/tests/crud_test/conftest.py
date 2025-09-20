import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_supabase_client():
    """Mock the Supabase client connection"""
    with patch("backend.wrappers.supabase_wrapper.supabase_client.create_client") as mock_create:
        mock_client = Mock()
        mock_create.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_supabase_crud():
    """Mock the CRUD operations"""
    with patch("backend.routers.crud_test.SupabaseCRUD") as mock_crud_class:
        mock_crud_instance = Mock()
        mock_crud_class.return_value = mock_crud_instance
        yield mock_crud_instance
