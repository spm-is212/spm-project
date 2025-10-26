"""
Task Management Page Object Model
"""
from selenium.webdriver.common.by import By
from e2e_tests.pages.base_page import BasePage


class TaskPage(BasePage):
    """Task management page interactions"""

    # Locators - Update these based on your actual frontend
    CREATE_TASK_BUTTON = (By.CSS_SELECTOR, "button:contains('Create'), button:contains('New Task'), [data-testid='create-task-btn']")
    TASK_LIST = (By.CSS_SELECTOR, ".task-list, [data-testid='task-list']")
    TASK_ITEMS = (By.CSS_SELECTOR, ".task-item, [data-testid='task-item']")

    # Task Form
    TASK_TITLE_INPUT = (By.CSS_SELECTOR, "input[name='title'], input#title, [data-testid='task-title-input']")
    TASK_DESCRIPTION_INPUT = (By.CSS_SELECTOR, "textarea[name='description'], textarea#description, [data-testid='task-description-input']")
    TASK_DUE_DATE_INPUT = (By.CSS_SELECTOR, "input[type='date'], input[name='due_date'], [data-testid='task-due-date-input']")
    TASK_PRIORITY_SELECT = (By.CSS_SELECTOR, "select[name='priority'], [data-testid='task-priority-select']")
    SUBMIT_TASK_BUTTON = (By.CSS_SELECTOR, "button[type='submit'], [data-testid='submit-task-btn']")

    # Success/Error Messages
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".success-message, .alert-success, [role='status']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message, .alert-error, [role='alert']")

    def navigate(self):
        """Navigate to task management page"""
        self.navigate_to("/tasks")

    def click_create_task(self):
        """Click create task button"""
        self.click(self.CREATE_TASK_BUTTON)

    def fill_task_form(self, title, description, due_date=None, priority=None):
        """Fill out task creation/edit form"""
        self.send_keys(self.TASK_TITLE_INPUT, title)
        self.send_keys(self.TASK_DESCRIPTION_INPUT, description)

        if due_date:
            self.send_keys(self.TASK_DUE_DATE_INPUT, due_date)

        if priority:
            priority_select = self.find_element(self.TASK_PRIORITY_SELECT)
            priority_select.click()
            option = (By.CSS_SELECTOR, f"option[value='{priority}']")
            self.click(option)

    def submit_task(self):
        """Submit task form"""
        self.click(self.SUBMIT_TASK_BUTTON)

    def create_task(self, title, description, due_date=None, priority=None):
        """Complete task creation flow"""
        self.click_create_task()
        self.fill_task_form(title, description, due_date, priority)
        self.submit_task()

    def get_task_count(self):
        """Get number of tasks in the list"""
        if self.is_element_visible(self.TASK_ITEMS):
            tasks = self.find_elements(self.TASK_ITEMS)
            return len(tasks)
        return 0

    def is_task_visible(self, title):
        """Check if task with title is visible"""
        task_locator = (By.XPATH, f"//*[contains(@class, 'task-item') and contains(., '{title}')]")
        return self.is_element_visible(task_locator, timeout=5)

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
