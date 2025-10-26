from datetime import date, timedelta
from io import BytesIO
from backend.utils.report_util.task_completion_util import TaskCompletionReportGenerator
from backend.schemas.report_schemas import TaskCompletionResponse, TaskCompletionItem


class TestTaskCompletionReportGenerator:
    """Unit tests for TaskCompletionReportGenerator class"""

    def test_generate_report_by_project(self, mock_crud, sample_project, sample_tasks, date_range):
        """Test generating task completion report for a project"""
        # Arrange
        mock_crud.select.side_effect = [
            [sample_project],  # For _get_scope_name
            [sample_tasks[0], sample_tasks[1], sample_tasks[3]]  # Tasks for project
        ]

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_report(
            scope_type="project",
            scope_id="proj-123",
            start_date=date_range["start_date"],
            end_date=date_range["end_date"]
        )

        # Assert
        assert isinstance(result, TaskCompletionResponse)
        assert result.scope_type == "project"
        assert result.scope_id == "proj-123"
        assert result.scope_name == "Test Project"
        assert result.total_tasks == 3
        assert len(result.tasks) == 3

    def test_generate_report_by_staff(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test generating task completion report for a staff member"""
        # Arrange
        mock_crud.select.side_effect = [
            [sample_users[0]],  # For _get_scope_name
            sample_tasks  # All tasks
        ]

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_report(
            scope_type="staff",
            scope_id="user-1",
            start_date=date_range["start_date"],
            end_date=date_range["end_date"]
        )

        # Assert
        assert isinstance(result, TaskCompletionResponse)
        assert result.scope_type == "staff"
        assert result.scope_id == "user-1"
        assert result.scope_name == "user1@test.com"
        # Should include tasks where user-1 is in assignee_ids or is owner
        assert result.total_tasks == 2  # task-1, task-3

    def test_get_scope_name_for_project(self, mock_crud, sample_project):
        """Test getting scope name for a project"""
        # Arrange
        mock_crud.select.return_value = [sample_project]

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_scope_name("project", "proj-123")

        # Assert
        assert result == "Test Project"
        mock_crud.select.assert_called_once_with("projects", filters={"id": "proj-123"})

    def test_get_scope_name_for_project_not_found(self, mock_crud):
        """Test getting scope name for non-existent project"""
        # Arrange
        mock_crud.select.return_value = []

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_scope_name("project", "proj-999")

        # Assert
        assert result == "Unknown Project"

    def test_get_scope_name_for_staff(self, mock_crud, sample_users):
        """Test getting scope name for a staff member"""
        # Arrange
        mock_crud.select.return_value = [sample_users[0]]

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_scope_name("staff", "user-1")

        # Assert
        assert result == "user1@test.com"
        mock_crud.select.assert_called_once_with("users", filters={"uuid": "user-1"})

    def test_get_scope_name_for_staff_not_found(self, mock_crud):
        """Test getting scope name for non-existent staff"""
        # Arrange
        mock_crud.select.return_value = []

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_scope_name("staff", "user-999")

        # Assert
        assert result == "Unknown User"

    def test_get_tasks_by_project(self, mock_crud, sample_tasks, date_range):
        """Test getting tasks filtered by project"""
        # Arrange
        project_tasks = [sample_tasks[0], sample_tasks[1], sample_tasks[3]]
        mock_crud.select.return_value = project_tasks

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_tasks_by_project(
            "proj-123",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        mock_crud.select.assert_called_once_with("tasks", filters={"project_id": "proj-123"})
        assert len(result) == 3

    def test_get_tasks_by_staff_as_assignee(self, mock_crud, sample_tasks, date_range):
        """Test getting tasks where staff is in assignee_ids"""
        # Arrange
        mock_crud.select.return_value = sample_tasks

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_tasks_by_staff(
            "user-2",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        # Should return task-1 (assignee) and task-2 (assignee and owner)
        assert len(result) == 2
        task_ids = [task["id"] for task in result]
        assert "task-1" in task_ids
        assert "task-2" in task_ids

    def test_get_tasks_by_staff_as_owner(self, mock_crud, sample_tasks, date_range):
        """Test getting tasks where staff is the owner"""
        # Arrange
        mock_crud.select.return_value = sample_tasks

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_tasks_by_staff(
            "user-3",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        # Should return task-4 (owner and assignee)
        assert len(result) == 1
        assert result[0]["id"] == "task-4"

    def test_filter_by_date_range(self, mock_crud, sample_tasks):
        """Test filtering tasks by date range"""
        # Arrange
        today = date.today()
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act - narrow date range
        result = generator._filter_by_date_range(
            sample_tasks,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=5)
        )

        # Assert - should only include task-2 and task-4
        assert len(result) == 2
        task_ids = [task["id"] for task in result]
        assert "task-2" in task_ids
        assert "task-4" in task_ids

    def test_filter_by_date_range_excludes_past_tasks(self, mock_crud, sample_tasks):
        """Test that date filtering excludes past tasks correctly"""
        # Arrange
        today = date.today()
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act - only future dates
        result = generator._filter_by_date_range(
            sample_tasks,
            start_date=today,
            end_date=today + timedelta(days=10)
        )

        # Assert - should not include completed or overdue tasks
        task_ids = [task["id"] for task in result]
        assert "task-1" not in task_ids  # Past due date
        assert "task-3" not in task_ids  # Past due date

    def test_filter_by_date_range_handles_missing_due_date(self, mock_crud):
        """Test that tasks without due_date are excluded"""
        # Arrange
        tasks = [
            {
                "id": "task-no-date",
                "title": "Task without due date",
                "due_date": None
            }
        ]
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._filter_by_date_range(
            tasks,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )

        # Assert
        assert len(result) == 0

    def test_filter_by_date_range_handles_invalid_date(self, mock_crud):
        """Test that tasks with invalid due_date are excluded"""
        # Arrange
        tasks = [
            {
                "id": "task-bad-date",
                "title": "Task with invalid date",
                "due_date": "not-a-date"
            }
        ]
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._filter_by_date_range(
            tasks,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )

        # Assert
        assert len(result) == 0

    def test_convert_to_task_item(self, mock_crud):
        """Test converting task data to TaskCompletionItem"""
        # Arrange
        today = date.today()
        task = {
            "title": "Test Task",
            "priority": 5,
            "status": "IN_PROGRESS",
            "due_date": (today + timedelta(days=3)).isoformat()
        }
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._convert_to_task_item(task)

        # Assert
        assert isinstance(result, TaskCompletionItem)
        assert result.task_title == "Test Task"
        assert result.priority == 5
        assert result.status == "IN_PROGRESS"
        assert result.overdue is False

    def test_convert_to_task_item_overdue_calculation(self, mock_crud):
        """Test that overdue is correctly calculated"""
        # Arrange
        today = date.today()
        overdue_task = {
            "title": "Overdue Task",
            "priority": 3,
            "status": "TO_DO",
            "due_date": (today - timedelta(days=5)).isoformat()
        }
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._convert_to_task_item(overdue_task)

        # Assert
        assert result.overdue is True

    def test_convert_to_task_item_completed_not_overdue(self, mock_crud):
        """Test that completed tasks are not marked as overdue"""
        # Arrange
        today = date.today()
        completed_task = {
            "title": "Completed Task",
            "priority": 5,
            "status": "COMPLETED",
            "due_date": (today - timedelta(days=5)).isoformat()
        }
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._convert_to_task_item(completed_task)

        # Assert
        assert result.overdue is False

    def test_convert_to_task_item_handles_missing_fields(self, mock_crud):
        """Test that missing fields are handled with defaults"""
        # Arrange
        task = {}
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._convert_to_task_item(task)

        # Assert
        assert result.task_title == "Untitled"
        assert result.priority == 5
        assert result.status == "TO_DO"
        assert result.due_date == ""
        assert result.overdue is False

    def test_convert_to_task_item_handles_invalid_due_date_format(self, mock_crud):
        """Test that invalid due_date format doesn't crash conversion"""
        task = {
            "title": "Test Task",
            "priority": 5,
            "status": "TO_DO",
            "due_date": "invalid-date-format"
        }
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        result = generator._convert_to_task_item(task)

        assert result.task_title == "Test Task"
        assert result.overdue is False

    def test_generate_excel_bytes(self, mock_crud):
        """Test generating Excel file returns BytesIO"""
        # Arrange
        today = date.today()
        tasks = [
            TaskCompletionItem(
                task_title="Task 1",
                priority=5,
                status="COMPLETED",
                due_date=today.isoformat(),
                overdue=False
            )
        ]
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_excel_bytes(
            scope_type="project",
            scope_id="proj-123",
            scope_name="Test Project",
            start_date=today,
            end_date=today + timedelta(days=7),
            tasks=tasks
        )

        # Assert
        assert isinstance(result, BytesIO)
        assert result.tell() == 0  # Check it's seeked to start
        content = result.read()
        assert len(content) > 0  # Check it has content

    def test_generate_pdf_bytes(self, mock_crud):
        """Test generating PDF file returns BytesIO"""
        # Arrange
        today = date.today()
        tasks = [
            TaskCompletionItem(
                task_title="Task 1",
                priority=5,
                status="COMPLETED",
                due_date=today.isoformat(),
                overdue=False
            )
        ]
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_pdf_bytes(
            scope_type="project",
            scope_id="proj-123",
            scope_name="Test Project",
            start_date=today,
            end_date=today + timedelta(days=7),
            tasks=tasks
        )

        # Assert
        assert isinstance(result, BytesIO)
        assert result.tell() == 0  # Check it's seeked to start
        content = result.read()
        assert len(content) > 0  # Check it has content
        assert content[:4] == b'%PDF'  # Check it's a PDF

    def test_generate_excel_bytes_with_empty_tasks(self, mock_crud):
        """Test generating Excel with no tasks"""
        # Arrange
        today = date.today()
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_excel_bytes(
            scope_type="project",
            scope_id="proj-123",
            scope_name="Test Project",
            start_date=today,
            end_date=today + timedelta(days=7),
            tasks=[]
        )

        # Assert
        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0  # Still produces a valid file

    def test_generate_pdf_bytes_with_empty_tasks(self, mock_crud):
        """Test generating PDF with no tasks"""
        # Arrange
        today = date.today()
        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_pdf_bytes(
            scope_type="project",
            scope_id="proj-123",
            scope_name="Test Project",
            start_date=today,
            end_date=today + timedelta(days=7),
            tasks=[]
        )

        # Assert
        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0  # Still produces a valid file
        assert content[:4] == b'%PDF'

    def test_get_tasks_by_staff_handles_string_assignee_ids(self, mock_crud, date_range):
        """Test handling of assignee_ids as PostgreSQL array string"""
        # Arrange
        tasks = [
            {
                "id": "task-1",
                "title": "Task 1",
                "due_date": date.today().isoformat(),
                "assignee_ids": "{user-1,user-2}",  # PostgreSQL array format
                "owner_user_id": "user-3"
            }
        ]
        mock_crud.select.return_value = tasks

        generator = TaskCompletionReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_tasks_by_staff(
            "user-1",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "task-1"
