from datetime import date, timedelta
from io import BytesIO
from backend.utils.report_util.logged_time_util import LoggedTimeReportGenerator
from backend.schemas.report_schemas import LoggedTimeResponse, LoggedTimeItem


class TestLoggedTimeReportGenerator:
    """Unit tests for LoggedTimeReportGenerator class"""

    def test_generate_report_by_department(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test generating logged time report for a department"""
        # Arrange
        mock_crud.select.side_effect = [
            sample_users,  # For get_users_by_department
            sample_tasks   # For get_all_tasks
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_report(
            scope_type="department",
            scope_id="Engineering",
            start_date=date_range["start_date"],
            end_date=date_range["end_date"]
        )

        # Assert
        assert isinstance(result, LoggedTimeResponse)
        assert result.scope_type == "department"
        assert result.scope_id == "Engineering"
        assert result.scope_name == "Engineering"
        assert result.total_entries > 0
        assert result.total_hours > 0

    def test_generate_report_by_project(self, mock_crud, sample_project, sample_users, sample_tasks, date_range):
        """Test generating logged time report for a project"""
        # Arrange
        project_tasks = [sample_tasks[0], sample_tasks[1], sample_tasks[3]]
        mock_crud.select.side_effect = [
            [sample_project],  # For _get_scope_name
            project_tasks,     # Tasks for project
            sample_users       # For user mapping
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_report(
            scope_type="project",
            scope_id="proj-123",
            start_date=date_range["start_date"],
            end_date=date_range["end_date"]
        )

        # Assert
        assert isinstance(result, LoggedTimeResponse)
        assert result.scope_type == "project"
        assert result.scope_id == "proj-123"
        assert result.scope_name == "Test Project"
        assert result.total_entries >= 0
        assert result.total_hours == 16.5  # task-1: 5.5*2 (2 assignees), task-2: 3.0, task-4: 2.5

    def test_get_scope_name_for_department(self, mock_crud):
        """Test getting scope name for a department"""
        # Arrange
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_scope_name("department", "Engineering")

        # Assert
        assert result == "Engineering"

    def test_get_scope_name_for_project(self, mock_crud, sample_project):
        """Test getting scope name for a project"""
        # Arrange
        mock_crud.select.return_value = [sample_project]

        generator = LoggedTimeReportGenerator()
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

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_scope_name("project", "proj-999")

        # Assert
        assert result == "Unknown Project"

    def test_get_entries_by_department(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test getting time entries for a department"""
        # Arrange
        mock_crud.select.side_effect = [
            sample_users,  # All users
            sample_tasks   # All tasks
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_entries_by_department(
            "Engineering",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) > 0
        assert all(isinstance(entry, LoggedTimeItem) for entry in result)
        # Check that entries are for users in Engineering department
        staff_names = [entry.staff_name for entry in result]
        assert "user1@test.com" in staff_names or "user2@test.com" in staff_names

    def test_get_entries_by_department_case_insensitive(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test that department matching is case insensitive"""
        # Arrange
        mock_crud.select.side_effect = [
            sample_users,  # All users
            sample_tasks   # All tasks
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_entries_by_department(
            "engineering",  # lowercase
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) > 0

    def test_get_entries_by_department_no_users(self, mock_crud, sample_tasks, date_range):
        """Test getting entries for department with no users"""
        # Arrange
        mock_crud.select.side_effect = [
            [],            # No users
            sample_tasks   # All tasks
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_entries_by_department(
            "NonExistent",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) == 0

    def test_get_entries_by_project(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test getting time entries for a project"""
        # Arrange
        project_tasks = [sample_tasks[0], sample_tasks[1], sample_tasks[3]]
        mock_crud.select.side_effect = [
            project_tasks,  # Tasks for project
            sample_users    # All users for mapping
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_entries_by_project(
            "proj-123",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) > 0
        assert all(isinstance(entry, LoggedTimeItem) for entry in result)

    def test_get_entries_by_project_no_tasks(self, mock_crud, sample_users, date_range):
        """Test getting entries for project with no tasks"""
        # Arrange
        mock_crud.select.side_effect = [
            [],           # No tasks
            sample_users  # All users
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_entries_by_project(
            "proj-999",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) == 0

    def test_filter_by_date_range(self, mock_crud, sample_tasks):
        """Test filtering tasks by date range"""
        # Arrange
        today = date.today()
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
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

    def test_filter_by_date_range_excludes_missing_due_date(self, mock_crud):
        """Test that tasks without due_date are excluded"""
        # Arrange
        tasks = [
            {
                "id": "task-no-date",
                "title": "Task without due date",
                "due_date": None
            }
        ]
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._filter_by_date_range(
            tasks,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )

        # Assert
        assert len(result) == 0

    def test_create_time_entry(self, mock_crud):
        """Test creating a LoggedTimeItem from task data"""
        # Arrange
        today = date.today()
        task = {
            "title": "Test Task",
            "status": "IN_PROGRESS",
            "due_date": (today + timedelta(days=3)).isoformat(),
            "time_log": 5.5
        }
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._create_time_entry("user@test.com", task)

        # Assert
        assert isinstance(result, LoggedTimeItem)
        assert result.staff_name == "user@test.com"
        assert result.task_title == "Test Task"
        assert result.time_log == 5.5
        assert result.status == "IN_PROGRESS"
        assert result.overdue is False

    def test_create_time_entry_handles_none_time_log(self, mock_crud):
        """Test that None time_log is converted to 0.0"""
        # Arrange
        today = date.today()
        task = {
            "title": "Test Task",
            "status": "TO_DO",
            "due_date": today.isoformat(),
            "time_log": None
        }
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._create_time_entry("user@test.com", task)

        # Assert
        assert result.time_log == 0.0

    def test_create_time_entry_handles_invalid_time_log(self, mock_crud):
        """Test that invalid time_log is converted to 0.0"""
        # Arrange
        today = date.today()
        task = {
            "title": "Test Task",
            "status": "TO_DO",
            "due_date": today.isoformat(),
            "time_log": "invalid"
        }
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._create_time_entry("user@test.com", task)

        # Assert
        assert result.time_log == 0.0

    def test_create_time_entry_overdue_calculation(self, mock_crud):
        """Test that overdue is correctly calculated"""
        # Arrange
        today = date.today()
        overdue_task = {
            "title": "Overdue Task",
            "status": "TO_DO",
            "due_date": (today - timedelta(days=5)).isoformat(),
            "time_log": 2.0
        }
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._create_time_entry("user@test.com", overdue_task)

        # Assert
        assert result.overdue is True

    def test_create_time_entry_completed_not_overdue(self, mock_crud):
        """Test that completed tasks are not marked as overdue"""
        # Arrange
        today = date.today()
        completed_task = {
            "title": "Completed Task",
            "status": "COMPLETED",
            "due_date": (today - timedelta(days=5)).isoformat(),
            "time_log": 3.0
        }
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._create_time_entry("user@test.com", completed_task)

        # Assert
        assert result.overdue is False

    def test_create_time_entry_handles_missing_fields(self, mock_crud):
        """Test that missing fields are handled with defaults"""
        # Arrange
        task = {}
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._create_time_entry("user@test.com", task)

        # Assert
        assert result.staff_name == "user@test.com"
        assert result.task_title == "Untitled"
        assert result.time_log == 0.0
        assert result.status == "TO_DO"
        assert result.due_date == ""
        assert result.overdue is False

    def test_generate_report_calculates_total_hours_correctly(self, mock_crud, sample_project, sample_users, sample_tasks, date_range):
        """Test that total hours is calculated correctly including None values"""
        # Arrange
        mock_crud.select.side_effect = [
            [sample_project],  # For _get_scope_name
            sample_tasks,      # Tasks for project (includes task-3 with None time_log)
            sample_users       # For user mapping
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_report(
            scope_type="project",
            scope_id="proj-123",
            start_date=date_range["start_date"],
            end_date=date_range["end_date"]
        )

        # Assert
        assert result.total_hours == 16.5  # task-1: 5.5*2 (2 assignees), task-2: 3.0, task-3: 0.0, task-4: 2.5

    def test_generate_excel_bytes(self, mock_crud):
        """Test generating Excel file returns BytesIO"""
        # Arrange
        today = date.today()
        time_entries = [
            LoggedTimeItem(
                staff_name="user@test.com",
                task_title="Task 1",
                time_log=5.5,
                status="COMPLETED",
                due_date=today.isoformat(),
                overdue=False
            )
        ]
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_excel_bytes(
            scope_type="project",
            scope_name="Test Project",
            start_date=today,
            end_date=today + timedelta(days=7),
            time_entries=time_entries,
            total_hours=5.5
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
        time_entries = [
            LoggedTimeItem(
                staff_name="user@test.com",
                task_title="Task 1",
                time_log=5.5,
                status="COMPLETED",
                due_date=today.isoformat(),
                overdue=False
            )
        ]
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_pdf_bytes(
            scope_type="project",
            scope_name="Test Project",
            start_date=today,
            end_date=today + timedelta(days=7),
            time_entries=time_entries,
            total_hours=5.5
        )

        # Assert
        assert isinstance(result, BytesIO)
        assert result.tell() == 0  # Check it's seeked to start
        content = result.read()
        assert len(content) > 0  # Check it has content
        assert content[:4] == b'%PDF'  # Check it's a PDF

    def test_generate_excel_bytes_with_empty_entries(self, mock_crud):
        """Test generating Excel with no time entries"""
        # Arrange
        today = date.today()
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_excel_bytes(
            scope_type="project",
            scope_name="Test Project",
            start_date=today,
            end_date=today + timedelta(days=7),
            time_entries=[],
            total_hours=0.0
        )

        # Assert
        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0  # Still produces a valid file

    def test_generate_pdf_bytes_with_empty_entries(self, mock_crud):
        """Test generating PDF with no time entries"""
        # Arrange
        today = date.today()
        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_pdf_bytes(
            scope_type="project",
            scope_name="Test Project",
            start_date=today,
            end_date=today + timedelta(days=7),
            time_entries=[],
            total_hours=0.0
        )

        # Assert
        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0  # Still produces a valid file
        assert content[:4] == b'%PDF'

    def test_get_entries_by_project_handles_unknown_user(self, mock_crud, sample_tasks, date_range):
        """Test handling of tasks with unknown user IDs"""
        # Arrange
        project_tasks = [sample_tasks[0]]
        mock_crud.select.side_effect = [
            project_tasks,  # Tasks for project
            []              # No users found
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_entries_by_project(
            "proj-123",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) > 0
        # Should still create entries with "Unknown User"
        assert all(entry.staff_name == "Unknown User" for entry in result)

    def test_total_hours_rounding(self, mock_crud, sample_project, sample_users, date_range):
        """Test that total hours is rounded to 2 decimal places"""
        # Arrange
        tasks_with_precise_time = [
            {
                "id": "task-1",
                "title": "Task 1",
                "due_date": date.today().isoformat(),
                "status": "COMPLETED",
                "project_id": "proj-123",
                "assignee_ids": ["user-1"],
                "time_log": 1.234567  # Many decimal places
            }
        ]
        mock_crud.select.side_effect = [
            [sample_project],
            tasks_with_precise_time,
            sample_users
        ]

        generator = LoggedTimeReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_report(
            scope_type="project",
            scope_id="proj-123",
            start_date=date_range["start_date"],
            end_date=date_range["end_date"]
        )

        # Assert
        assert result.total_hours == 1.23  # Rounded to 2 decimal places
