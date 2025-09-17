import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Set fake environment variables for testing
os.environ["SUPABASE_URL"] = "https://fake.supabase.co"
os.environ["SUPABASE_KEY"] = "fake_key"

# Mock Supabase create_client globally
with patch("supabase.create_client") as mock_create_client:
    mock_create_client.return_value = Mock()
    from backend.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture"""
    return TestClient(app)
