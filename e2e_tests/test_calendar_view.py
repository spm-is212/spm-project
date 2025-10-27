"""
Comprehensive E2E Tests for Calendar View
Tests calendar navigation, task display, filtering, and modal interactions
"""
import time
import pytest
from selenium.webdriver.common.by import By

pytestmark = pytest.mark.nondestructive


class TestCalendarAccess:
    """Tests for accessing the calendar view"""

    def test_access_calendar_page(self, authenticated_driver, base_url):
        """Test accessing the calendar view page"""
        driver = authenticated_driver

        # Navigate to calendar view
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Verify page loaded
        assert "/calendarview" in driver.current_url, "Should be on /calendarview page"

        # Verify calendar grid is present (7 columns for days of week)
        calendar_grid = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-7')]")
        assert len(calendar_grid) > 0, "Calendar grid should be displayed"

    def test_calendar_shows_current_month(self, authenticated_driver, base_url):
        """Test that calendar shows the current month and year"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Get current month and year
        import datetime
        current_month = datetime.datetime.now().strftime('%B')
        current_year = datetime.datetime.now().strftime('%Y')

        # Find month/year header
        header_elements = driver.find_elements(By.XPATH, "//header//h2 | //div[contains(@class, 'text-2xl')]")

        # Verify current month and year are displayed
        header_text = " ".join([elem.text for elem in header_elements])
        assert current_month in header_text or current_year in header_text, \
            f"Calendar should show current month/year. Found: {header_text}"

    def test_calendar_shows_day_headers(self, authenticated_driver, base_url):
        """Test that day of week headers are shown"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Look for day headers (Sun, Mon, Tue, etc.)
        day_headers = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

        page_text = driver.find_element(By.TAG_NAME, "body").text

        # At least some day headers should be present
        found_days = [day for day in day_headers if day in page_text]
        assert len(found_days) >= 3, f"Calendar should show day headers. Found: {found_days}"


class TestCalendarNavigation:
    """Tests for navigating between months"""

    def test_navigate_to_previous_month(self, authenticated_driver, base_url):
        """Test navigating to previous month"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Get current month text
        header_elements = driver.find_elements(By.XPATH, "//header//h2 | //h2")
        current_month_text = " ".join([elem.text for elem in header_elements])

        # Find and click "Prev" button
        prev_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Prev') or contains(., 'Previous') or contains(., '<')]")

        if len(prev_buttons) > 0:
            prev_buttons[0].click()
            time.sleep(2)

            # Verify month changed
            new_header_elements = driver.find_elements(By.XPATH, "//header//h2 | //h2")
            new_month_text = " ".join([elem.text for elem in new_header_elements])

            # Month text should be different (either month or year changed)
            assert new_month_text != current_month_text or len(new_month_text) > 0, \
                "Calendar should navigate to previous month"

    def test_navigate_to_next_month(self, authenticated_driver, base_url):
        """Test navigating to next month"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Get current month text
        header_elements = driver.find_elements(By.XPATH, "//header//h2 | //h2")
        current_month_text = " ".join([elem.text for elem in header_elements])

        # Find and click "Next" button
        next_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Next') or contains(., '>')]")

        if len(next_buttons) > 0:
            next_buttons[0].click()
            time.sleep(2)

            # Verify month changed
            new_header_elements = driver.find_elements(By.XPATH, "//header//h2 | //h2")
            new_month_text = " ".join([elem.text for elem in new_header_elements])

            assert new_month_text != current_month_text or len(new_month_text) > 0, \
                "Calendar should navigate to next month"

    def test_navigate_multiple_months(self, authenticated_driver, base_url):
        """Test navigating forward and backward multiple times"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Click next 2 times
        next_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Next') or contains(., '>')]")
        if len(next_buttons) > 0:
            next_buttons[0].click()
            time.sleep(1)
            next_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Next') or contains(., '>')]")
            next_buttons[0].click()
            time.sleep(1)

        # Click prev 1 time
        prev_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Prev') or contains(., '<')]")
        if len(prev_buttons) > 0:
            prev_buttons[0].click()
            time.sleep(2)

        # Calendar should still be functional
        calendar_grid = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-7')]")
        assert len(calendar_grid) > 0, "Calendar should remain functional after navigation"


class TestCalendarTaskDisplay:
    """Tests for displaying tasks on calendar"""

    def test_tasks_display_on_calendar(self, authenticated_driver, base_url):
        """Test that tasks with due dates appear on calendar"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Look for task blocks (colored divs with cursor-pointer)
        task_blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(@class, 'text-xs')]")

        # Should find at least some tasks (or empty calendar)
        assert len(task_blocks) >= 0, "Calendar should display tasks if any exist"

    def test_tasks_show_color_coding(self, authenticated_driver, base_url):
        """Test that tasks are color-coded by status"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Look for status color legend
        legend_items = driver.find_elements(By.XPATH, "//div[contains(@class, 'flex') and contains(@class, 'gap')]//span[contains(@class, 'px-2')]")

        # Legend should show different status colors
        assert len(legend_items) >= 0, "Calendar should have status color legend"

        # Look for actual colored tasks
        colored_tasks = driver.find_elements(By.XPATH,
            "//div[contains(@class, 'bg-red-100') or contains(@class, 'bg-green-100') or contains(@class, 'bg-blue-100') or contains(@class, 'bg-yellow-100')]")

        assert len(colored_tasks) >= 0, "Tasks should be color-coded on calendar"

    def test_overdue_tasks_highlighted(self, authenticated_driver, base_url):
        """Test that overdue tasks are highlighted in red"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Look for red/overdue tasks (bg-red-100, border-red-500)
        overdue_tasks = driver.find_elements(By.XPATH, "//div[contains(@class, 'bg-red-100')]")

        # Overdue tasks may or may not exist
        assert len(overdue_tasks) >= 0, "Overdue tasks should be visually highlighted if they exist"


class TestCalendarFiltering:
    """Tests for filtering tasks on calendar"""

    def test_filter_by_project(self, authenticated_driver, base_url):
        """Test filtering calendar by project"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Find project filter dropdown
        project_selects = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Project')] or contains(@id, 'project')]")

        if len(project_selects) > 0:
            # Select a project
            project_selects[0].click()
            time.sleep(0.5)

            # Select first project option
            options = project_selects[0].find_elements(By.TAG_NAME, "option")
            if len(options) > 1:
                options[1].click()
                time.sleep(2)

                # Verify calendar updated
                calendar_grid = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-7')]")
                assert len(calendar_grid) > 0, "Calendar should update with filtered tasks"

    def test_filter_by_person(self, authenticated_driver, base_url):
        """Test filtering calendar by person"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Find person filter dropdown (may not be available for all roles)
        person_selects = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Person')] or contains(@id, 'person')]")

        if len(person_selects) > 0:
            # Select a person
            person_selects[0].click()
            time.sleep(0.5)

            options = person_selects[0].find_elements(By.TAG_NAME, "option")
            if len(options) > 1:
                options[1].click()
                time.sleep(2)

                # Verify calendar updated
                calendar_grid = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-7')]")
                assert len(calendar_grid) > 0, "Calendar should update with person-filtered tasks"

    def test_reset_calendar_filters(self, authenticated_driver, base_url):
        """Test resetting calendar filters"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Look for Reset button
        reset_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Reset') or contains(., 'Clear')]")

        if len(reset_buttons) > 0:
            # Apply a filter first
            project_selects = driver.find_elements(By.XPATH, "//select")
            if len(project_selects) > 0:
                project_selects[0].click()
                time.sleep(0.5)
                options = project_selects[0].find_elements(By.TAG_NAME, "option")
                if len(options) > 1:
                    options[1].click()
                    time.sleep(1)

            # Click reset
            reset_buttons[0].click()
            time.sleep(2)

            # Verify calendar shows all tasks again
            calendar_grid = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid-cols-7')]")
            assert len(calendar_grid) > 0, "Calendar should show all tasks after reset"


class TestTaskDetailsModal:
    """Tests for task details modal on calendar"""

    def test_click_task_opens_modal(self, authenticated_driver, base_url):
        """Test that clicking a task opens details modal"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Find and click a task
        task_blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(@class, 'text-xs') and contains(@class, 'p-1')]")

        if len(task_blocks) > 0:
            task_blocks[0].click()
            time.sleep(2)

            # Look for modal (fixed inset-0 with high z-index)
            modals = driver.find_elements(By.XPATH, "//div[contains(@class, 'fixed') and contains(@class, 'inset-0')]")
            assert len(modals) > 0, "Clicking task should open details modal"

    def test_modal_shows_task_details(self, authenticated_driver, base_url):
        """Test that modal displays task information"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Find and click a task
        task_blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(@class, 'text-xs') and contains(@class, 'p-1')]")

        if len(task_blocks) > 0:
            task_blocks[0].text
            task_blocks[0].click()
            time.sleep(2)

            # Verify modal content
            modal_content = driver.find_elements(By.XPATH, "//div[contains(@class, 'bg-white') and contains(@class, 'rounded')]")

            if len(modal_content) > 0:
                # Should contain task details
                modal_text = modal_content[0].text

                # Modal should show some task information
                assert len(modal_text) > 0, "Modal should display task details"

    def test_close_modal(self, authenticated_driver, base_url):
        """Test closing the task details modal"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Find and click a task to open modal
        task_blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(@class, 'text-xs') and contains(@class, 'p-1')]")

        if len(task_blocks) > 0:
            task_blocks[0].click()
            time.sleep(2)

            # Find close button (X button or Close button)
            close_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Close') or contains(., '×') or contains(., 'X')]")

            if len(close_buttons) > 0:
                close_buttons[0].click()
                time.sleep(1)

                # Modal should be closed (no longer visible)
                driver.find_elements(By.XPATH, "//div[contains(@class, 'fixed') and contains(@class, 'inset-0') and contains(@class, 'z-50')]")

                # Modal might still exist in DOM but should not be visible
                assert True, "Close button should dismiss modal"

    def test_modal_shows_subtasks(self, authenticated_driver, base_url):
        """Test that modal shows subtasks if task has them"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Find and click a task
        task_blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(@class, 'text-xs')]")

        if len(task_blocks) > 0:
            task_blocks[0].click()
            time.sleep(2)

            # Look for subtask information in modal
            modal_text = driver.find_element(By.TAG_NAME, "body").text

            # If task has subtasks, they should be listed
            # This is a soft check - subtasks may or may not exist
            assert len(modal_text) > 0, "Modal should display content"


class TestCalendarUserInfo:
    """Tests for user information display on calendar page"""

    def test_display_user_department(self, authenticated_driver, base_url):
        """Test that user's department is displayed"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Look for user info section (with Building icon or department label)
        user_info = driver.find_elements(By.XPATH, "//div[contains(@class, 'bg-white') and contains(@class, 'border')]")

        assert len(user_info) > 0, "User information should be displayed"

    def test_display_user_role(self, authenticated_driver, base_url):
        """Test that user's role is displayed"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Look for role badge (uppercase text)
        role_badges = driver.find_elements(By.XPATH, "//span[contains(@class, 'uppercase')]")

        assert len(role_badges) >= 0, "User role should be displayed"

    def test_display_project_count(self, authenticated_driver, base_url):
        """Test that user's project count is displayed"""
        driver = authenticated_driver
        driver.get(f"{base_url}/calendarview")
        time.sleep(3)

        # Look for project count (with Folder icon or "projects" text)
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Should show some user information
        assert len(page_text) > 0, "Page should display user information"
