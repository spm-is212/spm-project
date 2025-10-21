#!/bin/bash
#
# Automated Regression Test Runner
# Runs comprehensive E2E tests for SPM Project
#

set -e  # Exit on error

PROJECT_DIR="/Users/estrella/Library/CloudStorage/OneDrive-SingaporeManagementUniversity/Y3S1/IS212 SPM G10/proj/spm-project"

echo "========================================="
echo "SPM Project - Regression Test Suite"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if server is running
check_server() {
    local url=$1
    local name=$2

    if curl -s --max-time 2 "$url" > /dev/null; then
        echo -e "${GREEN}✓${NC} $name is running at $url"
        return 0
    else
        echo -e "${RED}✗${NC} $name is NOT running at $url"
        return 1
    fi
}

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check backend
if ! check_server "http://localhost:8000/api/health" "Backend"; then
    echo -e "${YELLOW}Please start the backend server:${NC}"
    echo "  cd $PROJECT_DIR"
    echo "  uvicorn backend.main:app --reload --port 8000"
    echo ""
    exit 1
fi

# Check frontend
if ! check_server "http://localhost:5173" "Frontend"; then
    echo -e "${YELLOW}Please start the frontend server:${NC}"
    echo "  cd $PROJECT_DIR/frontend/all-in-one"
    echo "  npm run dev"
    echo ""
    exit 1
fi

echo ""
echo "All servers are running!"
echo ""

# Create screenshots directory
mkdir -p screenshots

# Parse arguments
TEST_SUITE=${1:-"all"}
HEADLESS=${2:-"false"}

# Build pytest command
PYTEST_CMD="pytest e2e_tests/"

case "$TEST_SUITE" in
    "smoke")
        echo "Running SMOKE tests only..."
        PYTEST_CMD="$PYTEST_CMD -m smoke"
        ;;
    "regression")
        echo "Running FULL REGRESSION suite..."
        PYTEST_CMD="$PYTEST_CMD -m regression"
        ;;
    "auth")
        echo "Running AUTHENTICATION tests..."
        PYTEST_CMD="$PYTEST_CMD test_auth_flow.py"
        ;;
    "all")
        echo "Running ALL E2E tests..."
        ;;
    *)
        echo "Unknown test suite: $TEST_SUITE"
        echo "Usage: ./run_regression_tests.sh [smoke|regression|auth|all] [headless]"
        exit 1
        ;;
esac

# Add common options
PYTEST_CMD="$PYTEST_CMD -v --tb=short"

# Add HTML report
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PYTEST_CMD="$PYTEST_CMD --html=reports/test_report_${TIMESTAMP}.html --self-contained-html"

# Create reports directory
mkdir -p reports

echo "Executing: $PYTEST_CMD"
echo ""
echo "========================================="
echo ""

# Run tests
cd "$PROJECT_DIR"
if eval "$PYTEST_CMD"; then
    echo ""
    echo "========================================="
    echo -e "${GREEN}✓ All tests PASSED!${NC}"
    echo "========================================="
    echo ""
    echo "Report: reports/test_report_${TIMESTAMP}.html"
    exit 0
else
    echo ""
    echo "========================================="
    echo -e "${RED}✗ Some tests FAILED!${NC}"
    echo "========================================="
    echo ""
    echo "Report: reports/test_report_${TIMESTAMP}.html"
    echo "Screenshots: screenshots/"
    exit 1
fi
