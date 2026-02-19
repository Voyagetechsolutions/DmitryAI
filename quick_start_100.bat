@echo off
REM Quick Start Script - Get Dmitry to 100% (Windows)
REM Run this to begin the transformation

echo ==========================================
echo DMITRY 100%% - QUICK START
echo ==========================================
echo.

REM Step 1: Secure the platform
echo Step 1: Securing the platform...
echo.

REM Create .env.example
if not exist "MarkX\.env.example" (
    echo Creating .env.example template...
    (
        echo # OpenRouter API Configuration
        echo OPENROUTER_API_KEY=your_openrouter_key_here
        echo DMITRY_MODEL=google/gemini-2.0-flash-001
        echo.
        echo # Security Integrations ^(Optional^)
        echo SPLUNK_API_KEY=your_splunk_key
        echo SPLUNK_API_URL=https://your-splunk-instance:8089
        echo.
        echo ELASTIC_API_KEY=your_elastic_key
        echo ELASTIC_API_URL=https://your-elastic-instance:9200
        echo.
        echo VIRUSTOTAL_API_KEY=your_virustotal_key
        echo MISP_API_KEY=your_misp_key
        echo MISP_URL=https://your-misp-instance
        echo.
        echo # Cloud Security ^(Optional^)
        echo AWS_ACCESS_KEY_ID=your_aws_key
        echo AWS_SECRET_ACCESS_KEY=your_aws_secret
        echo AWS_REGION=us-east-1
        echo.
        echo AZURE_TENANT_ID=your_azure_tenant
        echo AZURE_CLIENT_ID=your_azure_client
        echo AZURE_CLIENT_SECRET=your_azure_secret
        echo.
        echo GCP_PROJECT_ID=your_gcp_project
        echo GCP_CREDENTIALS_PATH=/path/to/credentials.json
        echo.
        echo # Authentication
        echo JWT_SECRET_KEY=generate_a_random_secret_key_here
        echo API_RATE_LIMIT=100
    ) > MarkX\.env.example
    echo [OK] Created .env.example
) else (
    echo [OK] .env.example already exists
)

REM Add .env to .gitignore
findstr /C:"MarkX/.env" .gitignore >nul 2>&1
if errorlevel 1 (
    echo Adding .env to .gitignore...
    (
        echo.
        echo # Environment variables
        echo MarkX/.env
        echo **/.env
    ) >> .gitignore
    echo [OK] Updated .gitignore
) else (
    echo [OK] .gitignore already configured
)

echo.
echo WARNING: You must manually:
echo    1. Go to https://openrouter.ai/keys
echo    2. Generate a NEW API key
echo    3. Update MarkX/.env with the new key
echo    4. Delete the old exposed key from OpenRouter dashboard
echo.

REM Step 2: Install dependencies
echo Step 2: Installing dependencies...
echo.

if exist "MarkX\requirements_full.txt" (
    echo Installing Python packages...
    pip install -r MarkX\requirements_full.txt
    
    echo Installing security packages...
    pip install pyjwt prometheus-client structlog redis
    
    echo [OK] Dependencies installed
) else (
    echo [WARNING] requirements_full.txt not found
)

echo.

REM Step 3: Create necessary directories
echo Step 3: Creating directory structure...
echo.

mkdir MarkX\logs 2>nul
mkdir MarkX\modes\security_mode\integrations\siem 2>nul
mkdir MarkX\modes\security_mode\integrations\threat_intel 2>nul
mkdir MarkX\modes\security_mode\integrations\vulnerability 2>nul
mkdir MarkX\modes\security_mode\integrations\cloud_security 2>nul
mkdir MarkX\modes\security_mode\ai_security 2>nul
mkdir MarkX\modes\security_mode\compliance 2>nul
mkdir MarkX\modes\security_mode\incident_response 2>nul
mkdir MarkX\tools\security 2>nul
mkdir tests 2>nul

echo [OK] Directory structure created
echo.

REM Step 4: Create __init__.py files
echo Step 4: Creating Python package files...
echo.

type nul > MarkX\modes\security_mode\integrations\siem\__init__.py
type nul > MarkX\modes\security_mode\integrations\threat_intel\__init__.py
type nul > MarkX\modes\security_mode\integrations\vulnerability\__init__.py
type nul > MarkX\modes\security_mode\integrations\cloud_security\__init__.py
type nul > MarkX\modes\security_mode\ai_security\__init__.py
type nul > MarkX\modes\security_mode\compliance\__init__.py
type nul > MarkX\modes\security_mode\incident_response\__init__.py
type nul > MarkX\tools\security\__init__.py

echo [OK] Package files created
echo.

REM Step 5: Summary
echo ==========================================
echo SETUP COMPLETE!
echo ==========================================
echo.
echo Next Steps:
echo.
echo 1. CRITICAL - Rotate API Key:
echo    - Go to https://openrouter.ai/keys
echo    - Generate new key
echo    - Update MarkX\.env
echo.
echo 2. Review the implementation plan:
echo    - Read GETTING_TO_100_PERCENT.md
echo    - Read ACTION_PLAN_100_PERCENT.md
echo    - Read IMPLEMENTATION_PLAN.md
echo.
echo 3. Fix permissions (edit MarkX\dmitry_operator\permissions.py):
echo    - Restore proper risk levels
echo    - Not everything should be LOW risk
echo.
echo 4. Integrate Enhanced Security Mode:
echo    - Edit MarkX\modes\mode_manager.py
echo    - Replace SecurityMode with EnhancedSecurityMode
echo.
echo 5. Test the system:
echo    cd MarkX
echo    python run_dmitry.py --mode server
echo.
echo 6. Start Week 1 tasks from ACTION_PLAN_100_PERCENT.md
echo.
echo ==========================================
echo Documentation:
echo   - FINDINGS.md - Current state analysis
echo   - GETTING_TO_100_PERCENT.md - Executive summary
echo   - ACTION_PLAN_100_PERCENT.md - Week-by-week plan
echo   - IMPLEMENTATION_PLAN.md - Technical details
echo ==========================================
echo.
echo Good luck! You're on your way to 100%%! 🚀
pause
