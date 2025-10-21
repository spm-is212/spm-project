import pytest
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


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
    """
    Check if frontend and backend servers are running.
    Fails with helpful message if servers aren't started.
    """
    max_retries = 3
    retry_delay = 2

    # Check backend
    backend_running = False
    for i in range(max_retries):
        try:
            response = requests.get(f"{api_base_url}/api/health", timeout=2)
            if response.status_code == 200:
                backend_running = True
                print(f"\n✓ Backend server is running at {api_base_url}")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(retry_delay)

    if not backend_running:
        pytest.fail(
            f"\n\n❌ Backend server is NOT running at {api_base_url}\n"
            f"Please start the backend in a separate terminal:\n"
            f"  cd backend && uvicorn main:app --reload --port 8000\n"
        )

    # Check frontend
    frontend_running = False
    for i in range(max_retries):
        try:
            response = requests.get(base_url, timeout=2)
            if response.status_code in [200, 304]:
                frontend_running = True
                print(f"✓ Frontend server is running at {base_url}")
                break
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(retry_delay)

    if not frontend_running:
        pytest.fail(
            f"\n\n❌ Frontend server is NOT running at {base_url}\n"
            f"Please start the frontend in a separate terminal:\n"
            f"  cd frontend/all-in-one && npm run dev\n"
        )

    yield

    print("\n✓ Server checks passed")


@pytest.fixture(scope="function")
def driver():
    """Setup Chrome WebDriver"""
    options = Options()
    # Headless mode for CI/CD
    # options.add_argument("--headless")
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
