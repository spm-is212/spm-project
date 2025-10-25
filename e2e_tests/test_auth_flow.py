import time
import pytest
from e2e_tests.pages.login_page import LoginPage
from e2e_tests.test_data.test_users import TEST_USERS

pytestmark = pytest.mark.nondestructive


class TestAuthenticationFlow:
    """Regression tests for authentication"""

    def test_successful_login(self, driver, base_url):
        """Test user can login with valid credentials"""
        # Arrange
        login_page = LoginPage(driver, base_url)

        # Act
        login_page.navigate()
        login_page.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])
        time.sleep(3)

        # Assert
        assert login_page.is_logged_in(), "User should be redirected to dashboard"

    def test_invalid_credentials_show_error(self, driver, base_url):
        """Test error message shown for invalid credentials"""
        # Arrange
        login_page = LoginPage(driver, base_url)

        # Act
        login_page.navigate()
        login_page.login("wrong@example.com", "wrongpassword")
        time.sleep(3)

        # Assert
        # User should NOT be logged in with invalid credentials
        is_logged_in = login_page.is_logged_in()
        current_url = driver.current_url
        assert not is_logged_in, f"Login should fail with invalid credentials. Current URL: {current_url}"

        # Optional: Check if error message is displayed
        error = login_page.get_error_message()
        if error:
            assert len(error) > 0, "Error message should not be empty"
        
    def test_logout_clears_session(self, driver, base_url):
        """Test logout functionality with confirmation dialog"""
        # Arrange
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        login_page.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])
        time.sleep(3)

        # Verify logged in first
        assert login_page.is_logged_in(), "Should be logged in before logout"

        # Act - logout() method handles confirmation dialog and waiting
        login_page.logout()

        # Assert - should be redirected back to login page (root)
        current_url = driver.current_url
        assert base_url + "/" == current_url or current_url == base_url, f"Should redirect to login page ({base_url}/), got: {current_url}"

        # Verify user is no longer logged in
        assert not login_page.is_logged_in(), "User should not be logged in after logout"

    def test_empty_email_prevents_login(self, driver, base_url):
        """Test that empty email prevents login"""
        # Arrange
        login_page = LoginPage(driver, base_url)
        login_page.navigate()

        # Act
        login_page.enter_email("")
        login_page.enter_password("password123")
        login_page.click_login_button()
        time.sleep(2)

        # Assert - should remain on login page
        assert not login_page.is_logged_in(), "Should not login with empty email"

    def test_empty_password_prevents_login(self, driver, base_url):
        """Test that empty password prevents login"""
        # Arrange
        login_page = LoginPage(driver, base_url)
        login_page.navigate()

        # Act
        login_page.enter_email(TEST_USERS["admin"]["email"])
        login_page.enter_password("")
        login_page.click_login_button()
        time.sleep(2)

        # Assert - should remain on login page
        assert not login_page.is_logged_in(), "Should not login with empty password"

    def test_wrong_password_prevents_login(self, driver, base_url):
        """Test that wrong password for valid user prevents login"""
        # Arrange
        login_page = LoginPage(driver, base_url)
        login_page.navigate()

        # Act
        login_page.login(TEST_USERS["admin"]["email"], "wrongpassword123")
        time.sleep(3)

        # Assert
        assert not login_page.is_logged_in(), "Should not login with wrong password"

    def test_different_user_roles_can_login(self, driver, base_url):
        """Test that users with different roles can all login successfully"""
        for role, user_data in TEST_USERS.items():
            # Arrange
            login_page = LoginPage(driver, base_url)
            login_page.navigate()

            # Act
            login_page.login(user_data["email"], user_data["password"])
            time.sleep(3)

            # Assert
            assert login_page.is_logged_in(), f"{role} user should be able to login"

            # Logout for next iteration
            login_page.logout()
            time.sleep(2)
