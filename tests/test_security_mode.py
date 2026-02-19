"""
Unit tests for Enhanced Security Mode
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'MarkX'))

from modes.security_mode_enhanced import EnhancedSecurityMode


class TestEnhancedSecurityMode:
    """Test Enhanced Security Mode functionality"""
    
    @pytest.fixture
    def security_mode(self):
        """Create security mode instance"""
        return EnhancedSecurityMode()
    
    def test_initialization(self, security_mode):
        """Test security mode initializes correctly"""
        assert security_mode is not None
        assert hasattr(security_mode, 'sub_modes')
        assert len(security_mode.sub_modes) == 7
    
    def test_sub_modes_exist(self, security_mode):
        """Test all 7 sub-modes are present"""
        expected_modes = [
            'threat_hunting',
            'vulnerability_assessment',
            'ai_security_audit',
            'compliance_audit',
            'incident_response',
            'cloud_security_posture',
            'penetration_testing'
        ]
        for mode in expected_modes:
            assert mode in security_mode.sub_modes
    
    def test_mode_switching(self, security_mode):
        """Test switching between sub-modes"""
        result = security_mode.switch_sub_mode('threat_hunting')
        assert result['success'] is True
        assert security_mode.current_sub_mode == 'threat_hunting'
    
    def test_invalid_mode_switch(self, security_mode):
        """Test switching to invalid sub-mode"""
        result = security_mode.switch_sub_mode('invalid_mode')
        assert result['success'] is False
    
    def test_get_capabilities(self, security_mode):
        """Test getting mode capabilities"""
        capabilities = security_mode.get_capabilities()
        assert 'sub_modes' in capabilities
        assert 'integrations' in capabilities
        assert len(capabilities['sub_modes']) == 7
