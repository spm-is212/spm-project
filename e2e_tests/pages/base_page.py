"""
Base Page Object - Shared methods for all pages
"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time


class BasePage:
    """Base class for all page objects with common utilities"""

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def navigate_to(self, path=""):
        """Navigate to a specific path"""
        url = f"{self.base_url}{path}"
        self.driver.get(url)

    def find_element(self, locator, timeout=10):
        """Find element with explicit wait"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def find_elements(self, locator, timeout=10):
        """Find multiple elements with explicit wait"""
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return self.driver.find_elements(*locator)

    def click(self, locator, timeout=10):
        """Click element with explicit wait"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()

    def send_keys(self, locator, text, timeout=10):
        """Send keys to element with explicit wait"""
        element = self.find_element(locator, timeout)
        element.clear()
        element.send_keys(text)

    def get_text(self, locator, timeout=10):
        """Get text from element"""
        element = self.find_element(locator, timeout)
        return element.text

    def is_element_visible(self, locator, timeout=5):
        """Check if element is visible"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def is_element_present(self, locator, timeout=5):
        """Check if element is present in DOM"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def wait_for_url_to_contain(self, text, timeout=10):
        """Wait for URL to contain specific text"""
        WebDriverWait(self.driver, timeout).until(
            EC.url_contains(text)
        )

    def wait_for_element_to_disappear(self, locator, timeout=10):
        """Wait for element to disappear"""
        WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(locator)
        )

    def get_current_url(self):
        """Get current page URL"""
        return self.driver.current_url

    def refresh_page(self):
        """Refresh current page"""
        self.driver.refresh()

    def take_screenshot(self, filename):
        """Take screenshot for debugging"""
        self.driver.save_screenshot(filename)

    def scroll_to_element(self, locator):
        """Scroll to element"""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # Small delay after scroll

    def get_attribute(self, locator, attribute, timeout=10):
        """Get attribute value from element"""
        element = self.find_element(locator, timeout)
        return element.get_attribute(attribute)
