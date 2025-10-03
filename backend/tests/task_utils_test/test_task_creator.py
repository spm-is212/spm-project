from backend.utils.task_crud.create import TaskCreator
from backend.schemas.task import TaskCreate, SubtaskCreate


class TestTaskCreator:
    """Unit tests for TaskCreator class"""

    def test_create_main_task_only(self, mock_crud, sample_task_data):
        """Test creating only a main task without subtasks"""
        # Arrange
        sample_task_data["project_id"] = "proj-123"
        mock_crud.insert.return_value = {**sample_task_data, "id": "generated-id-123"}

        creator = TaskCreator()
        creator.crud = mock_crud

        main_task = TaskCreate(**sample_task_data)

        # Act
        result = creator.create_task_with_subtasks("test-user-id", main_task, None)

        # Assert
        assert result["main_task"]["id"] == "generated-id-123"
        assert result["main_task"]["title"] == "Test Task"
        assert result["subtasks"] == []

        # Verify CRUD was called correctly
        mock_crud.insert.assert_called_once()
        call_args = mock_crud.insert.call_args
        assert call_args[0][0] == "tasks"  # table name
        assert call_args[0][1]["parent_id"] is None  # main task has no parent
        assert call_args[0][1]["owner_user_id"] == "test-user-id"

    def test_create_main_task_with_subtasks(self, mock_crud, sample_task_data, sample_subtask_data):
        """Test creating main task with subtasks"""
        # Arrange
        sample_task_data["project_id"] = "proj-123"
        sample_subtask_data["project_id"] = "proj-123"
        main_task_result = {**sample_task_data, "id": "main-task-id"}
        subtask_result = {**sample_subtask_data, "id": "subtask-id", "parent_id": "main-task-id"}

        mock_crud.insert.side_effect = [main_task_result, subtask_result]

        creator = TaskCreator()
        creator.crud = mock_crud

        main_task = TaskCreate(**sample_task_data)
        subtasks = [SubtaskCreate(**sample_subtask_data)]

        # Act
        result = creator.create_task_with_subtasks("test-user-id", main_task, subtasks)

        # Assert
        assert result["main_task"]["id"] == "main-task-id"
        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0]["id"] == "subtask-id"
        assert result["subtasks"][0]["parent_id"] == "main-task-id"

        # Verify CRUD was called twice
        assert mock_crud.insert.call_count == 2

        # Check main task call
        main_call = mock_crud.insert.call_args_list[0]
        assert main_call[0][1]["parent_id"] is None

        # Check subtask call
        subtask_call = mock_crud.insert.call_args_list[1]
        assert subtask_call[0][1]["parent_id"] == "main-task-id"

    def test_subtask_inherits_main_task_id(self, mock_crud, sample_task_data, sample_subtask_data):
        """Test that subtasks get the main task's ID as parent_id"""
        # Arrange
        sample_task_data["project_id"] = "proj-123"
        sample_subtask_data["project_id"] = "proj-123"
        main_task_result = {**sample_task_data, "id": "main-123"}
        subtask_result = {**sample_subtask_data, "id": "sub-123", "parent_id": "main-123"}

        mock_crud.insert.side_effect = [main_task_result, subtask_result]

        creator = TaskCreator()
        creator.crud = mock_crud

        main_task = TaskCreate(**sample_task_data)
        subtasks = [SubtaskCreate(**sample_subtask_data)]

        # Act
        result = creator.create_task_with_subtasks("test-user-id", main_task, subtasks)

        # Assert
        subtask_call = mock_crud.insert.call_args_list[1]
        assert subtask_call[0][1]["parent_id"] == "main-123"
        assert result["subtasks"][0]["parent_id"] == "main-123"

    def test_main_task_parent_id_always_none(self, mock_crud, sample_task_data):
        """Test that main task parent_id is always set to None regardless of input"""
        # Arrange
        sample_task_data["project_id"] = "proj-123" 
        task_data_with_parent = {**sample_task_data, "parent_id": "some-invalid-parent"}
        mock_crud.insert.return_value = {**task_data_with_parent, "id": "test-id", "parent_id": None}

        creator = TaskCreator()
        creator.crud = mock_crud

        main_task = TaskCreate(**task_data_with_parent)

        # Act
        result = creator.create_task_with_subtasks("test-user-id", main_task, None)

        # Assert
        call_args = mock_crud.insert.call_args[0][1]
        assert call_args["parent_id"] is None
        assert result["main_task"]["parent_id"] is None

    def test_subtask_without_assignees_defaults_to_empty_list(self, mock_crud, sample_task_data):
        """Test that subtasks without assignee_ids get empty list"""
        # Arrange
        sample_task_data["project_id"] = "proj-123" 
        subtask_data = {
            "title": "Unassigned Subtask",
            "description": "No assignees",
            "due_date": "2025-10-01",
            "status": "TO_DO",
            "priority": "LOW",
            "project_id": "proj-123"
        }

        main_task_result = {**sample_task_data, "id": "main-id"}
        subtask_result = {**subtask_data, "id": "sub-id", "parent_id": "main-id", "assignee_ids": []}

        mock_crud.insert.side_effect = [main_task_result, subtask_result]

        creator = TaskCreator()
        creator.crud = mock_crud

        main_task = TaskCreate(**sample_task_data)
        subtasks = [SubtaskCreate(**subtask_data)]

        # Act
        creator.create_task_with_subtasks("test-user-id", main_task, subtasks)

        # Assert - creator should be auto-assigned
        subtask_call = mock_crud.insert.call_args_list[1]
        assert subtask_call[0][1]["assignee_ids"] == ["test-user-id"]

    def test_owner_user_id_set_for_all_tasks(self, mock_crud, sample_task_data, sample_subtask_data):
        """Test that owner_user_id is set correctly for main task and subtasks"""
        # Arrange
        sample_task_data["project_id"] = "proj-123"
        sample_subtask_data["project_id"] = "proj-123"
        main_task_result = {**sample_task_data, "id": "main-id"}
        subtask_result = {**sample_subtask_data, "id": "sub-id", "parent_id": "main-id"}

        mock_crud.insert.side_effect = [main_task_result, subtask_result]

        creator = TaskCreator()
        creator.crud = mock_crud

        main_task = TaskCreate(**sample_task_data)
        subtasks = [SubtaskCreate(**sample_subtask_data)]

        # Act
        creator.create_task_with_subtasks("owner-123", main_task, subtasks)

        # Assert
        main_call = mock_crud.insert.call_args_list[0]
        subtask_call = mock_crud.insert.call_args_list[1]

        assert main_call[0][1]["owner_user_id"] == "owner-123"
        assert subtask_call[0][1]["owner_user_id"] == "owner-123"
