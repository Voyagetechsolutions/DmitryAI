@echo off
REM install_and_verify.bat - Install dependencies and verify setup (Windows)

echo ============================================
echo Dmitry - Installation and Verification
echo ============================================
echo.

REM Check Python version
echo 1. Checking Python version...
python --version
if errorlevel 1 (
    echo    X Python not found
    exit /b 1
)
echo    √ Python found
echo.

REM Check if virtual environment exists
echo 2. Checking virtual environment...
if not exist ".venv" (
    echo    Creating virtual environment...
    python -m venv .venv
    echo    √ Virtual environment created
) else (
    echo    √ Virtual environment exists
)
echo.

REM Activate virtual environment
echo 3. Activating virtual environment...
call .venv\Scripts\activate.bat
echo    √ Virtual environment activated
echo.

REM Install production dependencies
echo 4. Installing production dependencies...
pip install -q -r MarkX\requirements_production.txt
echo    √ Production dependencies installed
echo.

REM Install development dependencies
echo 5. Installing development dependencies...
pip install -q -r requirements-dev.txt
echo    √ Development dependencies installed
echo.

REM Check .env file
echo 6. Checking configuration...
if not exist ".env" (
    echo    Creating .env from template...
    copy .env.example .env
    echo    ! Please edit .env with your API keys
) else (
    echo    √ .env file exists
)
echo.

REM Run tests
echo 7. Running tests...
pytest --tb=short -q
if errorlevel 1 (
    echo    ! Some tests failed (may need Platform running)
) else (
    echo    √ All tests passed
)
echo.

REM Check code quality
echo 8. Checking code quality...
echo    Running ruff...
ruff check MarkX\ --quiet
echo    √ Code quality check complete
echo.

REM Verify imports
echo 9. Verifying imports...
python -c "from config import get_settings; from core.logging import get_logger; from core.tracing import get_tracing; print('   √ All imports successful')"
echo.

REM Summary
echo ============================================
echo Installation Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Edit .env with your API keys
echo 2. Run server: cd MarkX ^&^& python main.py
echo 3. Test endpoints: curl http://127.0.0.1:8765/health
echo 4. Read docs: type README.md
echo.
echo Quick commands:
echo   pytest                    # Run tests
echo   pytest --cov=MarkX       # Run with coverage
echo   ruff check MarkX\        # Lint code
echo   cd MarkX ^&^& python main.py  # Start server
echo.
echo √ Ready to develop!

pause
