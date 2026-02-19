# modes/security_mode/__init__.py
"""
Enhanced Security Mode Package

Enterprise-grade AI Risk Intelligence and Cybersecurity platform.
This is the integration hub for all security operations.
"""

# For backward compatibility, import SecurityMode from parent
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from core import EnhancedSecurityMode, SecurityFinding, ThreatIntelligence, ComplianceStatus
    from integrations import SecurityIntegrationManager
    
    __all__ = [
        "EnhancedSecurityMode",
        "SecurityFinding",
        "ThreatIntelligence",
        "ComplianceStatus",
        "SecurityIntegrationManager",
    ]
except ImportError:
    # Fallback if enhanced mode not available
    __all__ = []
