# Testing Guide

Comprehensive guide to testing Dmitry.

---

## Test Philosophy

- **Fast feedback** - Tests should run quickly
- **Reliable** - Tests should not be flaky
- **Isolated** - Tests should not depend on each other
- **Comprehensive** - Cover happy paths and edge cases

---

## Test Structure

```
MarkX/tests/
├── unit/                    # Fast, isolated tests
│   ├── test_call_ledger.py
│   ├── test_action_safety.py
│   ├── test_input_sanitizer.py
│   ├── test_output_validator.py
│   ├── test_evidence_chain.py
│   └── test_structured_actions.py
├── integration/             # Tests with dependencies
│   ├── test_platform_client.py
│   ├── test_server_endpoints.py
│   └── test_service_registry.py
├── fixtures/                # Test data and mocks
│   ├── mock_platform.py
│   ├── sample_requests.py
│   └── sample_responses.py
└── conftest.py             # Pytest configuration
```

---

## Running Tests

### All Tests

```bash
pytest
```

### Specific Test File

```bash
pytest MarkX/tests/unit/test_call_ledger.py
```

### Specific Test Function

```bash
pytest MarkX/tests/unit/test_call_ledger.py::test_record_call
```

### With Coverage

```bash
pytest --cov=MarkX --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # Mac
start htmlcov/index.html # Windows
```

### Verbose Output

```bash
pytest -v
```

### Stop on First Failure

```bash
pytest -x
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Only Integration Tests

```bash
pytest -m integration
```

---

## Writing Tests

### Unit Test Example

```python
# MarkX/tests/unit/test_call_ledger.py
import pytest
from core.call_ledger import CallLedger, get_call_ledger

def test_record_call():
    """Test recording a Platform call."""
    ledger = CallLedger()
    
    call_id = ledger.record_call(
        request_id="test-req-1",
        endpoint="get_risk_findings",
        args={"entity_id": "db-1"},
        response={"findings": []},
        status="success"
    )
    
    assert call_id is not None
    assert len(call_id) == 36  # UUID format
    
    # Verify record exists
    records = ledger.get_records_for_request("test-req-1")
    assert len(records) == 1
    assert records[0].endpoint == "get_risk_findings"
    assert records[0].response_status == "success"

def test_get_verified_citations():
    """Test getting verified citations from ledger."""
    ledger = CallLedger()
    request_id = "test-req-2"
    
    # Record some calls
    ledger.record_call(
        request_id=request_id,
        endpoint="get_risk_findings",
        args={},
        response={"findings": []},
        status="success"
    )
    
    # Get citations
    from core.call_ledger import get_verified_citations
    citations = get_verified_citations(request_id)
    
    assert len(citations) == 1
    assert citations[0]["endpoint"] == "get_risk_findings"
    assert "call_id" in citations[0]
    assert "args_hash" in citations[0]
    assert "response_hash" in citations[0]

def test_immutable_ledger():
    """Test that ledger records cannot be modified."""
    ledger = CallLedger()
    
    call_id = ledger.record_call(
        request_id="test-req-3",
        endpoint="test_endpoint",
        args={"key": "value"},
        response={"result": "ok"},
        status="success"
    )
    
    # Try to modify (should not affect ledger)
    records = ledger.get_records_for_request("test-req-3")
    original_hash = records[0].args_hash
    
    # Verify hash hasn't changed
    records_again = ledger.get_records_for_request("test-req-3")
    assert records_again[0].args_hash == original_hash
```

### Integration Test Example

```python
# MarkX/tests/integration/test_server_endpoints.py
import pytest
import requests
import time

@pytest.fixture(scope="module")
def server_url():
    """Server URL for testing."""
    return "http://127.0.0.1:8765"

def test_health_endpoint(server_url):
    """Test /health endpoint returns ServiceHealth model."""
    response = requests.get(f"{server_url}/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify ServiceHealth schema
    assert "service" in data
    assert "status" in data
    assert "version" in data
    assert "uptime_seconds" in data
    assert "checks" in data
    assert "timestamp" in data
    
    # Verify values
    assert data["service"] == "dmitry"
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert isinstance(data["uptime_seconds"], (int, float))
    assert isinstance(data["checks"], dict)

def test_ready_endpoint(server_url):
    """Test /ready endpoint for K8s readiness."""
    response = requests.get(f"{server_url}/ready")
    
    data = response.json()
    
    # Verify schema
    assert "ready" in data
    assert "dependencies" in data
    
    # Verify status code matches ready state
    if data["ready"]:
        assert response.status_code == 200
    else:
        assert response.status_code == 503

def test_advise_endpoint(server_url):
    """Test /advise endpoint with AdviseRequest."""
    request = {
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
    
    response = requests.post(
        f"{server_url}/advise",
        json=request,
        timeout=30
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify AdviseResponse schema
    required_fields = [
        "summary",
        "risk_factors",
        "impact_analysis",
        "recommended_actions",
        "evidence_chain",
        "confidence",
        "citations",
        "processing_time_ms"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    # Verify types
    assert isinstance(data["summary"], str)
    assert isinstance(data["risk_factors"], list)
    assert isinstance(data["recommended_actions"], list)
    assert isinstance(data["confidence"], (int, float))
    assert 0.0 <= data["confidence"] <= 1.0
```

### Fixture Example

```python
# MarkX/tests/fixtures/mock_platform.py
from unittest.mock import Mock

class MockPlatformClient:
    """Mock Platform client for testing."""
    
    def __init__(self):
        self.calls = []
    
    def call(self, endpoint: str, **kwargs):
        """Mock Platform call."""
        self.calls.append({"endpoint": endpoint, "kwargs": kwargs})
        
        # Return mock responses
        if endpoint == "get_risk_findings":
            return {
                "findings": [
                    {
                        "id": "find-1",
                        "entity_id": kwargs.get("entity_id"),
                        "risk_score": 85,
                        "severity": "high"
                    }
                ]
            }
        elif endpoint == "get_finding_details":
            return {
                "finding": {
                    "id": kwargs.get("finding_id"),
                    "description": "Test finding",
                    "risk_score": 85
                }
            }
        
        return {}
    
    def is_connected(self) -> bool:
        """Mock connection check."""
        return True

# MarkX/tests/conftest.py
import pytest
from tests.fixtures.mock_platform import MockPlatformClient

@pytest.fixture
def mock_platform():
    """Provide mock Platform client."""
    return MockPlatformClient()

@pytest.fixture
def sample_advise_request():
    """Provide sample AdviseRequest."""
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
        "evidence_refs": ["evt-456"],
        "policy_context": {}
    }
```

---

## Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_unit_example():
    """Fast, isolated test."""
    pass

@pytest.mark.integration
def test_integration_example():
    """Test with dependencies."""
    pass

@pytest.mark.slow
def test_slow_example():
    """Long-running test."""
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    """Test for future feature."""
    pass
```

Run specific markers:
```bash
pytest -m unit        # Only unit tests
pytest -m integration # Only integration tests
pytest -m "not slow"  # Skip slow tests
```

---

## Mocking

### Mock External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test with mocked dependency."""
    mock_client = Mock()
    mock_client.call.return_value = {"result": "success"}
    
    # Use mock in test
    result = mock_client.call("endpoint", param="value")
    
    assert result["result"] == "success"
    mock_client.call.assert_called_once_with("endpoint", param="value")

@patch('tools.platform.platform_client.requests.post')
def test_with_patch(mock_post):
    """Test with patched requests."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"data": "test"}
    
    # Test code that uses requests.post
    # ...
    
    assert mock_post.called
```

---

## Test Coverage

### View Coverage

```bash
# Generate coverage report
pytest --cov=MarkX --cov-report=html

# Open report
open htmlcov/index.html
```

### Coverage Goals

- **Overall:** 80%+
- **Core components:** 90%+
- **Critical paths:** 100%

### Exclude from Coverage

```python
# .coveragerc
[run]
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*
    */.venv/*
```

---

## Continuous Integration

Tests run automatically on:
- Every push
- Every pull request
- Scheduled (daily)

See `.github/workflows/ci-cd.yml` for configuration.

---

## Performance Testing

### Benchmark Example

```python
import time

def test_performance_call_ledger():
    """Test call ledger performance."""
    ledger = CallLedger()
    
    start = time.time()
    
    # Record 1000 calls
    for i in range(1000):
        ledger.record_call(
            request_id=f"req-{i}",
            endpoint="test",
            args={},
            response={},
            status="success"
        )
    
    elapsed = time.time() - start
    
    # Should complete in under 1 second
    assert elapsed < 1.0
    
    # Should handle 1000+ calls/second
    calls_per_second = 1000 / elapsed
    assert calls_per_second > 1000
```

---

## Debugging Tests

### Run with Debugger

```bash
# Run with pdb
pytest --pdb

# Drop into debugger on failure
pytest --pdb --maxfail=1
```

### Print Debug Info

```python
def test_with_debug():
    """Test with debug output."""
    result = some_function()
    
    # Print for debugging
    print(f"Result: {result}")
    
    assert result == expected
```

Run with output:
```bash
pytest -s  # Show print statements
```

---

## Best Practices

### DO

- ✅ Write tests first (TDD)
- ✅ Test one thing per test
- ✅ Use descriptive test names
- ✅ Test edge cases
- ✅ Mock external dependencies
- ✅ Keep tests fast
- ✅ Use fixtures for setup
- ✅ Assert specific values

### DON'T

- ❌ Test implementation details
- ❌ Write flaky tests
- ❌ Skip error cases
- ❌ Use sleep() for timing
- ❌ Test multiple things in one test
- ❌ Depend on test order
- ❌ Leave commented-out tests

---

## Common Patterns

### Testing Exceptions

```python
def test_raises_exception():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError, match="Invalid input"):
        some_function(invalid_input)
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result == expected
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test", "TEST"),
    ("hello", "HELLO"),
    ("", ""),
])
def test_uppercase(input, expected):
    """Test uppercase conversion."""
    assert input.upper() == expected
```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

---

**Write tests. Sleep better. 🧪**
