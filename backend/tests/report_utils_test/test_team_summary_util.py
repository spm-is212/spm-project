from datetime import date, timedelta
from io import BytesIO
from backend.utils.report_util.team_summary_util import TeamSummaryReportGenerator
from backend.schemas.report_schemas import TeamSummaryResponse, StaffTaskSummary


class TestTeamSummaryReportGenerator:
    """Unit tests for TeamSummaryReportGenerator class"""

    def test_generate_report_by_department(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test generating team summary report for a department"""
        # Arrange
        mock_crud.select.side_effect = [
            sample_users,  # For get_users_by_department
            sample_tasks   # For get_all_tasks
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_report(
            scope_type="department",
            scope_id="Engineering",
            time_frame="weekly",
            start_date=date_range["start_date"],
            end_date=date_range["end_date"]
        )

        # Assert
        assert isinstance(result, TeamSummaryResponse)
        assert result.scope_type == "department"
        assert result.scope_id == "Engineering"
        assert result.scope_name == "Engineering"
        assert result.time_frame == "weekly"
        assert result.total_staff > 0

    def test_generate_report_by_project(self, mock_crud, sample_project, sample_tasks, sample_users, date_range):
        """Test generating team summary report for a project"""
        # Arrange
        project_tasks = [sample_tasks[0], sample_tasks[1], sample_tasks[3]]
        mock_crud.select.side_effect = [
            [sample_project],  # For _get_scope_name
            project_tasks,     # Tasks for project
            sample_users       # For user mapping
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_report(
            scope_type="project",
            scope_id="proj-123",
            time_frame="monthly",
            start_date=date_range["start_date"],
            end_date=date_range["end_date"]
        )

        # Assert
        assert isinstance(result, TeamSummaryResponse)
        assert result.scope_type == "project"
        assert result.scope_id == "proj-123"
        assert result.scope_name == "Test Project"
        assert result.time_frame == "monthly"
        assert result.total_staff > 0

    def test_get_scope_name_for_department(self, mock_crud):
        """Test getting scope name for a department"""
        # Arrange
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_scope_name("department", "Engineering")

        # Assert
        assert result == "Engineering"

    def test_get_scope_name_for_project(self, mock_crud, sample_project):
        """Test getting scope name for a project"""
        # Arrange
        mock_crud.select.return_value = [sample_project]

        generator = TeamSummaryReportGenerator()
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

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_scope_name("project", "proj-999")

        # Assert
        assert result == "Unknown Project"

    def test_get_summaries_by_department(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test getting task summaries for a department"""
        # Arrange
        mock_crud.select.side_effect = [
            sample_users,  # All users
            sample_tasks   # All tasks
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_summaries_by_department(
            "Engineering",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) > 0
        assert all(isinstance(summary, StaffTaskSummary) for summary in result)
        # Check that summaries are for users in Engineering department
        staff_names = [summary.staff_name for summary in result]
        assert "user1@test.com" in staff_names or "user2@test.com" in staff_names

    def test_get_summaries_by_department_case_insensitive(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test that department matching is case insensitive"""
        # Arrange
        mock_crud.select.side_effect = [
            sample_users,  # All users
            sample_tasks   # All tasks
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_summaries_by_department(
            "engineering",  # lowercase
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) > 0

    def test_get_summaries_by_department_excludes_staff_without_tasks(self, mock_crud, sample_tasks, date_range):
        """Test that staff without tasks are excluded from results"""
        # Arrange
        users_with_no_tasks = [
            {
                "uuid": "user-999",
                "email": "notask@test.com",
                "departments": ["Engineering"]
            }
        ]
        mock_crud.select.side_effect = [
            users_with_no_tasks,  # User with no tasks
            sample_tasks          # All tasks (none assigned to user-999)
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_summaries_by_department(
            "Engineering",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) == 0  # Staff with 0 tasks should be excluded

    def test_get_summaries_by_project(self, mock_crud, sample_users, sample_tasks, date_range):
        """Test getting task summaries for a project"""
        # Arrange
        project_tasks = [sample_tasks[0], sample_tasks[1], sample_tasks[3]]
        mock_crud.select.side_effect = [
            project_tasks,  # Tasks for project
            sample_users    # All users for mapping
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_summaries_by_project(
            "proj-123",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) > 0
        assert all(isinstance(summary, StaffTaskSummary) for summary in result)

    def test_get_summaries_by_project_no_tasks(self, mock_crud, sample_users, date_range):
        """Test getting summaries for project with no tasks"""
        # Arrange
        mock_crud.select.side_effect = [
            [],           # No tasks
            sample_users  # All users
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_summaries_by_project(
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
        generator = TeamSummaryReportGenerator()
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
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._filter_by_date_range(
            tasks,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )

        # Assert
        assert len(result) == 0

    def test_aggregate_task_counts(self, mock_crud):
        """Test aggregating task counts by status"""
        # Arrange
        today = date.today()
        tasks = [
            {
                "status": "BLOCKED",
                "due_date": (today + timedelta(days=1)).isoformat()
            },
            {
                "status": "IN_PROGRESS",
                "due_date": (today + timedelta(days=2)).isoformat()
            },
            {
                "status": "COMPLETED",
                "due_date": (today - timedelta(days=1)).isoformat()
            },
            {
                "status": "TO_DO",
                "due_date": (today - timedelta(days=5)).isoformat()  # Overdue
            }
        ]
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._aggregate_task_counts("user@test.com", tasks)

        # Assert
        assert isinstance(result, StaffTaskSummary)
        assert result.staff_name == "user@test.com"
        assert result.blocked == 1
        assert result.in_progress == 1
        assert result.completed == 1
        assert result.overdue == 1
        assert result.total_tasks == 4

    def test_aggregate_task_counts_completed_not_overdue(self, mock_crud):
        """Test that completed tasks are not counted as overdue"""
        # Arrange
        today = date.today()
        tasks = [
            {
                "status": "COMPLETED",
                "due_date": (today - timedelta(days=10)).isoformat()  # Past due but completed
            }
        ]
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._aggregate_task_counts("user@test.com", tasks)

        # Assert
        assert result.completed == 1
        assert result.overdue == 0
        assert result.total_tasks == 1

    def test_aggregate_task_counts_overdue_takes_precedence(self, mock_crud):
        """Test that overdue status takes precedence in counting"""
        # Arrange
        today = date.today()
        tasks = [
            {
                "status": "IN_PROGRESS",
                "due_date": (today - timedelta(days=5)).isoformat()  # Overdue and in progress
            }
        ]
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._aggregate_task_counts("user@test.com", tasks)

        # Assert
        assert result.overdue == 1
        assert result.in_progress == 0  # Not counted in progress since it's overdue
        assert result.total_tasks == 1

    def test_aggregate_task_counts_empty_tasks(self, mock_crud):
        """Test aggregating counts with no tasks"""
        # Arrange
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._aggregate_task_counts("user@test.com", [])

        # Assert
        assert result.staff_name == "user@test.com"
        assert result.blocked == 0
        assert result.in_progress == 0
        assert result.completed == 0
        assert result.overdue == 0
        assert result.total_tasks == 0

    def test_aggregate_task_counts_handles_missing_status(self, mock_crud):
        """Test handling tasks without status field"""
        # Arrange
        today = date.today()
        tasks = [
            {
                "due_date": (today + timedelta(days=1)).isoformat()
                # Missing status field
            }
        ]
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._aggregate_task_counts("user@test.com", tasks)

        # Assert
        # Should default to "TO_DO" and not count it in any specific status
        assert result.total_tasks == 0  # Not counted since status defaults to TO_DO

    def test_aggregate_task_counts_handles_missing_due_date(self, mock_crud):
        """Test handling tasks without due_date for overdue calculation"""
        # Arrange
        tasks = [
            {
                "status": "IN_PROGRESS"
                # Missing due_date
            }
        ]
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._aggregate_task_counts("user@test.com", tasks)

        # Assert
        assert result.in_progress == 1
        assert result.overdue == 0  # Cannot be overdue without due_date

    def test_generate_excel_bytes(self, mock_crud):
        """Test generating Excel file returns BytesIO"""
        # Arrange
        today = date.today()
        staff_summaries = [
            StaffTaskSummary(
                staff_name="user@test.com",
                blocked=1,
                in_progress=2,
                completed=3,
                overdue=1,
                total_tasks=7
            )
        ]
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_excel_bytes(
            scope_type="project",
            scope_name="Test Project",
            time_frame="weekly",
            start_date=today,
            end_date=today + timedelta(days=7),
            staff_summaries=staff_summaries
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
        staff_summaries = [
            StaffTaskSummary(
                staff_name="user@test.com",
                blocked=1,
                in_progress=2,
                completed=3,
                overdue=1,
                total_tasks=7
            )
        ]
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_pdf_bytes(
            scope_type="project",
            scope_name="Test Project",
            time_frame="weekly",
            start_date=today,
            end_date=today + timedelta(days=7),
            staff_summaries=staff_summaries
        )

        # Assert
        assert isinstance(result, BytesIO)
        assert result.tell() == 0  # Check it's seeked to start
        content = result.read()
        assert len(content) > 0  # Check it has content
        assert content[:4] == b'%PDF'  # Check it's a PDF

    def test_generate_excel_bytes_with_empty_summaries(self, mock_crud):
        """Test generating Excel with no staff summaries"""
        # Arrange
        today = date.today()
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_excel_bytes(
            scope_type="project",
            scope_name="Test Project",
            time_frame="monthly",
            start_date=today,
            end_date=today + timedelta(days=30),
            staff_summaries=[]
        )

        # Assert
        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0  # Still produces a valid file

    def test_generate_pdf_bytes_with_empty_summaries(self, mock_crud):
        """Test generating PDF with no staff summaries"""
        # Arrange
        today = date.today()
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator.generate_pdf_bytes(
            scope_type="project",
            scope_name="Test Project",
            time_frame="monthly",
            start_date=today,
            end_date=today + timedelta(days=30),
            staff_summaries=[]
        )

        # Assert
        assert isinstance(result, BytesIO)
        content = result.read()
        assert len(content) > 0  # Still produces a valid file
        assert content[:4] == b'%PDF'

    def test_get_summaries_by_project_handles_unknown_user(self, mock_crud, sample_tasks, date_range):
        """Test handling of tasks with unknown user IDs"""
        # Arrange
        project_tasks = [sample_tasks[0]]
        mock_crud.select.side_effect = [
            project_tasks,  # Tasks for project
            []              # No users found
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_summaries_by_project(
            "proj-123",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) > 0
        # Should still create summaries with "Unknown User"
        assert all(summary.staff_name == "Unknown User" for summary in result)

    def test_get_summaries_by_project_aggregates_multiple_tasks_per_user(self, mock_crud, sample_users, date_range):
        """Test that multiple tasks for same user are aggregated correctly"""
        # Arrange
        today = date.today()
        tasks_for_one_user = [
            {
                "id": "task-1",
                "status": "COMPLETED",
                "due_date": (today - timedelta(days=1)).isoformat(),
                "project_id": "proj-123",
                "assignee_ids": ["user-1"]
            },
            {
                "id": "task-2",
                "status": "IN_PROGRESS",
                "due_date": (today + timedelta(days=1)).isoformat(),
                "project_id": "proj-123",
                "assignee_ids": ["user-1"]
            },
            {
                "id": "task-3",
                "status": "BLOCKED",
                "due_date": (today + timedelta(days=2)).isoformat(),
                "project_id": "proj-123",
                "assignee_ids": ["user-1"]
            }
        ]
        mock_crud.select.side_effect = [
            tasks_for_one_user,  # Tasks for project
            sample_users         # All users
        ]

        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._get_summaries_by_project(
            "proj-123",
            date_range["start_date"],
            date_range["end_date"]
        )

        # Assert
        assert len(result) == 1  # Only one user
        summary = result[0]
        assert summary.staff_name == "user1@test.com"
        assert summary.completed == 1
        assert summary.in_progress == 1
        assert summary.blocked == 1
        assert summary.total_tasks == 3

    def test_aggregate_task_counts_various_status_values(self, mock_crud):
        """Test aggregating with various status values"""
        # Arrange
        today = date.today()
        tasks = [
            {"status": "BLOCKED", "due_date": (today + timedelta(days=1)).isoformat()},
            {"status": "BLOCKED", "due_date": (today + timedelta(days=2)).isoformat()},
            {"status": "IN_PROGRESS", "due_date": (today + timedelta(days=3)).isoformat()},
            {"status": "IN_PROGRESS", "due_date": (today + timedelta(days=4)).isoformat()},
            {"status": "IN_PROGRESS", "due_date": (today + timedelta(days=5)).isoformat()},
            {"status": "COMPLETED", "due_date": (today - timedelta(days=1)).isoformat()},
            {"status": "TO_DO", "due_date": (today - timedelta(days=10)).isoformat()},  # Overdue
            {"status": "TO_DO", "due_date": (today - timedelta(days=5)).isoformat()},   # Overdue
        ]
        generator = TeamSummaryReportGenerator()
        generator.crud = mock_crud

        # Act
        result = generator._aggregate_task_counts("user@test.com", tasks)

        # Assert
        assert result.blocked == 2
        assert result.in_progress == 3
        assert result.completed == 1
        assert result.overdue == 2
        assert result.total_tasks == 8
