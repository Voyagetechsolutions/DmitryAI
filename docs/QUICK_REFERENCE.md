# Dmitry - Quick Reference

**One-page reference for common tasks**

---

## Installation

```bash
# Clone and setup
git clone https://github.com/yourusername/Mark-X.git
cd Mark-X
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r MarkX/requirements_production.txt
pip install -r requirements-dev.txt

# Configure
cp .env.example .env
# Edit .env with your settings
```

---

## Running Dmitry

```bash
# Start server
cd MarkX && python main.py

# Server runs on http://127.0.0.1:8765
```

---

## Testing

```bash
# Run all tests
pytest

# Unit tests only
pytest -m unit

# With coverage
pytest --cov=MarkX --cov-report=html

# Specific test
pytest MarkX/tests/unit/test_call_ledger.py -v

# Stop on first failure
pytest -x
```

---

## Code Quality

```bash
# Format code
ruff format MarkX/

# Lint code
ruff check MarkX/

# Auto-fix issues
ruff check --fix MarkX/

# Type check
mypy MarkX/

# Security scan
bandit -r MarkX/

# All checks
ruff check MarkX/ && mypy MarkX/ && bandit -r MarkX/
```

---

## API Endpoints

### Health Checks
```bash
curl http://127.0.0.1:8765/health  # Detailed health
curl http://127.0.0.1:8765/ready   # Readiness probe
curl http://127.0.0.1:8765/live    # Liveness probe
```

### Chat
```bash
curl -X POST http://127.0.0.1:8765/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the risk?", "context": {"entity_id": "db-1"}}'
```

### Advise
```bash
curl -X POST http://127.0.0.1:8765/advise \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "find-456",
    "tenant_id": "tenant-1",
    "entity": {"type": "database", "id": "db-1", "name": "Database 1"},
    "severity": "high",
    "risk_score": 85.0,
    "evidence_refs": ["evt-123"]
  }'
```

---

## Development

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes, add tests

# Run tests
pytest

# Check code quality
ruff check MarkX/ && mypy MarkX/

# Commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/your-feature
```

---

## Docker

```bash
# Build image
docker build -t dmitry:1.2 .

# Run container
docker run -p 8765:8765 \
  -e PLATFORM_URL=http://platform:8000 \
  -e OPENAI_API_KEY=sk-... \
  dmitry:1.2
```

---

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...              # LLM API key
DMITRY_PORT=8765                   # Server port

# Optional
PLATFORM_URL=http://localhost:8000 # Platform URL
LOG_LEVEL=INFO                     # Log level
HEARTBEAT_INTERVAL=10              # Heartbeat interval (seconds)
```

---

## Project Structure

```
Mark-X/
├── README.md              # Start here
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # How to contribute
├── MarkX/
│   ├── agent/            # Server
│   ├── core/             # Core components
│   ├── tools/            # Platform integration
│   ├── shared/           # Contracts
│   └── tests/            # Tests
└── docs/
    ├── guides/           # How-to guides
    └── architecture/     # System design
```

---

## Common Tasks

### Add New Endpoint
1. Add handler in `MarkX/agent/server.py`
2. Register in `do_POST` or `do_GET`
3. Add tests in `MarkX/tests/integration/`

### Add New Core Component
1. Create file in `MarkX/core/`
2. Add tests in `MarkX/tests/unit/`
3. Integrate in server or other components

### Add New Platform Tool
1. Add to `MarkX/tools/platform/platform_tools.py`
2. Add tests
3. Update documentation

---

## Troubleshooting

### Server won't start
```bash
# Check port
netstat -an | grep 8765

# Check logs
tail -f logs/dmitry.log
```

### Tests failing
```bash
# Run with verbose output
pytest -v

# Run specific test
pytest MarkX/tests/unit/test_call_ledger.py -v
```

### Platform connection fails
```bash
# Verify Platform URL
curl http://platform:8000/health

# Check environment
echo $PLATFORM_URL
```

---

## Documentation

- **Quick Start**: `docs/guides/QUICK_START.md`
- **Development**: `docs/guides/DEVELOPMENT.md`
- **Testing**: `docs/guides/TESTING.md`
- **API Reference**: `docs/API.md`
- **Architecture**: `docs/architecture/SYSTEM_ARCHITECTURE.md`

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/Mark-X/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Mark-X/discussions)
- **Documentation**: `docs/`

---

## Version

**Current**: 1.2.0  
**Status**: Production Ready ✅  
**Tests**: 11/12 passing  
**Service Mesh**: Integrated ✅

---

**Keep this handy for quick reference!**
