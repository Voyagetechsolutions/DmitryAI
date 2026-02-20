# Contributing to Dmitry

Thank you for your interest in contributing! This guide will help you get started.

---

## Code of Conduct

Be respectful, constructive, and professional. We're building production-grade software together.

---

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/Mark-X.git
cd Mark-X
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r MarkX/requirements_production.txt
pip install -r requirements-dev.txt  # Dev tools
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest MarkX/tests/

# Run specific test file
pytest MarkX/tests/unit/test_call_ledger.py

# Run with coverage
pytest --cov=MarkX --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format MarkX/

# Lint code
ruff check MarkX/

# Type checking
mypy MarkX/

# Run all checks
./scripts/check.sh  # If available
```

### Running Dmitry Locally

```bash
cd MarkX
python main.py

# Server starts on http://127.0.0.1:8765
```

---

## Contribution Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Keep functions small and focused
- Use meaningful variable names

**Example:**
```python
def calculate_confidence(
    evidence_count: int,
    success_rate: float
) -> float:
    """
    Calculate confidence score based on evidence.
    
    Args:
        evidence_count: Number of evidence pieces
        success_rate: Success rate of Platform calls (0.0-1.0)
    
    Returns:
        Confidence score (0.0-1.0)
    """
    base_confidence = 0.5
    evidence_boost = min(0.2, evidence_count * 0.05)
    success_boost = success_rate * 0.2
    return min(base_confidence + evidence_boost + success_boost, 1.0)
```

### Testing Requirements

- All new features must have tests
- Maintain or improve test coverage
- Tests must pass before merging

**Test Structure:**
```
MarkX/tests/
├── unit/           # Unit tests (fast, isolated)
├── integration/    # Integration tests (slower, with dependencies)
└── fixtures/       # Test fixtures and mocks
```

### Commit Messages

Use conventional commits:

```
feat: add Redis caching for Platform responses
fix: correct evidence chain validation logic
docs: update API documentation
test: add unit tests for action safety gate
refactor: simplify input sanitizer logic
chore: update dependencies
```

### Pull Request Process

1. **Update tests** - Add/update tests for your changes
2. **Update docs** - Update relevant documentation
3. **Run checks** - Ensure all tests and linters pass
4. **Write description** - Explain what and why
5. **Link issues** - Reference related issues

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

---

## Areas for Contribution

### High Priority

1. **Unit Tests** - Expand test coverage
   - `MarkX/core/` components need more unit tests
   - Target: 90%+ coverage

2. **Integration Tests** - Test component interactions
   - Platform client integration
   - Server endpoint integration

3. **Documentation** - Improve guides
   - More examples
   - Troubleshooting guides
   - Architecture deep-dives

### Medium Priority

4. **Observability** - Add OpenTelemetry tracing
   - Distributed tracing
   - Metrics collection
   - Log aggregation

5. **Performance** - Optimize hot paths
   - Caching strategies
   - Connection pooling improvements
   - Response time optimization

6. **Security** - Enhance security features
   - Rate limiting improvements
   - Additional input validation
   - Security scanning integration

### Nice to Have

7. **Developer Experience** - Improve DX
   - Better error messages
   - Development tools
   - Debugging utilities

8. **Examples** - Add example integrations
   - Sample Platform implementations
   - Integration patterns
   - Use case examples

---

## Project Structure

```
Mark-X/
├── MarkX/                      # Main package
│   ├── agent/                  # Agent server
│   │   ├── server.py          # HTTP server
│   │   └── auth.py            # Authentication
│   ├── core/                   # Core components
│   │   ├── call_ledger.py     # Audit trail
│   │   ├── action_safety.py   # Action validation
│   │   ├── input_sanitizer.py # Input sanitation
│   │   ├── output_validator.py# Output validation
│   │   ├── evidence_chain.py  # Evidence tracking
│   │   └── structured_actions.py # Action parsing
│   ├── tools/                  # Tool integrations
│   │   └── platform/          # Platform integration
│   ├── shared/                 # Shared contracts
│   │   ├── contracts/         # Pydantic models
│   │   └── registry.py        # Service registry
│   └── tests/                  # Test suite
│       ├── unit/              # Unit tests
│       ├── integration/       # Integration tests
│       └── fixtures/          # Test fixtures
├── docs/                       # Documentation
│   ├── guides/                # User guides
│   ├── architecture/          # Architecture docs
│   └── archive/               # Historical docs
├── README.md                   # Project overview
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # This file
└── LICENSE                    # License file
```

---

## Development Tips

### Debugging

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use breakpoints
import pdb; pdb.set_trace()
```

### Testing Specific Components

```bash
# Test call ledger only
pytest MarkX/tests/unit/test_call_ledger.py -v

# Test with specific marker
pytest -m "unit" -v

# Test and stop on first failure
pytest -x
```

### Local Platform Mock

For testing without Platform:

```python
# MarkX/tests/mocks/platform_mock.py
class MockPlatformClient:
    def get_risk_findings(self, **kwargs):
        return {"findings": [{"id": "test-1", "risk_score": 85}]}
```

---

## Questions?

- **Issues:** [GitHub Issues](https://github.com/yourusername/Mark-X/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/Mark-X/discussions)
- **Email:** maintainers@example.com

---

## Recognition

Contributors will be recognized in:
- README.md acknowledgments
- Release notes
- Project documentation

Thank you for contributing to Dmitry! 🚀
