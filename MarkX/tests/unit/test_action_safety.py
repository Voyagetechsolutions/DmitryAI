# test_action_safety.py - Unit tests for action safety gate

import pytest
import sys
from pathlib import Path

# Add MarkX to path
markx_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(markx_path))

from core.action_safety import ActionSafetyGate, SafeRecommendation


class TestActionSafetyGate:
    """Test ActionSafetyGate class."""
    
    def test_valid_action(self):
        """Test creating a valid action recommendation."""
        rec = ActionSafetyGate.create_safe_recommendation(
            action="isolate_entity",
            target="customer-db",
            reason="High risk detected",
            risk_reduction_estimate=0.35,
            confidence=0.85,
            priority="HIGH",
            evidence_call_ids=["call-1", "call-2"]
        )
        
        assert rec.is_valid is True
        assert rec.action == "isolate_entity"
        assert rec.target == "customer-db"
        assert rec.approval_required is True
        assert rec.blast_radius == "entity_only"
        assert rec.evidence_count == 2
    
    def test_invalid_action_type(self):
        """Test that invalid action types are rejected."""
        rec = ActionSafetyGate.create_safe_recommendation(
            action="delete_everything",  # Not in allow-list
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.5,
            confidence=0.8,
            priority="HIGH",
            evidence_call_ids=["call-1"]
        )
        
        assert rec.is_valid is False
        assert "not in allow-list" in rec.validation_errors[0]
    
    def test_insufficient_evidence(self):
        """Test that insufficient evidence is flagged."""
        rec = ActionSafetyGate.create_safe_recommendation(
            action="isolate_entity",
            target="customer-db",
            reason="High risk",
            risk_reduction_estimate=0.35,
            confidence=0.85,
            priority="HIGH",
            evidence_call_ids=[]  # No evidence
        )
        
        assert rec.is_valid is False
        assert "Insufficient evidence" in rec.validation_errors[0]
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence
        rec1 = ActionSafetyGate.create_safe_recommendation(
            action="increase_monitoring",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.15,
            confidence=0.75,
            priority="MEDIUM",
            evidence_call_ids=["call-1"]
        )
        assert rec1.is_valid is True
        
        # Invalid confidence (too high)
        rec2 = ActionSafetyGate.create_safe_recommendation(
            action="increase_monitoring",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.15,
            confidence=1.5,  # > 1.0
            priority="MEDIUM",
            evidence_call_ids=["call-1"]
        )
        assert rec2.is_valid is False
        
        # Invalid confidence (negative)
        rec3 = ActionSafetyGate.create_safe_recommendation(
            action="increase_monitoring",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.15,
            confidence=-0.1,  # < 0.0
            priority="MEDIUM",
            evidence_call_ids=["call-1"]
        )
        assert rec3.is_valid is False
    
    def test_blast_radius_assignment(self):
        """Test blast radius is assigned correctly."""
        # Entity-only action
        rec1 = ActionSafetyGate.create_safe_recommendation(
            action="isolate_entity",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.35,
            confidence=0.85,
            priority="HIGH",
            evidence_call_ids=["call-1"]
        )
        assert rec1.blast_radius == "entity_only"
        
        # Segment action
        rec2 = ActionSafetyGate.create_safe_recommendation(
            action="block_access",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.30,
            confidence=0.80,
            priority="HIGH",
            evidence_call_ids=["call-1"]
        )
        assert rec2.blast_radius == "segment"
        
        # Org-wide action
        rec3 = ActionSafetyGate.create_safe_recommendation(
            action="enforce_policy",
            target="all",
            reason="Test",
            risk_reduction_estimate=0.40,
            confidence=0.90,
            priority="CRITICAL",
            evidence_call_ids=["call-1", "call-2", "call-3"]
        )
        assert rec3.blast_radius == "org_wide"
    
    def test_approval_required(self):
        """Test approval_required is set correctly."""
        # High impact - requires approval
        rec1 = ActionSafetyGate.create_safe_recommendation(
            action="isolate_entity",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.35,
            confidence=0.85,
            priority="HIGH",
            evidence_call_ids=["call-1"]
        )
        assert rec1.approval_required is True
        
        # Low impact - no approval needed
        rec2 = ActionSafetyGate.create_safe_recommendation(
            action="increase_monitoring",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.15,
            confidence=0.75,
            priority="LOW",
            evidence_call_ids=["call-1"]
        )
        assert rec2.approval_required is False
    
    def test_impact_level(self):
        """Test impact level is assigned correctly."""
        # High impact
        rec1 = ActionSafetyGate.create_safe_recommendation(
            action="isolate_entity",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.35,
            confidence=0.85,
            priority="HIGH",
            evidence_call_ids=["call-1"]
        )
        assert rec1.impact_level == "high"
        
        # Medium impact
        rec2 = ActionSafetyGate.create_safe_recommendation(
            action="block_access",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.30,
            confidence=0.80,
            priority="MEDIUM",
            evidence_call_ids=["call-1"]
        )
        assert rec2.impact_level == "medium"
        
        # Low impact
        rec3 = ActionSafetyGate.create_safe_recommendation(
            action="increase_monitoring",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.15,
            confidence=0.75,
            priority="LOW",
            evidence_call_ids=["call-1"]
        )
        assert rec3.impact_level == "low"
    
    def test_evidence_threshold(self):
        """Test evidence threshold enforcement."""
        # High impact needs more evidence
        rec1 = ActionSafetyGate.create_safe_recommendation(
            action="isolate_entity",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.35,
            confidence=0.85,
            priority="HIGH",
            evidence_call_ids=["call-1"]  # Only 1 piece
        )
        # Should still be valid with 1 piece (minimum is 1)
        assert rec1.is_valid is True
        
        # But with 0 pieces, should be invalid
        rec2 = ActionSafetyGate.create_safe_recommendation(
            action="isolate_entity",
            target="customer-db",
            reason="Test",
            risk_reduction_estimate=0.35,
            confidence=0.85,
            priority="HIGH",
            evidence_call_ids=[]
        )
        assert rec2.is_valid is False
    
    def test_allowed_actions_list(self):
        """Test that only allowed actions are accepted."""
        allowed_actions = [
            "isolate_entity",
            "block_access",
            "revoke_credentials",
            "increase_monitoring",
            "alert_team",
            "quarantine_file",
            "disable_service",
            "rotate_keys",
            "enforce_policy",
            "update_firewall",
            "scan_entity",
            "backup_data",
            "notify_admin",
            "log_incident",
            "request_review"
        ]
        
        for action in allowed_actions:
            rec = ActionSafetyGate.create_safe_recommendation(
                action=action,
                target="test",
                reason="Test",
                risk_reduction_estimate=0.2,
                confidence=0.7,
                priority="MEDIUM",
                evidence_call_ids=["call-1"]
            )
            assert rec.is_valid is True, f"Action {action} should be valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
