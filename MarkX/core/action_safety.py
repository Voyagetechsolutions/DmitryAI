# core/action_safety.py
"""
Action Safety Gate - Prevents Dmitry from recommending dangerous actions.

Enforces:
- Allow-listed action values only
- Evidence thresholds for high-impact actions
- Approval requirements
- Blast radius estimates
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class ActionType(Enum):
    """Allow-listed action types."""
    
    # Investigation (Low Impact)
    INVESTIGATE = "investigate"
    MONITOR = "monitor"
    ALERT = "alert"
    LOG = "log"
    
    # Containment (Medium Impact)
    INCREASE_MONITORING = "increase_monitoring"
    RATE_LIMIT = "rate_limit"
    REQUIRE_MFA = "require_mfa"
    NOTIFY_ADMIN = "notify_admin"
    
    # Enforcement (High Impact)
    BLOCK_ACCESS = "block_access"
    ISOLATE_ENTITY = "isolate_entity"
    QUARANTINE = "quarantine"
    REVOKE_CREDENTIALS = "revoke_credentials"
    
    # Critical (Org-Wide Impact)
    SHUTDOWN_SERVICE = "shutdown_service"
    EMERGENCY_LOCKDOWN = "emergency_lockdown"


class BlastRadius(Enum):
    """Blast radius of an action."""
    
    ENTITY_ONLY = "entity_only"      # Affects single entity
    SEGMENT = "segment"              # Affects group/segment
    ORG_WIDE = "org_wide"            # Affects entire organization


class ImpactLevel(Enum):
    """Impact level of an action."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ActionPolicy:
    """Policy for an action type."""
    
    action_type: ActionType
    impact_level: ImpactLevel
    blast_radius: BlastRadius
    requires_approval: bool
    min_evidence_count: int
    min_confidence: float
    max_auto_execute: bool  # Can be auto-executed by Platform


# Action policies (immutable)
ACTION_POLICIES: Dict[ActionType, ActionPolicy] = {
    # Investigation actions
    ActionType.INVESTIGATE: ActionPolicy(
        action_type=ActionType.INVESTIGATE,
        impact_level=ImpactLevel.LOW,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=False,
        min_evidence_count=1,
        min_confidence=0.5,
        max_auto_execute=True,
    ),
    ActionType.MONITOR: ActionPolicy(
        action_type=ActionType.MONITOR,
        impact_level=ImpactLevel.LOW,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=False,
        min_evidence_count=1,
        min_confidence=0.6,
        max_auto_execute=True,
    ),
    ActionType.ALERT: ActionPolicy(
        action_type=ActionType.ALERT,
        impact_level=ImpactLevel.LOW,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=False,
        min_evidence_count=1,
        min_confidence=0.7,
        max_auto_execute=True,
    ),
    ActionType.LOG: ActionPolicy(
        action_type=ActionType.LOG,
        impact_level=ImpactLevel.LOW,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=False,
        min_evidence_count=1,
        min_confidence=0.5,
        max_auto_execute=True,
    ),
    
    # Containment actions
    ActionType.INCREASE_MONITORING: ActionPolicy(
        action_type=ActionType.INCREASE_MONITORING,
        impact_level=ImpactLevel.MEDIUM,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=False,
        min_evidence_count=2,
        min_confidence=0.7,
        max_auto_execute=True,
    ),
    ActionType.RATE_LIMIT: ActionPolicy(
        action_type=ActionType.RATE_LIMIT,
        impact_level=ImpactLevel.MEDIUM,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=True,
        min_evidence_count=2,
        min_confidence=0.75,
        max_auto_execute=False,
    ),
    ActionType.REQUIRE_MFA: ActionPolicy(
        action_type=ActionType.REQUIRE_MFA,
        impact_level=ImpactLevel.MEDIUM,
        blast_radius=BlastRadius.SEGMENT,
        requires_approval=True,
        min_evidence_count=3,
        min_confidence=0.8,
        max_auto_execute=False,
    ),
    ActionType.NOTIFY_ADMIN: ActionPolicy(
        action_type=ActionType.NOTIFY_ADMIN,
        impact_level=ImpactLevel.MEDIUM,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=False,
        min_evidence_count=2,
        min_confidence=0.7,
        max_auto_execute=True,
    ),
    
    # Enforcement actions
    ActionType.BLOCK_ACCESS: ActionPolicy(
        action_type=ActionType.BLOCK_ACCESS,
        impact_level=ImpactLevel.HIGH,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=True,
        min_evidence_count=3,
        min_confidence=0.85,
        max_auto_execute=False,
    ),
    ActionType.ISOLATE_ENTITY: ActionPolicy(
        action_type=ActionType.ISOLATE_ENTITY,
        impact_level=ImpactLevel.HIGH,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=True,
        min_evidence_count=3,
        min_confidence=0.85,
        max_auto_execute=False,
    ),
    ActionType.QUARANTINE: ActionPolicy(
        action_type=ActionType.QUARANTINE,
        impact_level=ImpactLevel.HIGH,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=True,
        min_evidence_count=4,
        min_confidence=0.9,
        max_auto_execute=False,
    ),
    ActionType.REVOKE_CREDENTIALS: ActionPolicy(
        action_type=ActionType.REVOKE_CREDENTIALS,
        impact_level=ImpactLevel.HIGH,
        blast_radius=BlastRadius.ENTITY_ONLY,
        requires_approval=True,
        min_evidence_count=4,
        min_confidence=0.9,
        max_auto_execute=False,
    ),
    
    # Critical actions
    ActionType.SHUTDOWN_SERVICE: ActionPolicy(
        action_type=ActionType.SHUTDOWN_SERVICE,
        impact_level=ImpactLevel.CRITICAL,
        blast_radius=BlastRadius.ORG_WIDE,
        requires_approval=True,
        min_evidence_count=5,
        min_confidence=0.95,
        max_auto_execute=False,
    ),
    ActionType.EMERGENCY_LOCKDOWN: ActionPolicy(
        action_type=ActionType.EMERGENCY_LOCKDOWN,
        impact_level=ImpactLevel.CRITICAL,
        blast_radius=BlastRadius.ORG_WIDE,
        requires_approval=True,
        min_evidence_count=5,
        min_confidence=0.95,
        max_auto_execute=False,
    ),
}


@dataclass
class ActionRecommendation:
    """Safe action recommendation with evidence."""
    
    action: str  # ActionType value
    target: str
    reason: str
    risk_reduction_estimate: float
    confidence: float
    priority: str
    
    # Safety fields
    approval_required: bool
    blast_radius: str
    impact_level: str
    evidence_count: int
    evidence_call_ids: List[str]
    
    # Validation
    is_valid: bool
    validation_errors: List[str]


class ActionSafetyGate:
    """
    Safety gate for action recommendations.
    
    Validates that:
    - Action type is allow-listed
    - Evidence threshold is met
    - Approval requirements are set
    - Blast radius is estimated
    """
    
    @staticmethod
    def validate_action(
        action: str,
        target: str,
        confidence: float,
        evidence_call_ids: List[str],
    ) -> tuple[bool, List[str]]:
        """
        Validate an action recommendation.
        
        Args:
            action: Action type string
            target: Target entity
            confidence: Confidence score
            evidence_call_ids: List of call IDs from ledger
            
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check if action is allow-listed
        try:
            action_type = ActionType(action)
        except ValueError:
            errors.append(f"Action '{action}' is not allow-listed")
            return False, errors
        
        # Get policy
        policy = ACTION_POLICIES.get(action_type)
        if not policy:
            errors.append(f"No policy found for action '{action}'")
            return False, errors
        
        # Check evidence count
        if len(evidence_call_ids) < policy.min_evidence_count:
            errors.append(
                f"Insufficient evidence: {len(evidence_call_ids)} < {policy.min_evidence_count}"
            )
        
        # Check confidence threshold
        if confidence < policy.min_confidence:
            errors.append(
                f"Confidence too low: {confidence} < {policy.min_confidence}"
            )
        
        # Check target is specified
        if not target or target == "unknown":
            errors.append("Target entity must be specified")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def create_safe_recommendation(
        action: str,
        target: str,
        reason: str,
        risk_reduction_estimate: float,
        confidence: float,
        priority: str,
        evidence_call_ids: List[str],
    ) -> ActionRecommendation:
        """
        Create a safe action recommendation with validation.
        
        Args:
            action: Action type
            target: Target entity
            reason: Human-readable reason
            risk_reduction_estimate: Estimated risk reduction (0.0-1.0)
            confidence: Confidence score (0.0-1.0)
            priority: Priority level
            evidence_call_ids: List of call IDs from ledger
            
        Returns:
            ActionRecommendation with validation results
        """
        # Validate
        is_valid, errors = ActionSafetyGate.validate_action(
            action, target, confidence, evidence_call_ids
        )
        
        # Get policy
        try:
            action_type = ActionType(action)
            policy = ACTION_POLICIES[action_type]
            
            approval_required = policy.requires_approval
            blast_radius = policy.blast_radius.value
            impact_level = policy.impact_level.value
        except (ValueError, KeyError):
            # Invalid action, use safe defaults
            approval_required = True
            blast_radius = BlastRadius.ORG_WIDE.value
            impact_level = ImpactLevel.CRITICAL.value
            is_valid = False
            errors.append("Invalid action type, using safe defaults")
        
        return ActionRecommendation(
            action=action,
            target=target,
            reason=reason,
            risk_reduction_estimate=risk_reduction_estimate,
            confidence=confidence,
            priority=priority,
            approval_required=approval_required,
            blast_radius=blast_radius,
            impact_level=impact_level,
            evidence_count=len(evidence_call_ids),
            evidence_call_ids=evidence_call_ids,
            is_valid=is_valid,
            validation_errors=errors,
        )
    
    @staticmethod
    def get_allowed_actions() -> List[str]:
        """Get list of allowed action types."""
        return [action.value for action in ActionType]
    
    @staticmethod
    def get_action_policy(action: str) -> Optional[ActionPolicy]:
        """Get policy for an action type."""
        try:
            action_type = ActionType(action)
            return ACTION_POLICIES.get(action_type)
        except ValueError:
            return None


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    import json
    
    gate = ActionSafetyGate()
    
    # Example 1: Valid high-impact action
    rec1 = gate.create_safe_recommendation(
        action="isolate_entity",
        target="customer-db",
        reason="High risk score detected with data exposure",
        risk_reduction_estimate=0.35,
        confidence=0.87,
        priority="HIGH",
        evidence_call_ids=["call-1", "call-2", "call-3"],
    )
    
    print("Example 1: Valid high-impact action")
    print(json.dumps({
        "action": rec1.action,
        "target": rec1.target,
        "approval_required": rec1.approval_required,
        "blast_radius": rec1.blast_radius,
        "impact_level": rec1.impact_level,
        "is_valid": rec1.is_valid,
        "errors": rec1.validation_errors,
    }, indent=2))
    
    # Example 2: Invalid action (not allow-listed)
    rec2 = gate.create_safe_recommendation(
        action="delete_everything",
        target="customer-db",
        reason="Bad idea",
        risk_reduction_estimate=0.5,
        confidence=0.9,
        priority="HIGH",
        evidence_call_ids=["call-1"],
    )
    
    print("\nExample 2: Invalid action")
    print(json.dumps({
        "action": rec2.action,
        "is_valid": rec2.is_valid,
        "errors": rec2.validation_errors,
    }, indent=2))
    
    # Example 3: Insufficient evidence
    rec3 = gate.create_safe_recommendation(
        action="isolate_entity",
        target="customer-db",
        reason="High risk",
        risk_reduction_estimate=0.35,
        confidence=0.87,
        priority="HIGH",
        evidence_call_ids=["call-1"],  # Only 1, needs 3
    )
    
    print("\nExample 3: Insufficient evidence")
    print(json.dumps({
        "action": rec3.action,
        "is_valid": rec3.is_valid,
        "errors": rec3.validation_errors,
    }, indent=2))
    
    # List allowed actions
    print("\nAllowed actions:")
    for action in gate.get_allowed_actions():
        policy = gate.get_action_policy(action)
        print(f"  - {action}: {policy.impact_level.value}, requires_approval={policy.requires_approval}")
