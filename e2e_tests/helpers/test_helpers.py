"""
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
