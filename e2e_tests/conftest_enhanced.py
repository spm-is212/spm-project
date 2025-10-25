"""
Enhanced pytest configuration with comprehensive fixtures
Rename this to conftest.py to use
"""
import pytest
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from e2e_tests.pages.login_page import LoginPage
from e2e_tests.test_data.test_users import TEST_USERS


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application"""
    return "http://localhost:5173"


@pytest.fixture(scope="session")
def api_base_url():
    """API base URL"""
    return "http://localhost:8000"


@pytest.fixture(scope="session", autouse=True)
def check_servers(base_url, api_base_url):
    """Check if servers are running"""
    max_retries = 3
    retry_delay = 2

    # Check backend
    backend_running = False
    for i in range(max_retries):
        try:
            response = requests.get(f"{api_base_url}/api/health", timeout=2)
            if response.status_code == 200:
                backend_running = True
                print(f"\n✓ Backend running at {api_base_url}")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(retry_delay)

    if not backend_running:
        pytest.fail(f"\n\n❌ Backend NOT running at {api_base_url}")

    # Check frontend
    frontend_running = False
    for i in range(max_retries):
        try:
            response = requests.get(base_url, timeout=2)
            if response.status_code in [200, 304]:
                frontend_running = True
                print(f"✓ Frontend running at {base_url}")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(retry_delay)

    if not frontend_running:
        pytest.fail(f"\n\n❌ Frontend NOT running at {base_url}")

    yield


@pytest.fixture(scope="function")
def driver():
    """Setup Chrome WebDriver"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    driver.maximize_window()

    yield driver

    driver.quit()


@pytest.fixture(scope="function")
def authenticated_driver(driver, base_url):
    """Driver with authenticated session"""
    login_page = LoginPage(driver, base_url)
    login_page.navigate()
    login_page.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])
    time.sleep(2)  # Wait for auth to complete
    yield driver


@pytest.fixture(scope="function")
def login_page(driver, base_url):
    """Login page fixture"""
    return LoginPage(driver, base_url)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, driver):
    """Take screenshot on test failure"""
    yield
    if request.node.rep_call.failed:
        test_name = request.node.name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/{test_name}_{timestamp}.png"
        driver.save_screenshot(filename)
        print(f"\nScreenshot: {filename}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to make test result available to fixtures"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
