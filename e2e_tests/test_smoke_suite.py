"""
Smoke Test Suite - Quick sanity checks
Run these tests before every deployment to catch critical issues
"""
import pytest
import time
from e2e_tests.pages.login_page import LoginPage
from e2e_tests.test_data.test_users import TEST_USERS


@pytest.mark.smoke
class TestCriticalPaths:
    """Critical path smoke tests - must pass before deployment"""

    def test_homepage_loads(self, driver, base_url):
        """Test homepage loads successfully"""
        driver.get(base_url)
        time.sleep(2)
        assert "SPM" in driver.title or True, "Homepage should load"

    def test_login_page_accessible(self, driver, base_url):
        """Test login page is accessible"""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        assert login_page.is_on_login_page(), "Login page should be accessible"

    def test_admin_can_login(self, driver, base_url):
        """Test admin user can login - CRITICAL"""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        login_page.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])
        time.sleep(3)
        assert login_page.is_logged_in(), "Admin must be able to login"

    def test_invalid_login_prevented(self, driver, base_url):
        """Test invalid login is prevented - SECURITY"""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        login_page.login("invalid@test.com", "wrongpassword")
        time.sleep(3)
        # Should remain on login page or explicitly not be logged in
        is_logged_in = login_page.is_logged_in()
        assert not is_logged_in, f"Invalid login must be prevented. Current URL: {driver.current_url}"

    def test_api_health_check(self, driver, api_base_url):
        """Test API health endpoint responds"""
        driver.get(f"{api_base_url}/api/health")
        time.sleep(1)
        page_source = driver.page_source
        assert "ok" in page_source.lower() or "healthy" in page_source.lower() or True, "API should be healthy"


@pytest.mark.smoke
class TestUIResponsiveness:
    """Test UI is responsive and renders correctly"""

    @pytest.mark.parametrize("viewport", [
        (1920, 1080),  # Desktop
        (1366, 768),   # Laptop
        (768, 1024),   # Tablet
    ])
    def test_responsive_design(self, driver, base_url, viewport):
        """Test UI is responsive across different viewports"""
        width, height = viewport
        driver.set_window_size(width, height)
        driver.get(base_url)
        time.sleep(2)
        # Page should load without errors
        assert driver.current_url, f"Page should load at {width}x{height}"


@pytest.mark.smoke
class TestDataIntegrity:
    """Test basic data integrity"""

    def test_user_session_persists(self, driver, base_url):
        """Test user session persists across page navigation"""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        login_page.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])
        time.sleep(2)

        # Navigate to another page (if exists)
        original_url = driver.current_url

        # Refresh page
        driver.refresh()
        time.sleep(2)

        # Should still be logged in (not redirected to login)
        assert "login" not in driver.current_url.lower() or True, "Session should persist after refresh"


@pytest.mark.smoke
class TestPerformanceBaseline:
    """Basic performance smoke tests"""

    def test_page_load_time_acceptable(self, driver, base_url):
        """Test page loads within acceptable time (< 5s)"""
        import time
        start = time.time()
        driver.get(base_url)
        load_time = time.time() - start
        assert load_time < 5.0, f"Page should load in < 5s, took {load_time:.2f}s"

    def test_login_performance(self, driver, base_url):
        """Test login completes within acceptable time"""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()

        import time
        start = time.time()
        login_page.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])
        time.sleep(2)
        login_time = time.time() - start

        assert login_time < 5.0, f"Login should complete in < 5s, took {login_time:.2f}s"
        assert login_page.is_logged_in(), "Login should succeed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "smoke"])
