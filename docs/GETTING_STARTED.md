# Getting Started with Dmitry

**5-minute guide to get Dmitry running**

---

## Prerequisites

- Python 3.9 or higher
- Git
- OpenAI API key (or compatible LLM)

---

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/Mark-X.git
cd Mark-X

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r MarkX/requirements_production.txt
```

---

## Step 2: Configure (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

**Minimum required configuration:**
```bash
OPENAI_API_KEY=sk-your-api-key-here
DMITRY_PORT=8765
LOG_LEVEL=INFO
```

---

## Step 3: Run Dmitry (30 seconds)

```bash
cd MarkX
python main.py
```

**Expected output:**
```
✓ Agent API server started on http://127.0.0.1:8765
```

---

## Step 4: Test It Works (1 minute)

### Test Health Endpoint
```bash
curl http://127.0.0.1:8765/health
```

**Expected response:**
```json
{
  "service": "dmitry",
  "status": "healthy",
  "version": "1.2",
  "uptime_seconds": 5.2,
  "checks": {
    "llm": true,
    "platform": false,
    "call_ledger": true
  }
}
```

### Test Chat Endpoint
```bash
curl -X POST http://127.0.0.1:8765/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what can you do?",
    "context": {}
  }'
```

---

## Step 5: Run Tests (30 seconds)

```bash
# Install dev dependencies (if not already installed)
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=MarkX --cov-report=html
```

**Expected output:**
```
============ test session starts ============
collected 48 items

MarkX/tests/unit/test_call_ledger.py ............ [ 25%]
MarkX/tests/unit/test_action_safety.py ........... [ 48%]
MarkX/tests/unit/test_input_sanitizer.py .............. [ 77%]
MarkX/test_complete_loop.py ....... [ 92%]
MarkX/test_service_mesh.py .... [100%]

============ 48 passed in 2.5s ============
```

---

## What's Next?

### For Users
- Read [API Documentation](docs/API.md)
- Try the [Quick Start Guide](docs/guides/QUICK_START.md)
- Explore [Service Mesh Integration](docs/guides/SERVICE_MESH_QUICK_START.md)

### For Developers
- Read [Development Guide](docs/guides/DEVELOPMENT.md)
- Read [Testing Guide](docs/guides/TESTING.md)
- Check [Contributing Guidelines](CONTRIBUTING.md)

### For Deployment
- Read [Deployment Guide](docs/DEPLOYMENT.md)
- Check [Deployment Checklist](docs/guides/DEPLOYMENT_CHECKLIST.md)
- Review [Architecture Docs](docs/architecture/SYSTEM_ARCHITECTURE.md)

---

## Common Issues

### Port Already in Use
```bash
# Change port in .env
DMITRY_PORT=8766
```

### OpenAI API Key Not Set
```bash
# Set in .env
OPENAI_API_KEY=sk-your-key-here
```

### Tests Failing
```bash
# Make sure you're in the right directory
cd Mark-X

# Run tests with verbose output
pytest -v
```

---

## Quick Reference

### Start Server
```bash
cd MarkX && python main.py
```

### Run Tests
```bash
pytest
```

### Check Health
```bash
curl http://127.0.0.1:8765/health
```

### View Documentation
```bash
# Open README
cat README.md

# Browse docs
ls docs/
```

---

## Support

- **Documentation**: Start with [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/Mark-X/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Mark-X/discussions)
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

## Summary

**You now have Dmitry running!**

**What you did:**
1. ✅ Cloned and set up environment
2. ✅ Configured with API key
3. ✅ Started Dmitry server
4. ✅ Tested endpoints
5. ✅ Ran tests

**Time taken**: ~5 minutes

**Next steps**: Explore the documentation and start building!

---

**Welcome to Dmitry! 🚀**
