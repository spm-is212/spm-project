"""
Project Management Page Object Model
"""
from selenium.webdriver.common.by import By
from e2e_tests.pages.base_page import BasePage


class ProjectPage(BasePage):
    """Project management page interactions"""

    # Locators - Update these based on your actual frontend
    CREATE_PROJECT_BUTTON = (By.CSS_SELECTOR, "button:contains('Create'), button:contains('New Project'), [data-testid='create-project-btn']")
    PROJECT_LIST = (By.CSS_SELECTOR, ".project-list, [data-testid='project-list']")
    PROJECT_ITEMS = (By.CSS_SELECTOR, ".project-item, [data-testid='project-item']")

    # Project Form
    PROJECT_NAME_INPUT = (By.CSS_SELECTOR, "input[name='name'], input#name, [data-testid='project-name-input']")
    PROJECT_DESCRIPTION_INPUT = (By.CSS_SELECTOR, "textarea[name='description'], textarea#description, [data-testid='project-description-input']")
    SUBMIT_PROJECT_BUTTON = (By.CSS_SELECTOR, "button[type='submit'], [data-testid='submit-project-btn']")

    # Success/Error Messages
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".success-message, .alert-success, [role='status']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message, .alert-error, [role='alert']")

    def navigate(self):
        """Navigate to project management page"""
        self.navigate_to("/projects")

    def click_create_project(self):
        """Click create project button"""
        self.click(self.CREATE_PROJECT_BUTTON)

    def fill_project_form(self, name, description):
        """Fill out project creation form"""
        self.send_keys(self.PROJECT_NAME_INPUT, name)
        self.send_keys(self.PROJECT_DESCRIPTION_INPUT, description)

    def submit_project(self):
        """Submit project form"""
        self.click(self.SUBMIT_PROJECT_BUTTON)

    def create_project(self, name, description):
        """Complete project creation flow"""
        self.click_create_project()
        self.fill_project_form(name, description)
        self.submit_project()

    def get_project_count(self):
        """Get number of projects in the list"""
        if self.is_element_visible(self.PROJECT_ITEMS):
            projects = self.find_elements(self.PROJECT_ITEMS)
            return len(projects)
        return 0

    def is_project_visible(self, name):
        """Check if project with name is visible"""
        project_locator = (By.XPATH, f"//*[contains(@class, 'project-item') and contains(., '{name}')]")
        return self.is_element_visible(project_locator, timeout=5)

    def get_success_message(self):
        """Get success message text"""
        if self.is_element_visible(self.SUCCESS_MESSAGE, timeout=5):
            return self.get_text(self.SUCCESS_MESSAGE)
        return None

    def get_error_message(self):
        """Get error message text"""
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=5):
            return self.get_text(self.ERROR_MESSAGE)
        return None
