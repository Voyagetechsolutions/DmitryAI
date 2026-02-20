# conftest.py - Pytest configuration and fixtures

import pytest
import sys
from pathlib import Path

# Add MarkX to path
markx_path = Path(__file__).parent.parent
sys.path.insert(0, str(markx_path))


@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return {
        "event_id": "evt-test-123",
        "finding_id": "find-test-456",
        "entity_id": "customer-db",
        "entity_type": "database",
        "risk_score": 85.0,
        "severity": "high"
    }


@pytest.fixture
def sample_advise_request():
    """Sample AdviseRequest for testing."""
    return {
        "finding_id": "find-test-123",
        "tenant_id": "tenant-1",
        "entity": {
            "type": "database",
            "id": "customer-db",
            "name": "Customer Database",
            "attributes": {}
        },
        "severity": "high",
        "risk_score": 85.0,
        "exposure_paths": [],
        "evidence_refs": ["evt-456", "find-test-123"],
        "policy_context": {}
    }


@pytest.fixture
def sample_platform_response():
    """Sample Platform API response."""
    return {
        "findings": [
            {
                "id": "find-1",
                "entity_id": "customer-db",
                "risk_score": 85,
                "severity": "high",
                "description": "High risk detected"
            }
        ]
    }


@pytest.fixture
def mock_platform_client():
    """Mock Platform client for testing."""
    from unittest.mock import Mock
    
    client = Mock()
    client.call.return_value = {
        "findings": [{"id": "find-1", "risk_score": 85}]
    }
    client.is_connected.return_value = True
    
    return client
