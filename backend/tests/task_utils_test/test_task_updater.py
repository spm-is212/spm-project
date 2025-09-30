from datetime import date
from backend.utils.task_crud.update import TaskUpdater
from backend.schemas.task import TaskUpdate


class TestTaskUpdater:
    """Unit tests for TaskUpdater class"""

    def test_update_main_task_basic_fields(self, mock_crud, mock_task_in_db):
        """Test updating basic fields of a main task"""
        # Arrange
        updated_task = {**mock_task_in_db, "title": "Updated Title", "description": "Updated description"}
        mock_crud.update.return_value = [updated_task]

        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate(
            title="Updated Title",
            description="Updated description"
        )

        # Act
        result = updater.update_tasks("test-task-id", "user-1", "manager", ["team1"], main_task=update_data)

        # Assert
        assert result["main_task"]["title"] == "Updated Title"
        assert result["main_task"]["description"] == "Updated description"

        # Verify CRUD call
        mock_crud.update.assert_called_once()
        call_args = mock_crud.update.call_args
        assert call_args[0][0] == "tasks"  # table name
        assert call_args[0][1]["title"] == "Updated Title"
        assert call_args[0][1]["parent_id"] is None  # Always None for main tasks
        assert call_args[0][2] == {"id": "test-task-id"}  # filter

    def test_update_main_task_status_and_priority(self, mock_crud, mock_task_in_db):
        """Test updating status and priority fields"""
        # Arrange
        updated_task = {**mock_task_in_db, "status": "IN_PROGRESS", "priority": "MEDIUM"}
        mock_crud.update.return_value = [updated_task]

        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate(
            status="IN_PROGRESS",
            priority="MEDIUM"
        )

        # Act
        updater.update_tasks("test-task-id", "user-1", "staff", ["team1"], main_task=update_data)

        # Assert
        call_args = mock_crud.update.call_args[0][1]
        assert call_args["status"] == "IN_PROGRESS"
        assert call_args["priority"] == "MEDIUM"

    def test_update_main_task_due_date(self, mock_crud, mock_task_in_db):
        """Test updating due date converts to ISO format"""
        # Arrange
        updated_task = {**mock_task_in_db, "due_date": "2025-12-25"}
        mock_crud.update.return_value = [updated_task]

        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate(due_date=date(2025, 12, 25))

        # Act
        updater.update_tasks("test-task-id", "user-1", "manager", ["team1"], main_task=update_data)

        # Assert
        call_args = mock_crud.update.call_args[0][1]
        assert call_args["due_date"] == "2025-12-25"

    def test_manager_can_remove_assignees(self, mock_crud):
        """Test that managers can remove assignees"""
        # Arrange
        current_task = {
            "id": "test-task-id",
            "assignee_ids": ["user-1", "user-2", "user-3"]
        }
        updated_task = {**current_task, "assignee_ids": ["user-1"]}

        mock_crud.select.return_value = [current_task]
        mock_crud.update.return_value = [updated_task]

        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate(assignee_ids=["user-1"])  # Removing user-2 and user-3

        # Act
        result = updater.update_tasks("test-task-id", "user-1", "manager", ["team1"], main_task=update_data)

        # Assert
        call_args = mock_crud.update.call_args[0][1]
        assert call_args["assignee_ids"] == ["user-1"]
        assert result["main_task"]["assignee_ids"] == ["user-1"]

    def test_staff_can_add_assignees(self, mock_crud):
        """Test that staff can add assignees"""
        # Arrange
        current_task = {
            "id": "test-task-id",
            "assignee_ids": ["user-1"]
        }
        updated_task = {**current_task, "assignee_ids": ["user-1", "user-2"]}

        mock_crud.select.return_value = [current_task]
        mock_crud.update.return_value = [updated_task]

        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate(assignee_ids=["user-1", "user-2"])  # Adding user-2

        # Act
        updater.update_tasks("test-task-id", "user-1", "staff", ["team1"], main_task=update_data)

        # Assert
        call_args = mock_crud.update.call_args[0][1]
        assert call_args["assignee_ids"] == ["user-1", "user-2"]

    def test_staff_cannot_remove_assignees(self, mock_crud):
        """Test that staff cannot remove assignees"""
        # Arrange
        current_task = {
            "id": "test-task-id",
            "assignee_ids": ["user-1", "user-2", "user-3"]
        }

        mock_crud.select.return_value = [current_task]
        # Should not call update since removal is not allowed

        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate(assignee_ids=["user-1"])  # Trying to remove user-2 and user-3

        # Act
        result = updater.update_tasks("test-task-id", "user-1", "staff", ["team1"], main_task=update_data)

        # Assert
        # Should not have called update because staff can't remove assignees
        mock_crud.update.assert_not_called()
        assert result["main_task"] is None

    def test_update_subtasks(self, mock_crud):
        """Test updating subtasks"""
        # Arrange
        current_subtask = {
            "id": "subtask-id",
            "parent_id": "main-task-id",
            "title": "Old Title",
            "assignee_ids": ["user-1"]
        }
        updated_subtask = {**current_subtask, "title": "New Title"}

        mock_crud.select.return_value = [current_subtask]
        mock_crud.update.return_value = [updated_subtask]

        updater = TaskUpdater()
        updater.crud = mock_crud

        subtask_updates = {
            "subtask-id": TaskUpdate(title="New Title")
        }

        # Act
        result = updater.update_tasks("main-task-id", "user-1", "manager", ["team1"], subtasks=subtask_updates)

        # Assert
        assert len(result["updated_subtasks"]) == 1
        assert result["updated_subtasks"][0]["title"] == "New Title"

        # Verify CRUD call
        call_args = mock_crud.update.call_args
        assert call_args[0][0] == "tasks"  # table name
        assert call_args[0][1]["title"] == "New Title"
        assert call_args[0][2] == {"id": "subtask-id", "parent_id": "main-task-id"}  # filter

    def test_subtask_assignee_permissions_manager(self, mock_crud):
        """Test that managers can modify subtask assignees"""
        # Arrange
        current_subtask = {
            "id": "subtask-id",
            "assignee_ids": ["user-1", "user-2"]
        }
        updated_subtask = {**current_subtask, "assignee_ids": ["user-1"]}

        mock_crud.select.return_value = [current_subtask]
        mock_crud.update.return_value = [updated_subtask]

        updater = TaskUpdater()
        updater.crud = mock_crud

        subtask_updates = {
            "subtask-id": TaskUpdate(assignee_ids=["user-1"])  # Removing user-2
        }

        # Act
        updater.update_tasks("main-task-id", "user-1", "manager", ["team1"], subtasks=subtask_updates)

        # Assert
        call_args = mock_crud.update.call_args[0][1]
        assert call_args["assignee_ids"] == ["user-1"]

    def test_subtask_assignee_permissions_staff(self, mock_crud):
        """Test that staff can only add subtask assignees, not remove"""
        # Arrange
        current_subtask = {
            "id": "subtask-id",
            "assignee_ids": ["user-1", "user-2"]
        }

        mock_crud.select.return_value = [current_subtask]

        updater = TaskUpdater()
        updater.crud = mock_crud

        subtask_updates = {
            "subtask-id": TaskUpdate(assignee_ids=["user-1"])  # Trying to remove user-2
        }

        # Act
        result = updater.update_tasks("main-task-id", "user-1", "staff", ["team1"], subtasks=subtask_updates)

        # Assert
        # Should not have called update because staff can't remove assignees
        mock_crud.update.assert_not_called()
        assert len(result["updated_subtasks"]) == 0

    def test_partial_update_only_provided_fields(self, mock_crud, mock_task_in_db):
        """Test that only provided fields are updated"""
        # Arrange
        updated_task = {**mock_task_in_db, "title": "Only Title Updated"}
        mock_crud.update.return_value = [updated_task]

        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate(title="Only Title Updated")  # Only title provided

        # Act
        updater.update_tasks("test-task-id", "user-1", "manager", ["team1"], main_task=update_data)

        # Assert
        call_args = mock_crud.update.call_args[0][1]
        # Should only contain title and parent_id (always set for main tasks)
        assert "title" in call_args
        assert "parent_id" in call_args
        assert "description" not in call_args
        assert "status" not in call_args
        assert "priority" not in call_args
        assert "assignee_ids" not in call_args

    def test_no_update_when_no_fields_provided(self, mock_crud):
        """Test that no update occurs when no fields are provided"""
        # Arrange
        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate()  # No fields provided

        # Act
        result = updater.update_tasks("test-task-id", "user-1", "manager", ["team1"], main_task=update_data)

        # Assert
        mock_crud.update.assert_not_called()
        assert result["main_task"] is None

    def test_main_task_parent_id_always_none(self, mock_crud, mock_task_in_db):
        """Test that main task parent_id is always set to None during updates"""
        # Arrange
        updated_task = {**mock_task_in_db, "title": "Updated", "parent_id": None}
        mock_crud.update.return_value = [updated_task]

        updater = TaskUpdater()
        updater.crud = mock_crud

        update_data = TaskUpdate(title="Updated")

        # Act
        updater.update_tasks("test-task-id", "user-1", "manager", ["team1"], main_task=update_data)

        # Assert
        call_args = mock_crud.update.call_args[0][1]
        assert call_args["parent_id"] is None
