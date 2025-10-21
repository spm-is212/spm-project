# 🎯 Selenium Automated Regression Testing - Complete Setup Guide

## ✅ What Has Been Created

### 1. **Page Object Models** (`e2e_tests/pages/`)
- ✓ `base_page.py` - Base class with common methods
- ✓ `login_page.py` - Enhanced login page interactions
- ✓ `dashboard_page.py` - Dashboard page (template)
- ✓ `task_page.py` - Task management page (template)
- ✓ `project_page.py` - Project management page (template)

### 2. **Test Suites** (`e2e_tests/`)
- ✓ `test_auth_flow.py` - Authentication tests (3 tests)
- ✓ `test_smoke_suite.py` - Critical smoke tests (9 tests)
- ✓ `test_regression_suite.py` - Full regression suite (20+ test templates)
- ✓ `test_task_crud.py` - Task CRUD tests (template)
- ✓ `test_project_management.py` - Project tests (template)

### 3. **Test Infrastructure**
- ✓ `conftest.py` - Pytest configuration with server checks
- ✓ `test_data/test_users.py` - Test user credentials
- ✓ `helpers/test_helpers.py` - Utility functions
- ✓ `run_regression_tests.sh` - Automated test runner script

### 4. **Documentation**
- ✓ `README_E2E_TESTS.md` - Comprehensive testing guide
- ✓ This guide - Setup and usage instructions

---

## 🚀 Quick Start (5 Steps)

### Step 1: Install Dependencies
```bash
cd "/Users/estrella/Library/CloudStorage/OneDrive-SingaporeManagementUniversity/Y3S1/IS212 SPM G10/proj/spm-project"

# Install Python packages
pip install pytest-html pytest-xdist

# Or reinstall all requirements
pip install -r requirements.txt
```

### Step 2: Update Test User Credentials

Edit `e2e_tests/test_data/test_users.py` with your actual test users:
```python
TEST_USERS = {
    "admin": {
        "email": "your-actual-admin@email.com",  # ← Change this
        "password": "your-actual-password",       # ← Change this
        "role": "admin"
    }
}
```

### Step 3: Start Servers

**Terminal 1 - Backend:**
```bash
cd "/Users/estrella/Library/CloudStorage/OneDrive-SingaporeManagementUniversity/Y3S1/IS212 SPM G10/proj/spm-project"
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd "/Users/estrella/Library/CloudStorage/OneDrive-SingaporeManagementUniversity/Y3S1/IS212 SPM G10/proj/spm-project/frontend/all-in-one"
npm run dev
```

### Step 4: Run Smoke Tests First
```bash
cd "/Users/estrella/Library/CloudStorage/OneDrive-SingaporeManagementUniversity/Y3S1/IS212 SPM G10/proj/spm-project"

# Quick smoke tests (should take ~30 seconds)
pytest e2e_tests/test_smoke_suite.py -v
```

### Step 5: Run Full Test Suite
```bash
# Using the test runner script
./run_regression_tests.sh all

# Or using pytest directly
pytest e2e_tests/ -v --html=reports/report.html
```

---

## 📝 Customizing Tests for Your Frontend

### Update Page Locators

Your frontend uses TypeScript/React. You need to update the CSS selectors in page objects to match your actual UI.

**Example: Update Login Page Locators**

1. Open your frontend in browser
2. Right-click on the email input → Inspect Element
3. Note the actual selector (id, class, data-testid, etc.)
4. Update `e2e_tests/pages/login_page.py`:

```python
# Before (generic):
EMAIL_INPUT = (By.CSS_SELECTOR, "input[type='email']")

# After (specific to your app):
EMAIL_INPUT = (By.CSS_SELECTOR, "input[data-testid='email-input']")
# or
EMAIL_INPUT = (By.ID, "email")
# or
EMAIL_INPUT = (By.CSS_SELECTOR, ".login-form input[name='email']")
```

**Recommended: Add data-testid to Your React Components**

In your React components, add `data-testid` attributes:
```tsx
<input
  data-testid="email-input"
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
/>

<button data-testid="login-button" type="submit">
  Login
</button>
```

Then use in tests:
```python
EMAIL_INPUT = (By.CSS_SELECTOR, "[data-testid='email-input']")
LOGIN_BUTTON = (By.CSS_SELECTOR, "[data-testid='login-button']")
```

---

## 🎯 Running Different Test Suites

### Smoke Tests (Quick - ~1 minute)
```bash
# Critical paths only
./run_regression_tests.sh smoke

# Or
pytest e2e_tests/ -m smoke -v
```

### Regression Tests (Full - ~5-10 minutes)
```bash
# Complete regression suite
./run_regression_tests.sh regression

# Or
pytest e2e_tests/ -m regression -v
```

### Specific Test Categories
```bash
# Authentication tests only
pytest e2e_tests/test_auth_flow.py -v

# Smoke tests only
pytest e2e_tests/test_smoke_suite.py -v

# Single test
pytest e2e_tests/test_auth_flow.py::TestAuthenticationFlow::test_successful_login -v
```

### Parallel Execution (Faster)
```bash
# Run tests in parallel using 4 workers
pytest e2e_tests/ -n 4 -v
```

---

## 📊 Test Reports

### HTML Reports
```bash
# Generate HTML report
pytest e2e_tests/ -v --html=reports/report.html --self-contained-html

# Open report
open reports/report.html
```

### Coverage + E2E Combined
```bash
# Backend unit tests with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Then run E2E tests
pytest e2e_tests/ -v --html=reports/e2e_report.html
```

---

## 🐛 Troubleshooting

### Issue: "Element not found" errors
**Solution:**
1. Open your app in browser
2. Inspect the actual elements
3. Update locators in page objects to match
4. Use more specific selectors (data-testid recommended)

### Issue: Tests time out
**Solution:**
1. Increase wait times in `conftest.py`:
   ```python
   driver.implicitly_wait(15)  # Increase from 10
   ```
2. Check if your app takes longer to load
3. Use explicit waits for specific elements

### Issue: "Server not running" error
**Solution:**
1. Make sure both frontend and backend are running
2. Check URLs in `conftest.py` match your setup
3. Test manually: `curl http://localhost:8000/api/health`

### Issue: ChromeDriver errors
**Solution:**
```bash
# Update webdriver-manager
pip install --upgrade webdriver-manager

# Clear cache
rm -rf ~/.wdm
```

---

## 📋 Test Development Workflow

### Adding New Tests

1. **Create Page Object** (if needed)
   ```python
   # e2e_tests/pages/new_page.py
   from e2e_tests.pages.base_page import BasePage
   from selenium.webdriver.common.by import By

   class NewPage(BasePage):
       SOME_BUTTON = (By.CSS_SELECTOR, "[data-testid='some-btn']")

       def click_button(self):
           self.click(self.SOME_BUTTON)
   ```

2. **Write Test**
   ```python
   # e2e_tests/test_new_feature.py
   import pytest
   from e2e_tests.pages.new_page import NewPage

   @pytest.mark.regression
   def test_new_feature(driver, base_url):
       page = NewPage(driver, base_url)
       page.navigate()
       page.click_button()
       assert True
   ```

3. **Run Test**
   ```bash
   pytest e2e_tests/test_new_feature.py -v
   ```

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/e2e-tests.yml`:
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Start Backend
        run: |
          cd backend
          uvicorn main:app --port 8000 &
          sleep 5

      - name: Start Frontend
        run: |
          cd frontend/all-in-one
          npm install
          npm run dev &
          sleep 10

      - name: Run E2E Tests
        run: pytest e2e_tests/ -v --html=report.html --self-contained-html

      - name: Upload Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-report
          path: report.html
```

---

## 📈 Current Test Coverage

### Implemented Tests (Ready to Run)
- ✅ **Smoke Tests**: 9 tests
  - Homepage loads
  - Login page accessible
  - Admin login
  - Invalid login prevented
  - API health check
  - Responsive design (3 viewports)
  - Session persistence
  - Page load performance
  - Login performance

- ✅ **Authentication Tests**: 3 tests
  - Successful login
  - Invalid credentials
  - Logout

### Template Tests (Need Customization)
- ⚠️ **Regression Suite**: 20+ test templates
- ⚠️ **Task CRUD**: Templates provided
- ⚠️ **Project Management**: Templates provided

**These templates need:**
1. Frontend locators updated
2. Test data adjusted
3. Assertions customized

---

## 🎓 Best Practices

1. ✅ **Use Page Object Model** - Keep UI interactions in page objects
2. ✅ **Use data-testid** - Add to React components for stable selectors
3. ✅ **Independent Tests** - Each test should work standalone
4. ✅ **Explicit Waits** - Avoid `time.sleep()`, use `WebDriverWait`
5. ✅ **Unique Test Data** - Use timestamps/UUIDs for test data
6. ✅ **Clean Up** - Delete test data after tests
7. ✅ **Screenshots on Failure** - Already configured automatically
8. ✅ **Descriptive Names** - Test names should describe what they test

---

## 📞 Next Steps

1. ✅ **Install dependencies**: `pip install -r requirements.txt`
2. ✅ **Update test users** in `e2e_tests/test_data/test_users.py`
3. ✅ **Start servers** (backend + frontend)
4. ✅ **Run smoke tests**: `pytest e2e_tests/test_smoke_suite.py -v`
5. ⚠️ **Update page locators** to match your actual frontend
6. ⚠️ **Customize regression tests** as needed
7. ✅ **Add to CI/CD pipeline**

---

## 📚 Resources

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Page Object Model](https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/)
- [WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager)

---

**Created with ❤️ for SPM Project**
**Ready for automated regression testing!**
