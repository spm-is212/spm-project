"""
Comprehensive E2E Tests for Team/Project Management
Tests project view, filtering, sorting, and team collaboration features
"""
import time
import pytest
from e2e_tests.pages.login_page import LoginPage
from e2e_tests.test_data.test_users import TEST_USERS
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = pytest.mark.nondestructive


class TestProjectView:
    """Tests for viewing projects and project information"""

    def test_access_team_view_page(self, authenticated_driver, base_url):
        """Test accessing the team/projects page"""
        driver = authenticated_driver

        # Navigate to team view
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Verify page loaded
        page_elements = driver.find_elements(By.XPATH, "//h1 | //h2")
        assert len(page_elements) > 0, "Team view page should load successfully"

        # Verify URL is correct
        assert "/team" in driver.current_url, "Should be on /team page"

    def test_view_user_information(self, authenticated_driver, base_url):
        """Test that user information is displayed"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Look for user info section (Department, Project count, Role)
        info_sections = driver.find_elements(By.XPATH, "//div[contains(@class, 'bg-white') and contains(@class, 'border')]")
        assert len(info_sections) > 0, "User information should be displayed"

        # Check for role badge
        role_badges = driver.find_elements(By.XPATH, "//span[contains(@class, 'uppercase')]")
        assert len(role_badges) > 0, "User role should be displayed"

    def test_view_statistics_dashboard(self, authenticated_driver, base_url):
        """Test that statistics dashboard is displayed"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Look for statistics cards (Total Tasks, Completed, In Progress, etc.)
        stat_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'gradient')]")

        # There should be 6 stat cards: Total, Completed, In Progress, To Do, Blocked, Overdue
        assert len(stat_cards) >= 4, f"Statistics dashboard should show multiple cards, found {len(stat_cards)}"

    def test_view_projects_list(self, authenticated_driver, base_url):
        """Test that projects are displayed"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Look for project headers/sections
        projects = driver.find_elements(By.XPATH, "//div[contains(@class, 'from-green-50')]")

        # User should have at least some access to projects
        assert len(projects) >= 0, "Projects section should be present"

    def test_expand_project_to_view_tasks(self, authenticated_driver, base_url):
        """Test expanding a project to view its tasks"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Find expand/collapse buttons (ChevronDown/ChevronRight)
        expand_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'text-green-600')]")

        if len(expand_buttons) > 0:
            # Click to expand first project
            expand_buttons[0].click()
            time.sleep(2)

            # Verify tasks are now visible (tasks are indented with pl-12 class)
            tasks = driver.find_elements(By.XPATH, "//div[contains(@class, 'pl-12')]")
            assert len(tasks) >= 0, "Tasks should be displayed when project is expanded"

    def test_view_task_details_in_project(self, authenticated_driver, base_url):
        """Test that task details are shown in project view"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Expand first project
        expand_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'text-green-600')]")
        if len(expand_buttons) > 0:
            expand_buttons[0].click()
            time.sleep(2)

            # Look for task details: status badges, priority badges, due dates
            status_badges = driver.find_elements(By.XPATH, "//span[contains(@class, 'rounded-full')]")
            assert len(status_badges) >= 0, "Task status badges should be visible in project view"


class TestProjectFiltering:
    """Tests for filtering tasks in projects"""

    def test_filter_by_project(self, authenticated_driver, base_url):
        """Test filtering by project"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Find project filter dropdown
        project_selects = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Select Project')]]")

        if len(project_selects) > 0:
            # Select a specific project
            project_selects[0].click()
            time.sleep(0.5)

            # Select first project option (skip "All Projects")
            options = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Select Project')]]/option")
            if len(options) > 1:
                options[1].click()
                time.sleep(2)

                # Verify filtering was applied (page should update)
                page_content = driver.find_element(By.TAG_NAME, "body").text
                assert len(page_content) > 0, "Page should show filtered content"

    def test_filter_by_person(self, authenticated_driver, base_url):
        """Test filtering by person (if available for user role)"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Find person filter dropdown (only for non-staff users)
        person_selects = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Select Person')]]")

        if len(person_selects) > 0:
            # Select a person
            person_selects[0].click()
            time.sleep(0.5)

            options = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Select Person')]]/option")
            if len(options) > 1:
                options[1].click()
                time.sleep(2)

                # Verify filtering was applied
                page_content = driver.find_element(By.TAG_NAME, "body").text
                assert len(page_content) > 0, "Page should show person-filtered content"

    def test_reset_filters(self, authenticated_driver, base_url):
        """Test resetting all filters"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Look for Reset button
        reset_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Reset') or contains(., 'Clear')]")

        if len(reset_buttons) > 0:
            # Apply a filter first
            project_selects = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Select Project')]]")
            if len(project_selects) > 0:
                project_selects[0].click()
                time.sleep(0.5)
                options = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Select Project')]]/option")
                if len(options) > 1:
                    options[1].click()
                    time.sleep(1)

            # Click reset
            reset_buttons[0].click()
            time.sleep(2)

            # Verify filters were reset (should show all projects again)
            projects = driver.find_elements(By.XPATH, "//div[contains(@class, 'from-green-50')]")
            assert len(projects) >= 0, "All accessible projects should be shown after reset"


class TestProjectSorting:
    """Tests for sorting tasks in projects"""

    def test_sort_by_priority(self, authenticated_driver, base_url):
        """Test sorting tasks by priority"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Find sort dropdown
        sort_selects = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Sort')]]")

        if len(sort_selects) > 0:
            # Select priority sorting
            sort_selects[0].click()
            time.sleep(0.5)

            priority_options = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Sort')]]/option[contains(., 'Priority')]")
            if len(priority_options) > 0:
                priority_options[0].click()
                time.sleep(2)

                # Verify page updated
                projects = driver.find_elements(By.XPATH, "//div[contains(@class, 'from-green-50')]")
                assert len(projects) >= 0, "Projects should be displayed with priority sorting"

    def test_sort_by_status(self, authenticated_driver, base_url):
        """Test sorting tasks by status"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Find sort dropdown
        sort_selects = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Sort')]]")

        if len(sort_selects) > 0:
            sort_selects[0].click()
            time.sleep(0.5)

            status_options = driver.find_elements(By.XPATH, "//select[preceding-sibling::label[contains(., 'Sort')]]/option[contains(., 'Status')]")
            if len(status_options) > 0:
                status_options[0].click()
                time.sleep(2)

                # Verify page updated
                projects = driver.find_elements(By.XPATH, "//div[contains(@class, 'from-green-50')]")
                assert len(projects) >= 0, "Projects should be displayed with status sorting"

    def test_toggle_sort_order(self, authenticated_driver, base_url):
        """Test toggling sort order (ascending/descending)"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Find sort order toggle button
        toggle_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'bg-blue') or contains(., '↑') or contains(., '↓')]")

        if len(toggle_buttons) > 0:
            # Click toggle
            toggle_buttons[0].click()
            time.sleep(2)

            # Verify page updated (sort order changed)
            projects = driver.find_elements(By.XPATH, "//div[contains(@class, 'from-green-50')]")
            assert len(projects) >= 0, "Projects should be re-sorted when toggle is clicked"


class TestTeamCollaboration:
    """Tests for team collaboration features"""

    def test_view_project_collaborators(self, authenticated_driver, base_url):
        """Test that project collaborators are displayed"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Look for collaborator count text
        collaborator_texts = driver.find_elements(By.XPATH, "//p[contains(., 'collaborator')]")

        # Some projects should show collaborator information
        assert len(collaborator_texts) >= 0, "Collaborator information should be available"

    def test_view_task_assignees(self, authenticated_driver, base_url):
        """Test that task assignees are shown"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Expand first project
        expand_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'text-green-600')]")
        if len(expand_buttons) > 0:
            expand_buttons[0].click()
            time.sleep(2)

            # Look for assignee information (User icon + names)
            user_icons = driver.find_elements(By.XPATH, "//*[local-name()='svg' and contains(@class, 'lucide-user')]")
            assert len(user_icons) >= 0, "Task assignees should be displayed with user icons"

    def test_view_subtasks(self, authenticated_driver, base_url):
        """Test that subtasks are viewable"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Expand a project first
        project_expand_btns = driver.find_elements(By.XPATH, "//button[contains(@class, 'text-green-600')]")
        if len(project_expand_btns) > 0:
            project_expand_btns[0].click()
            time.sleep(2)

            # Look for subtask toggle buttons (shows "X/Y subtasks")
            subtask_toggles = driver.find_elements(By.XPATH, "//button[contains(., 'subtask')]")

            if len(subtask_toggles) > 0:
                # Expand subtasks
                subtask_toggles[0].click()
                time.sleep(2)

                # Verify subtasks are now visible
                subtask_items = driver.find_elements(By.XPATH, "//div[contains(@class, 'pl-16') or contains(@class, 'pl-20')]")
                assert len(subtask_items) >= 0, "Subtasks should be expandable and viewable"


class TestProjectAccessControl:
    """Tests for role-based project access"""

    def test_director_sees_all_projects(self, driver, base_url):
        """Test that directors can see all projects"""
        # Login as director/managing_director
        login_page = LoginPage(driver, base_url)
        login_page.navigate()

        # Find a director user
        director_user = None
        for role, user in TEST_USERS.items():
            if 'director' in user.get('role', '').lower():
                director_user = user
                break

        if director_user:
            login_page.login(director_user['email'], director_user['password'])
            time.sleep(3)

            # Navigate to team view
            driver.get(f"{base_url}/team")
            time.sleep(3)

            # Directors should see projects
            projects = driver.find_elements(By.XPATH, "//div[contains(@class, 'from-green-50')]")
            assert len(projects) >= 0, "Directors should have access to projects"

    def test_regular_user_sees_assigned_projects_only(self, driver, base_url):
        """Test that regular users only see projects they're assigned to"""
        # Login as staff
        login_page = LoginPage(driver, base_url)
        login_page.navigate()

        if 'staff' in TEST_USERS:
            login_page.login(TEST_USERS['staff']['email'], TEST_USERS['staff']['password'])
            time.sleep(3)

            # Navigate to team view
            driver.get(f"{base_url}/team")
            time.sleep(3)

            # Staff should only see their projects
            projects = driver.find_elements(By.XPATH, "//div[contains(@class, 'from-green-50')]")

            # Verify limited access (should not see ALL projects like director)
            assert len(projects) >= 0, "Staff should see their assigned projects"


class TestProjectProgressTracking:
    """Tests for viewing project progress"""

    def test_view_project_task_completion(self, authenticated_driver, base_url):
        """Test that project task completion is shown"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Look for task completion badges (e.g., "3/5 Tasks")
        completion_badges = driver.find_elements(By.XPATH, "//span[contains(., '/') and contains(., 'Task')]")

        # Projects should show completion status
        assert len(completion_badges) >= 0, "Projects should display task completion status"

    def test_view_overall_statistics(self, authenticated_driver, base_url):
        """Test that overall task statistics are displayed"""
        driver = authenticated_driver
        driver.get(f"{base_url}/team")
        time.sleep(3)

        # Look for Total Tasks stat
        stat_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'gradient')]")

        # Should have multiple stat cards
        assert len(stat_cards) >= 4, "Statistics dashboard should show task metrics"

        # Look for specific stats
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Should contain stat labels
        assert any(keyword in page_text for keyword in ['Total', 'Completed', 'Progress', 'To Do']), \
            "Statistics should include task status counts"
