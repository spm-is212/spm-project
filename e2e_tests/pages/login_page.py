"""
Login Page Object Model
"""
from selenium.webdriver.common.by import By
from e2e_tests.pages.base_page import BasePage


class LoginPage(BasePage):
    """Login page interactions"""

    # Locators - Update these based on your actual frontend
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email'], input[name='email'], input#email")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password'], input[name='password'], input#password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message, .alert-error, [role='alert']")
    SIGNUP_LINK = (By.CSS_SELECTOR, "a[href*='signup'], a[href*='register']")
    FORGOT_PASSWORD_LINK = (By.CSS_SELECTOR, "a[href*='forgot'], a[href*='reset']")

    def navigate(self):
        """Navigate to login page"""
        self.navigate_to("/")

    def enter_email(self, email):
        """Enter email"""
        self.send_keys(self.EMAIL_INPUT, email)

    def enter_password(self, password):
        """Enter password"""
        self.send_keys(self.PASSWORD_INPUT, password)

    def click_login_button(self):
        """Click login button"""
        self.click(self.LOGIN_BUTTON)

    def login(self, email, password):
        """Complete login process"""
        self.enter_email(email)
        self.enter_password(password)
        self.click_login_button()

    def is_logged_in(self):
        """Check if login successful by checking URL"""
        try:
            self.wait_for_url_to_contain("/")
            return "login" not in self.get_current_url().lower()
        except:
            return False

    def get_error_message(self):
        """Get error message if login fails"""
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=3):
            return self.get_text(self.ERROR_MESSAGE)
        return None

    def is_on_login_page(self):
        """Verify we're on the login page"""
        return self.is_element_visible(self.LOGIN_BUTTON)

    def click_signup_link(self):
        """Click signup/register link"""
        self.click(self.SIGNUP_LINK)

    def click_forgot_password(self):
        """Click forgot password link"""
        self.click(self.FORGOT_PASSWORD_LINK)
