"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
import os

# Add MarkX to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'MarkX'))


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "test_mode": True,
        "log_level": "DEBUG",
        "api_key": "test_key_12345"
    }


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("DMITRY_MODEL", "test-model")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
