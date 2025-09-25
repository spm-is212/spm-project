import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.security import create_access_token
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from datetime import date, timedelta

client = TestClient(app)


class TestReadTaskEndpoint:
    """Integration tests for the read tasks endpoint"""

    @pytest.fixture
    def managing_director_token(self):
        """Create JWT token for managing director"""
        token_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "role": "managing_director",
            "teams": ["leadership"],
            "departments": ["executive"]
        }
        return create_access_token(token_data)

    @pytest.fixture
    def director_token(self):
        """Create JWT token for director"""
        token_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440001",
            "role": "director",
            "teams": ["management"],
            "departments": ["engineering"]
        }
        return create_access_token(token_data)

    @pytest.fixture
    def privileged_team_token(self):
        """Create JWT token for sales manager (privileged team)"""
        token_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440002",
            "role": "manager",
            "teams": ["sales manager"],
            "departments": ["sales"]
        }
        return create_access_token(token_data)

    @pytest.fixture
    def regular_staff_token(self):
        """Create JWT token for regular staff"""
        token_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440003",
            "role": "staff",
            "teams": ["developers"],
            "departments": ["engineering"]
        }
        return create_access_token(token_data)

    @pytest.fixture
    def setup_test_users_and_tasks(self, patch_crud_for_testing):
        """Setup test users and tasks in test database"""
        crud = SupabaseCRUD()

        # Clear existing test data
        try:
            crud.delete("users", {"email": "neq.null"})
            crud.delete("tasks", {"title": "neq.null"})
        except Exception:
            pass  # Tables might not exist yet or be empty

        # Create test users
        test_users = [
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "email": "md@test.com",
                "role": "managing_director",
                "departments": ["executive"],
                "teams": ["leadership"],
                "password_hash": "test"
            },
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440001",
                "email": "director@test.com",
                "role": "director",
                "departments": ["engineering"],
                "teams": ["management"],
                "password_hash": "test"
            },
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440002",
                "email": "sales@test.com",
                "role": "manager",
                "departments": ["sales"],
                "teams": ["sales manager"],
                "password_hash": "test"
            },
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440003",
                "email": "staff@test.com",
                "role": "staff",
                "departments": ["engineering"],
                "teams": ["developers"],
                "password_hash": "test"
            },
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440004",
                "email": "eng1@test.com",
                "role": "staff",
                "departments": ["engineering"],
                "teams": ["developers"],
                "password_hash": "test"
            },
            {
                "uuid": "550e8400-e29b-41d4-a716-446655440005",
                "email": "sales2@test.com",
                "role": "staff",
                "departments": ["sales"],
                "teams": ["sales team"],
                "password_hash": "test"
            }
        ]

        for user in test_users:
            try:
                crud.insert("users", user)
            except Exception as e:
                if "duplicate key" in str(e):
                    # User already exists, skip
                    pass
                else:
                    raise

        # Create test tasks
        tomorrow = date.today() + timedelta(days=1)
        test_tasks = [
            {
                "id": "650e8400-e29b-41d4-a716-446655440000",
                "title": "Engineering Task",
                "description": "Task owned by engineering user",
                "due_date": tomorrow.isoformat(),
                "status": "TO_DO",
                "priority": "HIGH",
                "owner_user_id": "550e8400-e29b-41d4-a716-446655440004",
                "assignee_ids": ["550e8400-e29b-41d4-a716-446655440004", "550e8400-e29b-41d4-a716-446655440003"],
                "parent_id": None,
                "comments": [],
                "attachments": [],
                "is_archived": False
            },
            {
                "id": "650e8400-e29b-41d4-a716-446655440001",
                "title": "Sales Task",
                "description": "Task owned by sales user",
                "due_date": tomorrow.isoformat(),
                "status": "IN_PROGRESS",
                "priority": "MEDIUM",
                "owner_user_id": "550e8400-e29b-41d4-a716-446655440005",
                "assignee_ids": ["550e8400-e29b-41d4-a716-446655440005"],
                "parent_id": None,
                "comments": [],
                "attachments": [],
                "is_archived": False
            },
            {
                "id": "650e8400-e29b-41d4-a716-446655440002",
                "title": "Executive Task",
                "description": "Task owned by managing director",
                "due_date": tomorrow.isoformat(),
                "status": "COMPLETED",
                "priority": "LOW",
                "owner_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "assignee_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "parent_id": None,
                "comments": [],
                "attachments": [],
                "is_archived": False
            }
        ]

        for task in test_tasks:
            try:
                crud.insert("tasks", task)
            except Exception as e:
                if "duplicate key" in str(e):
                    # Task already exists, skip
                    pass
                else:
                    raise

        yield

        # Cleanup after tests
        try:
            crud.delete("tasks", {"title": "neq.null"})
            crud.delete("users", {"email": "neq.null"})
        except Exception:
            pass

    @pytest.fixture
    def sample_tasks(self):
        """Sample task data"""
        return [
            {
                "id": "650e8400-e29b-41d4-a716-446655440000",
                "title": "Engineering Task",
                "owner_user_id": "550e8400-e29b-41d4-a716-446655440004",
                "assignee_ids": ["550e8400-e29b-41d4-a716-446655440004", "550e8400-e29b-41d4-a716-446655440003"],
                "parent_id": None,
                "status": "TO_DO",
                "priority": "HIGH"
            },
            {
                "id": "650e8400-e29b-41d4-a716-446655440001",
                "title": "Sales Task",
                "owner_user_id": "550e8400-e29b-41d4-a716-446655440005",
                "assignee_ids": ["550e8400-e29b-41d4-a716-446655440005"],
                "parent_id": None,
                "status": "IN_PROGRESS",
                "priority": "MEDIUM"
            },
            {
                "id": "650e8400-e29b-41d4-a716-446655440002",
                "title": "Executive Task",
                "owner_user_id": "550e8400-e29b-41d4-a716-446655440006",
                "assignee_ids": ["550e8400-e29b-41d4-a716-446655440006"],
                "parent_id": None,
                "status": "COMPLETED",
                "priority": "LOW"
            }
        ]

    @pytest.fixture
    def sample_users(self):
        """Sample user data for different departments/teams"""
        return {
            "engineering_dept": [
                {"id": "550e8400-e29b-41d4-a716-446655440004", "email": "eng1@test.com"},
                {"id": "550e8400-e29b-41d4-a716-446655440003", "email": "staff@test.com"}
            ],
            "sales_dept": [
                {"id": "550e8400-e29b-41d4-a716-446655440005", "email": "sales2@test.com"}
            ],
            "developers_team": [
                {"id": "550e8400-e29b-41d4-a716-446655440003", "email": "staff@test.com"},
                {"id": "550e8400-e29b-41d4-a716-446655440007", "email": "dev2@test.com"}
            ]
        }

    def test_managing_director_can_read_all_tasks(self, managing_director_token, setup_test_users_and_tasks):
        """Test that managing directors can read all tasks"""
        # Arrange
        headers = {"Authorization": f"Bearer {managing_director_token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) >= 3  # Should see at least our 3 test tasks

        # Verify our test task types are returned (may have more from other tests)
        task_ids = {task["id"] for task in data["tasks"]}
        expected_task_ids = {"650e8400-e29b-41d4-a716-446655440000", "650e8400-e29b-41d4-a716-446655440001", "650e8400-e29b-41d4-a716-446655440002"}
        assert expected_task_ids.issubset(task_ids)  # Our test tasks should be present

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_director_can_read_department_tasks(self, mock_get_tasks, director_token, sample_tasks):
        """Test that directors can read tasks from their department"""
        # Arrange
        dept_tasks = [task for task in sample_tasks if task["id"] in ["650e8400-e29b-41d4-a716-446655440000"]]  # Engineering tasks
        mock_get_tasks.return_value = dept_tasks
        headers = {"Authorization": f"Bearer {director_token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "650e8400-e29b-41d4-a716-446655440000"

        mock_get_tasks.assert_called_once_with(
            user_id="550e8400-e29b-41d4-a716-446655440001",
            user_role="director",
            user_teams=["management"],
            user_departments=["engineering"]
        )

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_privileged_team_can_read_department_tasks(self, mock_get_tasks, privileged_team_token, sample_tasks):
        """Test that privileged teams can read tasks from their department"""
        # Arrange
        sales_tasks = [task for task in sample_tasks if task["id"] in ["650e8400-e29b-41d4-a716-446655440001"]]  # Sales tasks
        mock_get_tasks.return_value = sales_tasks
        headers = {"Authorization": f"Bearer {privileged_team_token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "650e8400-e29b-41d4-a716-446655440001"

        mock_get_tasks.assert_called_once_with(
            user_id="550e8400-e29b-41d4-a716-446655440002",
            user_role="manager",
            user_teams=["sales manager"],
            user_departments=["sales"]
        )

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_regular_staff_can_read_team_and_assigned_tasks(self, mock_get_tasks, regular_staff_token, sample_tasks):
        """Test that regular staff can read team tasks and assigned tasks"""
        # Arrange
        accessible_tasks = [task for task in sample_tasks if task["id"] in ["650e8400-e29b-41d4-a716-446655440000"]]  # Staff is assigned to task-1
        mock_get_tasks.return_value = accessible_tasks
        headers = {"Authorization": f"Bearer {regular_staff_token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "650e8400-e29b-41d4-a716-446655440000"

        mock_get_tasks.assert_called_once_with(
            user_id="550e8400-e29b-41d4-a716-446655440003",
            user_role="staff",
            user_teams=["developers"],
            user_departments=["engineering"]
        )

    def test_read_tasks_without_authentication_fails(self):
        """Test that reading tasks without authentication fails"""
        # Act
        response = client.get("/api/tasks/readTasks")

        # Assert
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]

    def test_read_tasks_with_invalid_token_fails(self):
        """Test that reading tasks with invalid token fails"""
        # Arrange
        headers = {"Authorization": "Bearer invalid-token"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 401

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_read_tasks_returns_empty_when_no_access(self, mock_get_tasks, regular_staff_token):
        """Test that endpoint returns empty list when user has no access to tasks"""
        # Arrange
        mock_get_tasks.return_value = []  # No accessible tasks
        headers = {"Authorization": f"Bearer {regular_staff_token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_read_tasks_handles_task_reader_exception(self, mock_get_tasks, regular_staff_token):
        """Test that endpoint handles TaskReader exceptions gracefully"""
        # Arrange
        mock_get_tasks.side_effect = Exception("Database connection error")
        headers = {"Authorization": f"Bearer {regular_staff_token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_read_tasks_validates_jwt_token_structure(self, mock_get_tasks, sample_tasks):
        """Test that endpoint handles JWT token with minimal required fields"""
        # Arrange
        minimal_token_data = {
            "sub": "user-id",
            "role": "staff",  # Include required role
            # Missing teams, departments - should default to empty lists
        }
        minimal_token = create_access_token(minimal_token_data)
        mock_get_tasks.return_value = sample_tasks
        headers = {"Authorization": f"Bearer {minimal_token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200  # Should work with defaults
        data = response.json()
        assert "tasks" in data

        # Verify default values are used for missing fields
        mock_get_tasks.assert_called_once_with(
            user_id="user-id",
            user_role="staff",
            user_teams=[],   # Default empty list
            user_departments=[]  # Default empty list
        )

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_read_tasks_with_multiple_teams_and_departments(self, mock_get_tasks, sample_tasks):
        """Test reading tasks with user having multiple teams and departments"""
        # Arrange
        multi_team_token_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440008",
            "role": "manager",
            "teams": ["team1", "team2", "sales manager"],
            "departments": ["dept1", "dept2"]
        }
        token = create_access_token(multi_team_token_data)
        mock_get_tasks.return_value = sample_tasks
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200
        mock_get_tasks.assert_called_once_with(
            user_id="550e8400-e29b-41d4-a716-446655440008",
            user_role="manager",
            user_teams=["team1", "team2", "sales manager"],
            user_departments=["dept1", "dept2"]
        )

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_read_tasks_response_format(self, mock_get_tasks, managing_director_token, sample_tasks):
        """Test that the response format is correct"""
        # Arrange
        mock_get_tasks.return_value = sample_tasks
        headers = {"Authorization": f"Bearer {managing_director_token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data, dict)
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

        # Verify task structure
        if data["tasks"]:
            task = data["tasks"][0]
            required_fields = ["id", "title", "owner_user_id", "assignee_ids", "status", "priority"]
            for field in required_fields:
                assert field in task

    @patch('backend.utils.task_crud.read.TaskReader.get_tasks_for_user')
    def test_finance_manager_privileged_team_access(self, mock_get_tasks, sample_tasks):
        """Test that finance managers team has privileged access"""
        # Arrange
        finance_token_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440009",
            "role": "manager",
            "teams": ["finance managers"],
            "departments": ["finance"]
        }
        token = create_access_token(finance_token_data)
        mock_get_tasks.return_value = sample_tasks
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = client.get("/api/tasks/readTasks", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 3  # Should get all tasks due to privileged access

        mock_get_tasks.assert_called_once_with(
            user_id="550e8400-e29b-41d4-a716-446655440009",
            user_role="manager",
            user_teams=["finance managers"],
            user_departments=["finance"]
        )
