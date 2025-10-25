# E2E Automated Regression Testing Suite

Comprehensive Selenium-based automated regression testing for the SPM Project Management System.

## 📁 Structure

```
e2e_tests/
├── pages/                  # Page Object Models
│   ├── base_page.py       # Base page with common methods
│   ├── login_page.py      # Login page interactions
│   ├── dashboard_page.py  # Dashboard interactions
│   ├── task_page.py       # Task management page
│   └── project_page.py    # Project management page
├── test_data/              # Test data and fixtures
│   └── test_users.py      # Test user credentials
├── helpers/                # Helper utilities
│   └── test_helpers.py    # Common test utilities
├── screenshots/            # Auto-generated screenshots on failure
├── reports/                # HTML test reports
├── conftest.py             # Pytest configuration
├── test_auth_flow.py       # Authentication tests
├── test_task_crud.py       # Task CRUD tests
├── test_project_management.py  # Project tests
└── test_regression_suite.py    # Full regression suite
```

## 🚀 Quick Start

### Prerequisites

1. **Python packages installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Backend server running:**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

3. **Frontend server running:**
   ```bash
   cd frontend/all-in-one
   npm run dev
   ```

### Running Tests

**Method 1: Using the test runner script (Recommended)**
```bash
# Run all tests
./run_regression_tests.sh all

# Run smoke tests only (quick sanity checks)
./run_regression_tests.sh smoke

# Run full regression suite
./run_regression_tests.sh regression

# Run authentication tests only
./run_regression_tests.sh auth
```

**Method 2: Using pytest directly**
```bash
# Run all E2E tests
pytest e2e_tests/ -v

# Run specific test file
pytest e2e_tests/test_auth_flow.py -v

# Run tests with specific marker
pytest e2e_tests/ -m smoke -v
pytest e2e_tests/ -m regression -v

# Run with HTML report
pytest e2e_tests/ -v --html=reports/report.html --self-contained-html

# Run in headless mode
pytest e2e_tests/ -v --headless
```

## 📝 Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.smoke` - Quick smoke tests (critical paths)
- `@pytest.mark.regression` - Full regression test suite
- `@pytest.mark.auth` - Authentication-related tests
- `@pytest.mark.task` - Task management tests
- `@pytest.mark.project` - Project management tests

## 🎯 Test Categories

### 1. Authentication Tests (`test_auth_flow.py`)
- ✓ Valid login (admin, manager, staff)
- ✓ Invalid credentials
- ✓ Empty credentials
- ✓ SQL injection prevention
- ✓ Logout functionality

### 2. Task Management Tests (`test_task_crud.py`)
- ✓ Create task
- ✓ Read/view tasks
- ✓ Update task
- ✓ Delete task
- ✓ Task filtering
- ✓ Task search

### 3. Project Management Tests (`test_project_management.py`)
- ✓ Create project
- ✓ View project list
- ✓ Update project
- ✓ Delete project
- ✓ Project collaboration

### 4. Regression Suite (`test_regression_suite.py`)
- ✓ Data persistence
- ✓ Cross-browser compatibility
- ✓ Role-based access control
- ✓ Error handling
- ✓ Performance benchmarks

## 🔧 Configuration

### Update Test Users

Edit `e2e_tests/test_data/test_users.py`:
```python
TEST_USERS = {
    "admin": {
        "email": "your-admin@email.com",
        "password": "your-password"
    }
}
```

### Update Base URLs

Edit `e2e_tests/conftest.py`:
```python
@pytest.fixture(scope="session")
def base_url():
    return "http://localhost:5173"  # Your frontend URL

@pytest.fixture(scope="session")
def api_base_url():
    return "http://localhost:8000"  # Your backend URL
```

### Update Page Locators

Update locators in `e2e_tests/pages/*.py` to match your actual frontend:
```python
# Example: Update login page locators
EMAIL_INPUT = (By.CSS_SELECTOR, "input[data-testid='email']")
PASSWORD_INPUT = (By.CSS_SELECTOR, "input[data-testid='password']")
```

## 📊 Reports

### HTML Reports
After test run, view reports:
```bash
open reports/test_report_YYYYMMDD_HHMMSS.html
```

### Screenshots on Failure
Failed test screenshots are saved to `screenshots/` directory with timestamp.

## 🐛 Debugging

### Run Single Test with Verbose Output
```bash
pytest e2e_tests/test_auth_flow.py::TestAuthenticationFlow::test_successful_login -v -s
```

### Keep Browser Open on Failure
Add to conftest.py:
```python
@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    # Remove driver.quit() to keep browser open
```

### Enable Browser DevTools
```python
options = Options()
options.add_argument("--auto-open-devtools-for-tabs")
```

## 📋 Best Practices

1. **Page Object Model**: Keep page interactions in page objects
2. **Explicit Waits**: Use `WebDriverWait` instead of `time.sleep()`
3. **Unique Test Data**: Generate unique identifiers for test data
4. **Independent Tests**: Each test should be independent
5. **Clean Up**: Tests should clean up created data
6. **Screenshots**: Automatically captured on failure
7. **Readable Assertions**: Use descriptive assertion messages

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Start backend
        run: uvicorn backend.main:app --port 8000 &
      - name: Start frontend
        run: cd frontend/all-in-one && npm install && npm run dev &
      - name: Wait for servers
        run: sleep 10
      - name: Run E2E tests
        run: pytest e2e_tests/ -v --html=report.html
      - name: Upload test report
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-report
          path: report.html
```

## 🆘 Troubleshooting

### Issue: "Connection refused"
**Solution**: Ensure backend and frontend servers are running

### Issue: "Element not found"
**Solution**: Update locators in page objects to match your frontend

### Issue: "TimeoutException"
**Solution**: Increase wait times or check if elements are rendered

### Issue: ChromeDriver version mismatch
**Solution**: Update webdriver-manager: `pip install --upgrade webdriver-manager`

## 📚 Resources

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Page Object Model Pattern](https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/)

## 👥 Contributing

When adding new tests:
1. Follow the Page Object Model pattern
2. Add appropriate pytest markers
3. Include docstrings
4. Update this README if adding new test categories
