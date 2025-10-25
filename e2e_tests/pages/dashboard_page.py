"""
Dashboard Page Object Model
"""
from selenium.webdriver.common.by import By
from e2e_tests.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Dashboard page interactions"""

    # Locators - Update these based on your actual frontend
    DASHBOARD_HEADING = (By.CSS_SELECTOR, "h1, h2, [data-testid='dashboard-heading']")
    LOGOUT_BUTTON = (By.CSS_SELECTOR, "button:contains('Logout'), [data-testid='logout-btn']")
    TASKS_LINK = (By.CSS_SELECTOR, "a[href*='task'], [data-testid='tasks-link']")
    PROJECTS_LINK = (By.CSS_SELECTOR, "a[href*='project'], [data-testid='projects-link']")
    USER_PROFILE = (By.CSS_SELECTOR, ".user-profile, [data-testid='user-profile']")

    def navigate(self):
        """Navigate to dashboard page"""
        self.navigate_to("/dashboard")

    def is_on_dashboard(self):
        """Check if on dashboard page"""
        return self.is_element_visible(self.DASHBOARD_HEADING)

    def click_logout(self):
        """Click logout button"""
        self.click(self.LOGOUT_BUTTON)

    def navigate_to_tasks(self):
        """Navigate to tasks page"""
        self.click(self.TASKS_LINK)

    def navigate_to_projects(self):
        """Navigate to projects page"""
        self.click(self.PROJECTS_LINK)

    def get_user_name(self):
        """Get logged in user name"""
        if self.is_element_visible(self.USER_PROFILE):
            return self.get_text(self.USER_PROFILE)
        return None
