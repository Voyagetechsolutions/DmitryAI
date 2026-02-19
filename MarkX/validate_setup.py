#!/usr/bin/env python3
# validate_setup.py
"""
Dmitry Setup Validation Script

Validates that all critical components are properly configured
and ready for production use.
"""

import os
import sys
from pathlib import Path


class Colors:
    """Terminal colors for output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.END} {text}")


def check_environment_variables():
    """Check critical environment variables."""
    print_header("Environment Variables")
    
    issues = []
    
    # Critical variables
    if not os.getenv("OPENROUTER_API_KEY"):
        print_error("OPENROUTER_API_KEY not set")
        issues.append("Missing OPENROUTER_API_KEY")
    else:
        key = os.getenv("OPENROUTER_API_KEY")
        if key.startswith("sk-or-v1-"):
            print_success("OPENROUTER_API_KEY configured")
        else:
            print_warning("OPENROUTER_API_KEY format looks incorrect")
    
    # Optional but recommended
    if not os.getenv("JWT_SECRET_KEY"):
        print_warning("JWT_SECRET_KEY not set (will use generated key)")
    else:
        print_success("JWT_SECRET_KEY configured")
    
    return issues


def check_file_structure():
    """Check that critical files and directories exist."""
    print_header("File Structure")
    
    issues = []
    base_path = Path(__file__).parent
    
    critical_files = [
        "main.py",
        "llm.py",
        "run_dmitry.py",
        ".env.example",
        "modes/mode_manager.py",
        "modes/security_mode_enhanced.py",
        "modes/security_mode/ai_security/prompt_injection_detector.py",
        "agent/auth.py",
        "core/audit_log.py",
        "dmitry_operator/permissions.py",
    ]
    
    for file_path in critical_files:
        full_path = base_path / file_path
        if full_path.exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - MISSING")
            issues.append(f"Missing file: {file_path}")
    
    # Check directories
    critical_dirs = [
        "logs",
        "modes/security_mode/integrations",
        "modes/security_mode/ai_security",
        "modes/security_mode/compliance",
        "modes/security_mode/incident_response",
    ]
    
    for dir_path in critical_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print_success(f"{dir_path}/")
        else:
            print_warning(f"{dir_path}/ - Creating...")
            full_path.mkdir(parents=True, exist_ok=True)
    
    return issues


def check_dependencies():
    """Check that critical Python packages are installed."""
    print_header("Python Dependencies")
    
    issues = []
    
    critical_packages = [
        ("requests", "HTTP requests"),
        ("dotenv", "Environment variables"),
        ("jwt", "Authentication (PyJWT)"),
        ("structlog", "Structured logging"),
        ("chromadb", "Vector database"),
    ]
    
    for package, description in critical_packages:
        try:
            __import__(package)
            print_success(f"{package:20} - {description}")
        except ImportError:
            print_error(f"{package:20} - NOT INSTALLED ({description})")
            issues.append(f"Missing package: {package}")
    
    # Optional packages
    optional_packages = [
        ("prometheus_client", "Metrics"),
        ("redis", "Caching"),
        ("pytesseract", "OCR"),
        ("cv2", "Computer vision (opencv-python)"),
        ("boto3", "AWS integration"),
    ]
    
    print("\nOptional packages:")
    for package, description in optional_packages:
        try:
            __import__(package)
            print_success(f"{package:20} - {description}")
        except ImportError:
            print_warning(f"{package:20} - Not installed ({description})")
    
    return issues


def check_security_configuration():
    """Check security configuration."""
    print_header("Security Configuration")
    
    issues = []
    base_path = Path(__file__).parent
    
    # Check .env is in .gitignore
    gitignore_path = base_path.parent / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
            if ".env" in content:
                print_success(".env is in .gitignore")
            else:
                print_error(".env NOT in .gitignore - SECURITY RISK!")
                issues.append(".env not in .gitignore")
    else:
        print_warning(".gitignore not found")
    
    # Check .env.example exists
    env_example = base_path / ".env.example"
    if env_example.exists():
        print_success(".env.example template exists")
    else:
        print_warning(".env.example not found")
    
    # Check permissions.py has proper risk levels
    permissions_file = base_path / "dmitry_operator" / "permissions.py"
    if permissions_file.exists():
        with open(permissions_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'RiskLevel.HIGH' in content:
                print_success("Permissions system has HIGH risk levels configured")
            else:
                print_warning("Permissions system may still be in God Mode")
    
    return issues


def check_integrations():
    """Check integration readiness."""
    print_header("Security Integrations")
    
    integrations = {
        "SPLUNK_API_KEY": "Splunk SIEM",
        "ELASTIC_API_KEY": "Elastic Security",
        "VIRUSTOTAL_API_KEY": "VirusTotal",
        "MISP_API_KEY": "MISP Threat Intel",
        "AWS_ACCESS_KEY_ID": "AWS Security Hub",
        "AZURE_CLIENT_ID": "Azure Security Center",
        "GCP_PROJECT_ID": "GCP Security Command Center",
    }
    
    configured = 0
    for env_var, name in integrations.items():
        if os.getenv(env_var):
            print_success(f"{name:30} - Configured")
            configured += 1
        else:
            print_warning(f"{name:30} - Not configured")
    
    print(f"\n{configured}/{len(integrations)} integrations configured")
    
    return []


def main():
    """Run all validation checks."""
    print(f"\n{Colors.BOLD}Dmitry v2.0 - Setup Validation{Colors.END}")
    print(f"{Colors.BOLD}Checking system readiness...{Colors.END}")
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_environment_variables())
    all_issues.extend(check_file_structure())
    all_issues.extend(check_dependencies())
    all_issues.extend(check_security_configuration())
    all_issues.extend(check_integrations())
    
    # Summary
    print_header("Validation Summary")
    
    if not all_issues:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All critical checks passed!{Colors.END}")
        print(f"\n{Colors.GREEN}System is ready for operation.{Colors.END}")
        print(f"\nTo start Dmitry:")
        print(f"  python run_dmitry.py --mode server")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Found {len(all_issues)} issue(s):{Colors.END}\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print(f"\n{Colors.YELLOW}Please fix these issues before running Dmitry.{Colors.END}")
        print(f"\nFor help, see:")
        print(f"  - GETTING_TO_100_PERCENT.md")
        print(f"  - ACTION_PLAN_100_PERCENT.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
