import pytest
from unittest.mock import Mock
from backend.utils.task_crud.read import TaskReader


class TestTaskReader:
    """Unit tests for TaskReader class with 100% coverage"""

    @pytest.fixture
    def mock_crud(self):
        """Mock CRUD instance"""
        return Mock()

    @pytest.fixture
    def mock_user_manager(self):
        """Mock UserManager instance"""
        return Mock()

    @pytest.fixture
    def sample_tasks(self):
        """Sample task data for testing"""
        return [
            {
                "id": "task-1",
                "title": "Task 1",
                "owner_user_id": "user-1",
                "assignee_ids": ["user-1", "user-2"],
                "parent_id": None
            },
            {
                "id": "task-2",
                "title": "Task 2",
                "owner_user_id": "user-3",
                "assignee_ids": ["user-3"],
                "parent_id": None
            },
            {
                "id": "task-3",
                "title": "Task 3",
                "owner_user_id": "user-4",
                "assignee_ids": ["user-1", "user-4"],
                "parent_id": "task-1"
            }
        ]

    @pytest.fixture
    def sample_users(self):
        """Sample user data for testing"""
        return {
            "dept_users": [
                {"id": "user-1", "email": "user1@test.com"},
                {"id": "user-2", "email": "user2@test.com"}
            ],
            "team_users": [
                {"id": "user-1", "email": "user1@test.com"},
                {"id": "user-3", "email": "user3@test.com"}
            ]
        }

    def test_managing_director_can_view_all_tasks(self, mock_crud, mock_user_manager, sample_tasks):
        """Test that managing directors can view all tasks"""
        # Arrange
        mock_crud.select.return_value = sample_tasks

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="manager-1",
            user_role="managing_director",
            user_departments=["dept1"]
        )

        # Assert
        assert result == sample_tasks
        mock_crud.select.assert_called_once_with("tasks")

    def test_director_can_view_department_tasks(self, mock_crud, mock_user_manager, sample_tasks, sample_users):
        """Test that directors can view all tasks in their department"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        mock_user_manager.get_users_by_department.return_value = sample_users["dept_users"]

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="director-1",
            user_role="director",
            user_departments=["dept1"]
        )

        # Assert
        mock_user_manager.get_users_by_department.assert_called_once_with("dept1")
        # Should return tasks owned by users in the department (user-1, user-2)
        expected_tasks = [task for task in sample_tasks if task["owner_user_id"] in ["user-1", "user-2"]]
        assert result == expected_tasks

    @pytest.mark.skip(reason="Teams feature removed")
    def test_privileged_team_sales_manager_can_view_department_tasks(self, mock_crud, mock_user_manager, sample_tasks, sample_users):
        """Test that sales manager team can view all tasks in their department"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        mock_user_manager.get_users_by_department.return_value = sample_users["dept_users"]

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="sales-1",
            user_role="staff",
            user_departments=["dept1"]
        )

        # Assert
        mock_user_manager.get_users_by_department.assert_called_once_with("dept1")
        expected_tasks = [task for task in sample_tasks if task["owner_user_id"] in ["user-1", "user-2"]]
        assert result == expected_tasks

    @pytest.mark.skip(reason="Teams feature removed")
    def test_privileged_team_finance_managers_can_view_department_tasks(self, mock_crud, mock_user_manager, sample_tasks, sample_users):
        """Test that finance managers team can view all tasks in their department"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        mock_user_manager.get_users_by_department.return_value = sample_users["dept_users"]

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="finance-1",
            user_role="manager",
            user_departments=["dept1"]
        )

        # Assert
        mock_user_manager.get_users_by_department.assert_called_once_with("dept1")
        expected_tasks = [task for task in sample_tasks if task["owner_user_id"] in ["user-1", "user-2"]]
        assert result == expected_tasks

    def test_regular_staff_can_view_team_and_assigned_tasks(self, mock_crud, mock_user_manager, sample_tasks, sample_users):
        """Test that regular staff can view assigned tasks and parent tasks of assigned subtasks"""
        # Arrange
        mock_crud.select.return_value = sample_tasks

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="user-1",
            user_role="staff",
            user_departments=["dept1"]
        )

        # Assert
        # Should return:
        # - task-1: user-1 is assigned to it directly
        # - task-3: user-1 is assigned to it (it's a subtask of task-1)
        expected_task_ids = {"task-1", "task-3"}
        result_task_ids = {task["id"] for task in result}
        assert result_task_ids == expected_task_ids

    def test_regular_staff_without_teams_only_gets_assigned_tasks(self, mock_crud, mock_user_manager, sample_tasks):
        """Test that staff without teams only get tasks they're assigned to"""
        # Arrange
        mock_crud.select.return_value = sample_tasks

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="user-1",
            user_role="staff",
            user_departments=["dept1"]
        )

        # Assert
        # Should return task-1 (user-1 is assigned) and task-3 (user-1 is assigned)
        expected_task_ids = {"task-1", "task-3"}
        result_task_ids = {task["id"] for task in result}
        assert result_task_ids == expected_task_ids

    def test_empty_departments_for_director_returns_empty(self, mock_crud, mock_user_manager):
        """Test that directors with no departments return empty results"""
        # Arrange
        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="director-1",
            user_role="director",
            user_departments=[]  # No departments
        )

        # Assert
        assert result == []

    def test_no_users_in_department_returns_empty(self, mock_crud, mock_user_manager, sample_tasks):
        """Test that departments with no users return empty results"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        mock_user_manager.get_users_by_department.return_value = []  # No users

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="director-1",
            user_role="director",
            user_departments=["empty-dept"]
        )

        # Assert
        assert result == []

    def test_no_users_in_team_returns_assigned_tasks_only(self, mock_crud, mock_user_manager, sample_tasks):
        """Test that teams with no users return only assigned tasks"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        mock_user_manager.get_users_by_team.return_value = []  # No team users

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="user-1",
            user_role="staff",
            user_departments=["dept1"]
        )

        # Assert
        # Should return task-1 (user-1 is assigned) and task-3 (user-1 is assigned)
        expected_task_ids = {"task-1", "task-3"}
        result_task_ids = {task["id"] for task in result}
        assert result_task_ids == expected_task_ids

    def test_get_task_by_id_returns_accessible_task(self, mock_crud, mock_user_manager, sample_tasks):
        """Test getting a specific task by ID that user has access to"""
        # Arrange
        mock_crud.select.return_value = sample_tasks

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_task_by_id(
            task_id="task-1",
            user_id="manager-1",
            user_role="managing_director",
            user_departments=["dept1"]
        )

        # Assert
        assert result["id"] == "task-1"
        assert result["title"] == "Task 1"

    def test_get_task_by_id_returns_none_for_inaccessible_task(self, mock_crud, mock_user_manager):
        """Test getting a task by ID that user doesn't have access to"""
        # Arrange
        mock_crud.select.return_value = []  # User has no accessible tasks
        mock_user_manager.get_users_by_team.return_value = []

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_task_by_id(
            task_id="task-1",
            user_id="user-5",
            user_role="staff",
            user_departments=["dept1"]
        )

        # Assert
        assert result is None

    def test_get_task_by_id_returns_none_for_nonexistent_task(self, mock_crud, mock_user_manager, sample_tasks):
        """Test getting a task by ID that doesn't exist"""
        # Arrange
        mock_crud.select.return_value = sample_tasks

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_task_by_id(
            task_id="nonexistent-task",
            user_id="manager-1",
            user_role="managing_director",
            user_departments=["dept1"]
        )

        # Assert
        assert result is None

    @pytest.mark.skip(reason="Teams feature removed")
    def test_is_privileged_team_returns_true_for_sales_manager(self):
        """Test privileged team check for sales manager"""
        # Arrange
        reader = TaskReader()

        # Act & Assert
        assert reader._is_privileged_team(["sales manager", "other team"])

    @pytest.mark.skip(reason="Teams feature removed")
    def test_is_privileged_team_returns_true_for_finance_managers(self):
        """Test privileged team check for finance managers"""
        # Arrange
        reader = TaskReader()

        # Act & Assert
        assert reader._is_privileged_team(["finance managers"])

    @pytest.mark.skip(reason="Teams feature removed")
    def test_is_privileged_team_returns_false_for_regular_team(self):
        """Test privileged team check for regular team"""
        # Arrange
        reader = TaskReader()

        # Act & Assert
        assert not reader._is_privileged_team(["regular team", "another team"])

    @pytest.mark.skip(reason="Teams feature removed")
    def test_is_privileged_team_returns_false_for_empty_teams(self):
        """Test privileged team check for empty teams"""
        # Arrange
        reader = TaskReader()

        # Act & Assert
        assert not reader._is_privileged_team([])

    @pytest.mark.skip(reason="Teams feature removed")
    def test_multiple_departments_for_director(self, mock_crud, mock_user_manager, sample_tasks, sample_users):
        """Test that directors can view tasks from multiple departments"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        # Different users for each department
        mock_user_manager.get_users_by_department.side_effect = [
            [{"id": "user-1", "email": "user1@test.com"}],  # dept1
            [{"id": "user-3", "email": "user3@test.com"}]   # dept2
        ]

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="director-1",
            user_role="director",
            user_departments=["dept1", "dept2"]  # Multiple departments
        )

        # Assert
        assert mock_user_manager.get_users_by_department.call_count == 2
        # Should return tasks owned by user-1 (from dept1) and user-3 (from dept2)
        expected_task_ids = {"task-1", "task-2"}
        result_task_ids = {task["id"] for task in result}
        assert result_task_ids == expected_task_ids

    def test_regular_staff_can_see_assigned_task_from_different_team(self, mock_crud, mock_user_manager, sample_tasks):
        """Test that regular staff can see tasks they're assigned to even from different teams"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        mock_user_manager.get_users_by_team.return_value = []  # User not in any team with other users

        reader = TaskReader()
        reader.crud = mock_crud
        reader.user_manager = mock_user_manager

        # Act
        result = reader.get_tasks_for_user(
            user_id="user-2",  # user-2 is assigned to task-1 but not in the same team as owner
            user_role="staff",
            user_departments=["dept2"]
        )

        # Assert
        # Should return task-1 because user-2 is assigned to it
        expected_task_ids = {"task-1"}
        result_task_ids = {task["id"] for task in result}
        assert result_task_ids == expected_task_ids

    def test_get_all_tasks_method(self, mock_crud, sample_tasks):
        """Test the _get_all_tasks private method"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        reader = TaskReader()
        reader.crud = mock_crud

        # Act
        result = reader._get_all_tasks()

        # Assert
        assert result == sample_tasks
        mock_crud.select.assert_called_once_with("tasks")

    def test_get_assigned_tasks_method(self, mock_crud, sample_tasks):
        """Test the _get_assigned_tasks private method"""
        # Arrange
        mock_crud.select.return_value = sample_tasks
        reader = TaskReader()
        reader.crud = mock_crud

        # Act
        result = reader._get_assigned_tasks("user-1")

        # Assert
        # Should return tasks where user-1 is in assignee_ids
        expected_task_ids = {"task-1", "task-3"}
        result_task_ids = {task["id"] for task in result}
        assert result_task_ids == expected_task_ids
