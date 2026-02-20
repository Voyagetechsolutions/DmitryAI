# Development Guide

Guide for local development and contributing to Dmitry.

---

## Prerequisites

- Python 3.9+
- Git
- Virtual environment tool (venv, virtualenv, or conda)
- Code editor (VS Code, PyCharm, etc.)

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/Mark-X.git
cd Mark-X
```

### 2. Create Virtual Environment

```bash
# Using venv (recommended)
python -m venv .venv

# Activate
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
# Production dependencies
pip install -r MarkX/requirements_production.txt

# Development dependencies
pip install -r requirements-dev.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your settings
nano .env
```

**Required variables:**
```bash
OPENAI_API_KEY=sk-...
PLATFORM_URL=http://localhost:8000  # Optional
DMITRY_PORT=8765
LOG_LEVEL=DEBUG
```

---

## Running Dmitry

### Start Server

```bash
cd MarkX
python main.py
```

**Expected output:**
```
✓ Agent API server started on http://127.0.0.1:8765
✓ Registered with Platform, heartbeat started
```

### Test Endpoints

```bash
# Health check
curl http://127.0.0.1:8765/health

# Status
curl http://127.0.0.1:8765/status

# Chat (requires LLM configured)
curl -X POST http://127.0.0.1:8765/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "context": {}}'
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code in `MarkX/` directory:
- `agent/` - Server and API
- `core/` - Core components
- `tools/` - Tool integrations
- `shared/` - Shared contracts

### 3. Run Tests

```bash
# Run all tests
pytest MarkX/tests/

# Run specific test
pytest MarkX/tests/unit/test_call_ledger.py

# Run with coverage
pytest --cov=MarkX --cov-report=html
```

### 4. Check Code Quality

```bash
# Format code
ruff format MarkX/

# Lint
ruff check MarkX/

# Type check
mypy MarkX/

# All checks
ruff check MarkX/ && mypy MarkX/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

Use [conventional commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create Pull Request on GitHub.

---

## Testing

### Test Structure

```
MarkX/tests/
├── unit/              # Fast, isolated tests
│   ├── test_call_ledger.py
│   ├── test_action_safety.py
│   └── ...
├── integration/       # Tests with dependencies
│   ├── test_platform_client.py
│   ├── test_server_endpoints.py
│   └── ...
└── fixtures/          # Test data and mocks
    ├── mock_platform.py
    └── sample_data.py
```

### Writing Tests

**Unit test example:**
```python
# MarkX/tests/unit/test_call_ledger.py
import pytest
from core.call_ledger import CallLedger

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
    assert len(ledger.get_records_for_request("test-req-1")) == 1
```

**Integration test example:**
```python
# MarkX/tests/integration/test_server_endpoints.py
import pytest
import requests

def test_health_endpoint():
    """Test /health endpoint returns correct format."""
    response = requests.get("http://127.0.0.1:8765/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "checks" in data
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest MarkX/tests/unit/test_call_ledger.py

# Specific test function
pytest MarkX/tests/unit/test_call_ledger.py::test_record_call

# With coverage
pytest --cov=MarkX --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

---

## Debugging

### Using Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()
```

### Debug Logging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set in .env
LOG_LEVEL=DEBUG
```

### VS Code Debug Configuration

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Dmitry Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/MarkX/main.py",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "LOG_LEVEL": "DEBUG"
      }
    },
    {
      "name": "Python: Current Test",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Code Style

### Python Style Guide

Follow PEP 8 with these specifics:

**Imports:**
```python
# Standard library
import json
import time
from datetime import datetime

# Third-party
import requests
from pydantic import BaseModel

# Local
from core.call_ledger import CallLedger
from tools.platform.platform_client import get_platform_client
```

**Type Hints:**
```python
def process_request(
    request_id: str,
    context: dict,
    timeout: float = 30.0
) -> dict:
    """Process request with context."""
    ...
```

**Docstrings:**
```python
def calculate_confidence(evidence_count: int) -> float:
    """
    Calculate confidence score based on evidence.
    
    Args:
        evidence_count: Number of evidence pieces
    
    Returns:
        Confidence score between 0.0 and 1.0
    
    Raises:
        ValueError: If evidence_count is negative
    """
    if evidence_count < 0:
        raise ValueError("Evidence count cannot be negative")
    
    return min(0.5 + (evidence_count * 0.1), 1.0)
```

### Formatting Tools

```bash
# Format with ruff
ruff format MarkX/

# Check formatting
ruff check MarkX/

# Auto-fix issues
ruff check --fix MarkX/
```

---

## Project Structure

```
Mark-X/
├── MarkX/                    # Main package
│   ├── agent/               # Agent server
│   │   ├── server.py       # HTTP server
│   │   └── auth.py         # Authentication
│   ├── core/                # Core components
│   │   ├── call_ledger.py  # Audit trail
│   │   ├── action_safety.py# Action validation
│   │   └── ...
│   ├── tools/               # Tool integrations
│   │   └── platform/       # Platform integration
│   ├── shared/              # Shared contracts
│   │   ├── contracts/      # Pydantic models
│   │   └── registry.py     # Service registry
│   ├── tests/               # Test suite
│   │   ├── unit/           # Unit tests
│   │   ├── integration/    # Integration tests
│   │   └── fixtures/       # Test fixtures
│   ├── main.py              # Entry point
│   └── requirements_production.txt
├── docs/                    # Documentation
├── .env                     # Environment config (not in git)
├── .gitignore              # Git ignore rules
├── README.md               # Project overview
├── CHANGELOG.md            # Version history
└── CONTRIBUTING.md         # Contribution guide
```

---

## Common Tasks

### Add New Endpoint

1. Add handler in `MarkX/agent/server.py`:
```python
def _handle_new_endpoint(self):
    """Handle new endpoint."""
    data = self._read_json()
    # Process request
    self._send_json({"result": "success"})
```

2. Register in `do_POST` or `do_GET`:
```python
elif path == "/new-endpoint":
    self._handle_new_endpoint()
```

3. Add tests:
```python
def test_new_endpoint():
    response = requests.post(
        "http://127.0.0.1:8765/new-endpoint",
        json={"param": "value"}
    )
    assert response.status_code == 200
```

### Add New Core Component

1. Create file in `MarkX/core/`:
```python
# MarkX/core/new_component.py
class NewComponent:
    """Description of component."""
    
    def process(self, data: dict) -> dict:
        """Process data."""
        return {"processed": True}
```

2. Add tests:
```python
# MarkX/tests/unit/test_new_component.py
def test_new_component():
    component = NewComponent()
    result = component.process({"input": "data"})
    assert result["processed"] is True
```

3. Integrate in server or other components

### Add New Platform Tool

1. Add to `MarkX/tools/platform/platform_tools.py`:
```python
def new_tool(client: PlatformClient, **kwargs) -> dict:
    """
    New Platform tool.
    
    Args:
        param1: Description
    
    Returns:
        Tool result
    """
    return client.call("new_endpoint", **kwargs)
```

2. Register tool in tool list

3. Add tests

---

## Tips and Best Practices

### Performance

- Use connection pooling for external calls
- Cache expensive computations
- Profile hot paths with `cProfile`
- Monitor memory usage

### Security

- Never log secrets or PII
- Validate all inputs
- Use parameterized queries
- Keep dependencies updated

### Testing

- Write tests first (TDD)
- Test edge cases
- Mock external dependencies
- Aim for 80%+ coverage

### Documentation

- Update docs with code changes
- Add docstrings to public functions
- Include examples in docs
- Keep README up to date

---

## Getting Help

- **Code Questions:** [GitHub Discussions](https://github.com/yourusername/Mark-X/discussions)
- **Bug Reports:** [GitHub Issues](https://github.com/yourusername/Mark-X/issues)
- **Contributing:** See [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**Happy coding! 🚀**
