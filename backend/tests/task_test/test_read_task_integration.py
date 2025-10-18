import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.security import create_access_token
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from datetime import date, timedelta

client = TestClient(app)


class TestReadTaskIntegration:
    """Integration tests for the read tasks endpoint using real test database"""

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
    def setup_test_data(self, patch_crud_for_testing):
        """Setup test users and tasks in test database"""
        crud = SupabaseCRUD()

        # Clear all test data to ensure clean state
        # Note: patch_crud_for_testing redirects all operations to _test tables
        try:
            # Delete all tasks first (to avoid foreign key constraints)
            crud.delete("tasks", {"title": "neq.null"})
            # Delete all users
            crud.delete("users", {"email": "neq.null"})
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
                "priority": 9,
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
                "priority": 8,
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
                "priority": 1,
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

    def test_managing_director_can_read_all_tasks(self, managing_director_token, setup_test_data):
        """Test that managing directors can read all tasks"""
        headers = {"Authorization": f"Bearer {managing_director_token}"}

        response = client.get("/api/tasks/readTasks", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) >= 3  # Should see at least our 3 test tasks

        # Verify our test task types are returned (may have more from other tests)
        task_ids = {task["id"] for task in data["tasks"]}
        expected_task_ids = {"650e8400-e29b-41d4-a716-446655440000", "650e8400-e29b-41d4-a716-446655440001", "650e8400-e29b-41d4-a716-446655440002"}
        assert expected_task_ids.issubset(task_ids)  # Our test tasks should be present

    def test_director_can_read_department_tasks(self, director_token, setup_test_data):
        """Test that directors can read tasks from their department"""
        headers = {"Authorization": f"Bearer {director_token}"}

        response = client.get("/api/tasks/readTasks", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Director in engineering dept should see task-1 (owned by eng-user-1)
        task_ids = {task["id"] for task in data["tasks"]}
        # Debug: Print actual task IDs to understand what's being returned
        print(f"DEBUG: Director got {len(data['tasks'])} tasks with IDs: {task_ids}")
        # Look for engineering task (should be accessible by engineering director)
        engineering_tasks = [task for task in data["tasks"] if task.get("owner_user_id") == "550e8400-e29b-41d4-a716-446655440004"]
        print(f"DEBUG: Engineering tasks found: {len(engineering_tasks)}")
        assert len(engineering_tasks) >= 1  # Should see at least one engineering task
        # Should not see sales task
        assert "650e8400-e29b-41d4-a716-446655440001" not in task_ids

    @pytest.mark.skip(reason="Teams feature removed")
    def test_privileged_team_can_read_department_tasks(self, privileged_team_token, setup_test_data):
        """Test that privileged teams (sales manager) can read tasks from their department"""
        headers = {"Authorization": f"Bearer {privileged_team_token}"}

        response = client.get("/api/tasks/readTasks", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Sales manager should see sales department tasks
        task_ids = {task["id"] for task in data["tasks"]}
        print(f"DEBUG: Sales manager got {len(data['tasks'])} tasks with IDs: {task_ids}")
        # Look for sales task (should be accessible by sales manager)
        sales_tasks = [task for task in data["tasks"] if task.get("owner_user_id") == "550e8400-e29b-41d4-a716-446655440005"]
        print(f"DEBUG: Sales tasks found: {len(sales_tasks)}")
        assert len(sales_tasks) >= 1  # Should see at least one sales task

    def test_regular_staff_can_read_team_and_assigned_tasks(self, regular_staff_token, setup_test_data):
        """Test that regular staff can read team tasks and assigned tasks"""
        headers = {"Authorization": f"Bearer {regular_staff_token}"}

        response = client.get("/api/tasks/readTasks", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Staff should see:
        # - task-1: owned by eng-user-1 (same team: developers) AND assigned to staff-user-id
        task_ids = {task["id"] for task in data["tasks"]}
        assert "650e8400-e29b-41d4-a716-446655440000" in task_ids

    def test_read_tasks_without_authentication_fails(self):
        """Test that reading tasks without authentication fails"""
        response = client.get("/api/tasks/readTasks")
        assert response.status_code == 403

    def test_read_tasks_with_invalid_token_fails(self):
        """Test that reading tasks with invalid token fails"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/tasks/readTasks", headers=headers)
        assert response.status_code == 401

    def test_read_tasks_returns_empty_when_no_access(self, setup_test_data):
        """Test that endpoint returns empty list when user has no access to tasks"""
        # Create token for user not in any team/department
        token_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440010",
            "role": "staff",
            "teams": [],
            "departments": []
        }
        token = create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/tasks/readTasks", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []  # Should have no access to any tasks

    def test_response_format_is_correct(self, managing_director_token, setup_test_data):
        """Test that the response format is correct"""
        headers = {"Authorization": f"Bearer {managing_director_token}"}

        response = client.get("/api/tasks/readTasks", headers=headers)

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

    def test_finance_manager_privileged_team_access(self, setup_test_data):
        """Test that finance managers team has privileged access"""
        # Create finance manager token
        token_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440009",
            "role": "manager",
            "teams": ["finance managers"],
            "departments": ["finance"]
        }
        token = create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/tasks/readTasks", headers=headers)

        assert response.status_code == 200
        data = response.json()
        # Finance manager should have privileged access but no tasks in finance dept in our test data
        assert "tasks" in data

    def test_jwt_token_with_minimal_fields(self, setup_test_data):
        """Test that endpoint handles JWT token with minimal required fields"""
        minimal_token_data = {
            "sub": "user-id",
            "role": "staff",
            # Missing teams, departments - should default to empty lists
        }
        minimal_token = create_access_token(minimal_token_data)
        headers = {"Authorization": f"Bearer {minimal_token}"}

        response = client.get("/api/tasks/readTasks", headers=headers)

        assert response.status_code == 200  # Should work with defaults
        data = response.json()
        assert "tasks" in data
