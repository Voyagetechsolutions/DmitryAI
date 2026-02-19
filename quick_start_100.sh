#!/bin/bash
# Quick Start Script - Get Dmitry to 100%
# Run this to begin the transformation

echo "=========================================="
echo "DMITRY 100% - QUICK START"
echo "=========================================="
echo ""

# Step 1: Secure the platform
echo "Step 1: Securing the platform..."
echo ""

# Create .env.example
if [ ! -f "MarkX/.env.example" ]; then
    echo "Creating .env.example template..."
    cat > MarkX/.env.example << 'EOF'
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_key_here
DMITRY_MODEL=google/gemini-2.0-flash-001

# Security Integrations (Optional)
SPLUNK_API_KEY=your_splunk_key
SPLUNK_API_URL=https://your-splunk-instance:8089

ELASTIC_API_KEY=your_elastic_key
ELASTIC_API_URL=https://your-elastic-instance:9200

VIRUSTOTAL_API_KEY=your_virustotal_key
MISP_API_KEY=your_misp_key
MISP_URL=https://your-misp-instance

# Cloud Security (Optional)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1

AZURE_TENANT_ID=your_azure_tenant
AZURE_CLIENT_ID=your_azure_client
AZURE_CLIENT_SECRET=your_azure_secret

GCP_PROJECT_ID=your_gcp_project
GCP_CREDENTIALS_PATH=/path/to/credentials.json

# Authentication
JWT_SECRET_KEY=generate_a_random_secret_key_here
API_RATE_LIMIT=100
EOF
    echo "✓ Created .env.example"
else
    echo "✓ .env.example already exists"
fi

# Add .env to .gitignore
if ! grep -q "MarkX/.env" .gitignore 2>/dev/null; then
    echo "Adding .env to .gitignore..."
    echo "" >> .gitignore
    echo "# Environment variables" >> .gitignore
    echo "MarkX/.env" >> .gitignore
    echo "**/.env" >> .gitignore
    echo "✓ Updated .gitignore"
else
    echo "✓ .gitignore already configured"
fi

echo ""
echo "⚠️  IMPORTANT: You must manually:"
echo "   1. Go to https://openrouter.ai/keys"
echo "   2. Generate a NEW API key"
echo "   3. Update MarkX/.env with the new key"
echo "   4. Delete the old exposed key from OpenRouter dashboard"
echo ""

# Step 2: Install dependencies
echo "Step 2: Installing dependencies..."
echo ""

if [ -f "MarkX/requirements_full.txt" ]; then
    echo "Installing Python packages..."
    pip install -r MarkX/requirements_full.txt
    
    # Add new security packages
    echo "Installing security packages..."
    pip install pyjwt prometheus-client structlog redis
    
    echo "✓ Dependencies installed"
else
    echo "⚠️  requirements_full.txt not found"
fi

echo ""

# Step 3: Create necessary directories
echo "Step 3: Creating directory structure..."
echo ""

mkdir -p MarkX/logs
mkdir -p MarkX/modes/security_mode/integrations/siem
mkdir -p MarkX/modes/security_mode/integrations/threat_intel
mkdir -p MarkX/modes/security_mode/integrations/vulnerability
mkdir -p MarkX/modes/security_mode/integrations/cloud_security
mkdir -p MarkX/modes/security_mode/ai_security
mkdir -p MarkX/modes/security_mode/compliance
mkdir -p MarkX/modes/security_mode/incident_response
mkdir -p MarkX/tools/security
mkdir -p tests

echo "✓ Directory structure created"
echo ""

# Step 4: Create __init__.py files
echo "Step 4: Creating Python package files..."
echo ""

touch MarkX/modes/security_mode/integrations/siem/__init__.py
touch MarkX/modes/security_mode/integrations/threat_intel/__init__.py
touch MarkX/modes/security_mode/integrations/vulnerability/__init__.py
touch MarkX/modes/security_mode/integrations/cloud_security/__init__.py
touch MarkX/modes/security_mode/ai_security/__init__.py
touch MarkX/modes/security_mode/compliance/__init__.py
touch MarkX/modes/security_mode/incident_response/__init__.py
touch MarkX/tools/security/__init__.py

echo "✓ Package files created"
echo ""

# Step 5: Summary
echo "=========================================="
echo "SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. CRITICAL - Rotate API Key:"
echo "   - Go to https://openrouter.ai/keys"
echo "   - Generate new key"
echo "   - Update MarkX/.env"
echo ""
echo "2. Review the implementation plan:"
echo "   - Read GETTING_TO_100_PERCENT.md"
echo "   - Read ACTION_PLAN_100_PERCENT.md"
echo "   - Read IMPLEMENTATION_PLAN.md"
echo ""
echo "3. Fix permissions (edit MarkX/dmitry_operator/permissions.py):"
echo "   - Restore proper risk levels"
echo "   - Not everything should be LOW risk"
echo ""
echo "4. Integrate Enhanced Security Mode:"
echo "   - Edit MarkX/modes/mode_manager.py"
echo "   - Replace SecurityMode with EnhancedSecurityMode"
echo ""
echo "5. Test the system:"
echo "   cd MarkX"
echo "   python run_dmitry.py --mode server"
echo ""
echo "6. Start Week 1 tasks from ACTION_PLAN_100_PERCENT.md"
echo ""
echo "=========================================="
echo "Documentation:"
echo "  - FINDINGS.md - Current state analysis"
echo "  - GETTING_TO_100_PERCENT.md - Executive summary"
echo "  - ACTION_PLAN_100_PERCENT.md - Week-by-week plan"
echo "  - IMPLEMENTATION_PLAN.md - Technical details"
echo "=========================================="
echo ""
echo "Good luck! You're on your way to 100%! 🚀"
