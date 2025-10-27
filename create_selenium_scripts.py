#!/usr/bin/env python3
"""
Script to generate comprehensive Selenium test suite
Run this to create all necessary Page Objects and test files
"""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
E2E_DIR = os.path.join(BASE_DIR, "e2e_tests")
PAGES_DIR = os.path.join(E2E_DIR, "pages")
HELPERS_DIR = os.path.join(E2E_DIR, "helpers")
DATA_DIR = os.path.join(E2E_DIR, "test_data")

# Ensure directories exist
os.makedirs(PAGES_DIR, exist_ok=True)
os.makedirs(HELPERS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# File contents
FILES = {
    # Test Data
    f"{DATA_DIR}/test_users.py": '''"""
Test user data for E2E tests
"""

TEST_USERS = {
    "admin": {
        "email": "admin@spm.com",
        "password": "Admin123!",
        "role": "admin"
    },
    "manager": {
        "email": "manager@spm.com",
        "password": "Manager123!",
        "role": "manager"
    },
    "staff": {
        "email": "staff@spm.com",
        "password": "Staff123!",
        "role": "staff"
    }
}

TEST_TASKS = {
    "basic_task": {
        "title": "Test Task",
        "description": "This is a test task description",
        "priority": "5",
        "status": "TO_DO"
    },
    "high_priority_task": {
        "title": "Urgent Task",
        "description": "High priority urgent task",
        "priority": "9",
        "status": "IN_PROGRESS"
    }
}

TEST_PROJECTS = {
    "basic_project": {
        "name": "Test Project",
        "description": "This is a test project"
    }
}
''',

    # Helpers
    f"{HELPERS_DIR}/test_helpers.py": '''"""
Helper functions for E2E tests
"""
import time
from datetime import datetime, timedelta


def generate_unique_email():
    """Generate unique email for testing"""
    timestamp = int(time.time())
    return f"test_{timestamp}@spm.com"


def generate_future_date(days=7):
    """Generate future date string"""
    future_date = datetime.now() + timedelta(days=days)
    return future_date.strftime("%Y-%m-%d")


def wait_for_page_load(driver, timeout=10):
    """Wait for page to load"""
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def take_screenshot_on_failure(driver, test_name):
    """Take screenshot when test fails"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots/{test_name}_{timestamp}.png"
    driver.save_screenshot(filename)
    print(f"Screenshot saved: {filename}")
''',

    # Page Objects
    f"{PAGES_DIR}/__init__.py": '''"""
Page Objects Package
"""
from .login_page import LoginPage
from .dashboard_page import DashboardPage
from .task_page import TaskPage
from .project_page import ProjectPage

__all__ = ["LoginPage", "DashboardPage", "TaskPage", "ProjectPage"]
''',

    # Enhanced conftest with fixtures
    f"{E2E_DIR}/conftest_enhanced.py": '''"""
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
                print(f"\\n✓ Backend running at {api_base_url}")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(retry_delay)

    if not backend_running:
        pytest.fail(f"\\n\\n❌ Backend NOT running at {api_base_url}")

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
        pytest.fail(f"\\n\\n❌ Frontend NOT running at {base_url}")

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
        print(f"\\nScreenshot: {filename}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to make test result available to fixtures"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
'''
}

# Write all files
print("Creating Selenium test suite structure...")
for filepath, content in FILES.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Created: {filepath}")

print("\\n✅ Selenium test suite structure created successfully!")
print("\\nNext steps:")
print("1. Review and customize page locators in e2e_tests/pages/")
print("2. Update test_users.py with your actual test user credentials")
print("3. Run: pytest e2e_tests/ -v")
