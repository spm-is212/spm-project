"""
Tests for SupabaseCRUD wrapper
"""
import pytest
from unittest.mock import Mock
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD


class TestSupabaseCRUD:
    """Test SupabaseCRUD methods"""

    @pytest.fixture
    def mock_client(self):
        """Mock Supabase client"""
        client = Mock()
        return client

    @pytest.fixture
    def crud_with_mock(self, mock_client, monkeypatch):
        """SupabaseCRUD instance with mocked client"""
        crud = SupabaseCRUD()
        crud.client = mock_client
        return crud

    def test_select_with_order_by_ascending(self, crud_with_mock, mock_client):
        """Test select with order_by in ascending order"""
        # Arrange
        mock_table = Mock()
        mock_select = Mock()
        mock_order = Mock()
        mock_result = Mock()
        mock_result.data = [{"id": 1}, {"id": 2}]

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_order
        mock_order.execute.return_value = mock_result

        # Act
        result = crud_with_mock.select("tasks", order_by="created_at", ascending=True)

        # Assert
        mock_select.order.assert_called_once_with("created_at", desc=False)
        assert result == [{"id": 1}, {"id": 2}]

    def test_select_with_order_by_descending(self, crud_with_mock, mock_client):
        """Test select with order_by in descending order"""
        # Arrange
        mock_table = Mock()
        mock_select = Mock()
        mock_order = Mock()
        mock_result = Mock()
        mock_result.data = [{"id": 2}, {"id": 1}]

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_order
        mock_order.execute.return_value = mock_result

        # Act
        result = crud_with_mock.select("tasks", order_by="created_at", ascending=False)

        # Assert
        mock_select.order.assert_called_once_with("created_at", desc=True)
        assert result == [{"id": 2}, {"id": 1}]

    def test_select_with_limit(self, crud_with_mock, mock_client):
        """Test select with limit parameter"""
        # Arrange
        mock_table = Mock()
        mock_select = Mock()
        mock_limit = Mock()
        mock_result = Mock()
        mock_result.data = [{"id": 1}]

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.limit.return_value = mock_limit
        mock_limit.execute.return_value = mock_result

        # Act
        result = crud_with_mock.select("tasks", limit=10)

        # Assert
        mock_select.limit.assert_called_once_with(10)
        assert result == [{"id": 1}]

    def test_insert_many(self, crud_with_mock, mock_client):
        """Test insert_many method"""
        # Arrange
        mock_table = Mock()
        mock_insert = Mock()
        mock_result = Mock()
        mock_result.data = [{"id": 1}, {"id": 2}]

        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_result

        data = [{"name": "Task 1"}, {"name": "Task 2"}]

        # Act
        result = crud_with_mock.insert_many("tasks", data)

        # Assert
        mock_table.insert.assert_called_once_with(data)
        assert result == [{"id": 1}, {"id": 2}]

    def test_count_with_filters(self, crud_with_mock, mock_client):
        """Test count method with filters"""
        # Arrange
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_result = Mock()
        mock_result.count = 5

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_result

        # Act
        result = crud_with_mock.count("tasks", filters={"status": "completed"})

        # Assert
        mock_table.select.assert_called_once_with("*", count="exact")
        mock_select.eq.assert_called_once_with("status", "completed")
        assert result == 5

    def test_count_without_filters(self, crud_with_mock, mock_client):
        """Test count method without filters"""
        # Arrange
        mock_table = Mock()
        mock_select = Mock()
        mock_result = Mock()
        mock_result.count = 10

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.execute.return_value = mock_result

        # Act
        result = crud_with_mock.count("tasks")

        # Assert
        mock_table.select.assert_called_once_with("*", count="exact")
        assert result == 10

    def test_exists_returns_true_when_count_greater_than_zero(self, crud_with_mock, mock_client):
        """Test exists returns True when records exist"""
        # Arrange
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_result = Mock()
        mock_result.count = 1

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_result

        # Act
        result = crud_with_mock.exists("tasks", {"id": "task-1"})

        # Assert
        assert result is True

    def test_exists_returns_false_when_count_is_zero(self, crud_with_mock, mock_client):
        """Test exists returns False when no records exist"""
        # Arrange
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_result = Mock()
        mock_result.count = 0

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_result

        # Act
        result = crud_with_mock.exists("tasks", {"id": "nonexistent"})

        # Assert
        assert result is False
