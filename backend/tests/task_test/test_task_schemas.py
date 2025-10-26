"""
Tests for task schema validation
"""
import pytest
from datetime import date, timedelta
from pydantic import ValidationError
from backend.schemas.task import TaskCreate, SubtaskCreate, TaskUpdate, SubtaskUpdate


class TestTaskCreateValidation:
    """Test TaskCreate schema validators"""

    def test_empty_title_fails(self):
        """Test that empty title raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="   ",  # Empty after strip
                description="Valid description",
                priority=5,
                assignee_ids=["user1"],
                due_date=date.today() + timedelta(days=1)
            )
        assert "Title cannot be empty" in str(exc_info.value)

    def test_empty_description_fails(self):
        """Test that empty description raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Valid title",
                description="   ",  # Empty after strip
                priority=5,
                assignee_ids=["user1"],
                due_date=date.today() + timedelta(days=1)
            )
        assert "Description cannot be empty" in str(exc_info.value)

    def test_priority_too_low_fails(self):
        """Test that priority < 1 raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Valid title",
                description="Valid description",
                priority=0,  # Too low
                assignee_ids=["user1"],
                due_date=date.today() + timedelta(days=1)
            )
        assert "Priority must be between 1 and 10" in str(exc_info.value)

    def test_priority_too_high_fails(self):
        """Test that priority > 10 raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Valid title",
                description="Valid description",
                priority=11,  # Too high
                assignee_ids=["user1"],
                due_date=date.today() + timedelta(days=1)
            )
        assert "Priority must be between 1 and 10" in str(exc_info.value)

    def test_too_many_assignees_fails(self):
        """Test that more than 5 assignees raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Valid title",
                description="Valid description",
                priority=5,
                assignee_ids=["user1", "user2", "user3", "user4", "user5", "user6"],  # 6 assignees
                due_date=date.today() + timedelta(days=1)
            )
        assert "Maximum of 5 assignees allowed" in str(exc_info.value)

    def test_past_due_date_fails(self):
        """Test that past due date raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Valid title",
                description="Valid description",
                priority=5,
                assignee_ids=["user1"],
                due_date=date.today() - timedelta(days=1)  # Yesterday
            )
        assert "Due date cannot be in the past" in str(exc_info.value)

    def test_recurrence_interval_zero_with_rule_fails(self):
        """Test that recurrence_interval < 1 with recurrence_rule fails"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Valid title",
                description="Valid description",
                priority=5,
                assignee_ids=["user1"],
                due_date=date.today() + timedelta(days=1),
                recurrence_rule="DAILY",
                recurrence_interval=0  # Invalid when rule is set
            )
        assert "Recurrence interval must be at least 1" in str(exc_info.value)

    def test_recurrence_end_before_due_date_fails(self):
        """Test that recurrence_end_date before due_date fails"""
        due = date.today() + timedelta(days=7)
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Valid title",
                description="Valid description",
                priority=5,
                assignee_ids=["user1"],
                due_date=due,
                recurrence_rule="WEEKLY",
                recurrence_interval=1,
                recurrence_end_date=due - timedelta(days=1)  # Before due date
            )
        assert "Recurrence end date cannot be before the due date" in str(exc_info.value)

    def test_empty_file_url_fails(self):
        """Test that empty file_url raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(
                title="Valid title",
                description="Valid description",
                priority=5,
                assignee_ids=["user1"],
                due_date=date.today() + timedelta(days=1),
                file_url="   "  # Empty after strip
            )
        assert "File URL cannot be empty" in str(exc_info.value)


class TestSubtaskCreateValidation:
    """Test SubtaskCreate schema validators"""

    def test_empty_title_fails(self):
        """Test that empty subtask title raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            SubtaskCreate(
                title="   ",
                description="Valid description",
                due_date=date.today() + timedelta(days=1)
            )
        assert "Title cannot be empty" in str(exc_info.value)

    def test_empty_description_fails(self):
        """Test that empty subtask description raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            SubtaskCreate(
                title="Valid title",
                description="   ",
                due_date=date.today() + timedelta(days=1)
            )
        assert "Description cannot be empty" in str(exc_info.value)

    def test_past_due_date_fails(self):
        """Test that past due date for subtask raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            SubtaskCreate(
                title="Valid title",
                description="Valid description",
                due_date=date.today() - timedelta(days=1)
            )
        assert "Due date cannot be in the past" in str(exc_info.value)


class TestTaskUpdateValidation:
    """Test TaskUpdate schema validators"""

    def test_empty_title_fails(self):
        """Test that empty title in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(title="   ")
        assert "Title cannot be empty" in str(exc_info.value)

    def test_empty_description_fails(self):
        """Test that empty description in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(description="   ")
        assert "Description cannot be empty" in str(exc_info.value)

    def test_priority_too_low_fails(self):
        """Test that priority < 1 in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(priority=0)
        assert "Priority must be between 1 and 10" in str(exc_info.value)

    def test_priority_too_high_fails(self):
        """Test that priority > 10 in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(priority=11)
        assert "Priority must be between 1 and 10" in str(exc_info.value)

    def test_too_many_assignees_fails(self):
        """Test that more than 5 assignees in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(assignee_ids=["u1", "u2", "u3", "u4", "u5", "u6"])
        assert "Maximum of 5 assignees allowed" in str(exc_info.value)

    def test_past_due_date_fails(self):
        """Test that past due date in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(due_date=date.today() - timedelta(days=1))
        assert "Due date cannot be in the past" in str(exc_info.value)

    def test_recurrence_end_before_due_date_fails(self):
        """Test that recurrence_end_date before due_date in update fails"""
        due = date.today() + timedelta(days=7)
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(
                due_date=due,
                recurrence_end_date=due - timedelta(days=1)
            )
        assert "Recurrence end date cannot be before the due date" in str(exc_info.value)

    def test_empty_file_url_fails(self):
        """Test that empty file_url in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdate(file_url="   ")
        assert "File URL cannot be empty" in str(exc_info.value)


class TestSubtaskUpdateValidation:
    """Test SubtaskUpdate schema validators"""

    def test_empty_title_fails(self):
        """Test that empty subtask title in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            SubtaskUpdate(title="   ")
        assert "Title cannot be empty" in str(exc_info.value)

    def test_empty_description_fails(self):
        """Test that empty subtask description in update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            SubtaskUpdate(description="   ")
        assert "Description cannot be empty" in str(exc_info.value)

    def test_past_due_date_fails(self):
        """Test that past due date for subtask update raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            SubtaskUpdate(due_date=date.today() - timedelta(days=1))
        assert "Due date cannot be in the past" in str(exc_info.value)
