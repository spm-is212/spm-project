import pytest
from e2e_tests.pages.login_page import LoginPage

class TestAuthenticationFlow:
    """Regression tests for authentication"""
    
    def test_successful_login(self, driver, base_url):
        """Test user can login with valid credentials"""
        # Arrange
        login_page = LoginPage(driver, base_url)
        
        # Act
        login_page.navigate()
        login_page.login("admin@example.com", "password123")
        
        # Assert
        assert login_page.is_logged_in(), "User should be redirected to dashboard"
        
    def test_invalid_credentials_show_error(self, driver, base_url):
        """Test error message shown for invalid credentials"""
        # Arrange
        login_page = LoginPage(driver, base_url)
        
        # Act
        login_page.navigate()
        login_page.login("wrong@example.com", "wrongpassword")
        
        # Assert
        error = login_page.get_error_message()
        assert error is not None, "Error message should be displayed"
        assert "Invalid credentials" in error
        
    def test_logout_clears_session(self, driver, base_url):
        """Test logout functionality"""
        # Arrange
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        login_page.login("admin@example.com", "password123")
        
        # Act
        logout_button = driver.find_element(By.ID, "logout-btn")
        logout_button.click()
        
        # Assert
        assert "/login" in driver.current_url
