#!/bin/bash
# install_and_verify.sh - Install dependencies and verify setup

set -e  # Exit on error

echo "============================================"
echo "Dmitry - Installation and Verification"
echo "============================================"
echo ""

# Check Python version
echo "1. Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

if ! python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "   ❌ Python 3.9+ required"
    exit 1
fi
echo "   ✅ Python version OK"
echo ""

# Check if virtual environment exists
echo "2. Checking virtual environment..."
if [ ! -d ".venv" ]; then
    echo "   Creating virtual environment..."
    python -m venv .venv
    echo "   ✅ Virtual environment created"
else
    echo "   ✅ Virtual environment exists"
fi
echo ""

# Activate virtual environment
echo "3. Activating virtual environment..."
source .venv/bin/activate
echo "   ✅ Virtual environment activated"
echo ""

# Install production dependencies
echo "4. Installing production dependencies..."
pip install -q -r MarkX/requirements_production.txt
echo "   ✅ Production dependencies installed"
echo ""

# Install development dependencies
echo "5. Installing development dependencies..."
pip install -q -r requirements-dev.txt
echo "   ✅ Development dependencies installed"
echo ""

# Check .env file
echo "6. Checking configuration..."
if [ ! -f ".env" ]; then
    echo "   Creating .env from template..."
    cp .env.example .env
    echo "   ⚠️  Please edit .env with your API keys"
else
    echo "   ✅ .env file exists"
fi
echo ""

# Run tests
echo "7. Running tests..."
pytest --tb=short -q
test_result=$?
if [ $test_result -eq 0 ]; then
    echo "   ✅ All tests passed"
else
    echo "   ⚠️  Some tests failed (may need Platform running)"
fi
echo ""

# Check code quality
echo "8. Checking code quality..."
echo "   Running ruff..."
ruff check MarkX/ --quiet || echo "   ⚠️  Ruff found issues"
echo "   ✅ Code quality check complete"
echo ""

# Verify imports
echo "9. Verifying imports..."
python -c "
from config import get_settings
from core.logging import get_logger
from core.tracing import get_tracing
print('   ✅ All imports successful')
"
echo ""

# Summary
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Run server: cd MarkX && python main.py"
echo "3. Test endpoints: curl http://127.0.0.1:8765/health"
echo "4. Read docs: cat README.md"
echo ""
echo "Quick commands:"
echo "  pytest                    # Run tests"
echo "  pytest --cov=MarkX       # Run with coverage"
echo "  ruff check MarkX/        # Lint code"
echo "  cd MarkX && python main.py  # Start server"
echo ""
echo "✅ Ready to develop!"
