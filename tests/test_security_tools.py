"""
Unit tests for Security Tools
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'MarkX'))

from tools.security.threat_intel_lookup import ThreatIntelLookup
from tools.security.compliance_checker import ComplianceChecker
from tools.security.ai_security_audit import AISecurityAudit


class TestThreatIntelLookup:
    """Test threat intelligence lookup"""
    
    @pytest.fixture
    def threat_intel(self):
        return ThreatIntelLookup()
    
    def test_ioc_detection(self, threat_intel):
        """Test IOC detection in text"""
        text = "Suspicious IP: 192.168.1.100 and domain: malicious.com"
        iocs = threat_intel.detect_iocs(text)
        assert len(iocs) > 0
        assert any(ioc['type'] == 'ip' for ioc in iocs)
        assert any(ioc['type'] == 'domain' for ioc in iocs)
    
    def test_lookup_ioc(self, threat_intel):
        """Test IOC lookup"""
        result = threat_intel.lookup_ioc("192.168.1.1", ioc_type="ip")
        assert 'ioc' in result
        assert 'type' in result
        assert result['type'] == 'ip'


class TestComplianceChecker:
    """Test compliance checking"""
    
    @pytest.fixture
    def compliance_checker(self):
        return ComplianceChecker()
    
    def test_supported_frameworks(self, compliance_checker):
        """Test supported frameworks"""
        frameworks = compliance_checker.get_supported_frameworks()
        assert 'soc2' in frameworks
        assert 'iso27001' in frameworks
        assert 'nist_csf' in frameworks
        assert 'gdpr' in frameworks
    
    def test_check_compliance(self, compliance_checker):
        """Test compliance check"""
        result = compliance_checker.check_compliance(
            framework="soc2",
            system_config={"encryption": True, "mfa": True}
        )
        assert 'framework' in result
        assert 'controls_checked' in result
        assert 'compliance_score' in result


class TestAISecurityAudit:
    """Test AI security audit"""
    
    @pytest.fixture
    def ai_audit(self):
        return AISecurityAudit()
    
    def test_audit_model(self, ai_audit):
        """Test model security audit"""
        model_config = {
            "name": "test-model",
            "type": "llm",
            "input_validation": True,
            "output_filtering": False
        }
        result = ai_audit.audit_model(model_config)
        assert 'model_name' in result
        assert 'owasp_llm_checks' in result
        assert 'risk_score' in result
    
    def test_owasp_coverage(self, ai_audit):
        """Test OWASP LLM Top 10 coverage"""
        checks = ai_audit.get_owasp_checks()
        assert len(checks) == 10
        assert 'LLM01' in checks  # Prompt Injection
        assert 'LLM02' in checks  # Insecure Output Handling
