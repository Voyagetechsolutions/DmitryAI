# core/evidence_chain.py
"""
Evidence Chain - Links event → finding → action with proof.

Provides traceability: "This event triggered this finding which led to this action."
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class EvidenceChain:
    """Complete evidence chain linking event to action."""
    
    event_id: Optional[str]
    finding_id: Optional[str]
    call_ids: List[str]
    correlation_id: Optional[str]
    chain_complete: bool
    missing_links: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "event_id": self.event_id,
            "finding_id": self.finding_id,
            "call_ids": self.call_ids,
            "correlation_id": self.correlation_id,
            "chain_complete": self.chain_complete,
            "missing_links": self.missing_links if self.missing_links else None,
        }


def build_evidence_chain(
    context: Dict[str, Any],
    request_id: str
) -> EvidenceChain:
    """
    Build evidence chain linking event → finding → actions.
    
    Args:
        context: Request context with event_id, finding_id, etc.
        request_id: Request trace ID
        
    Returns:
        EvidenceChain with complete traceability
    """
    from core.call_ledger import get_call_ledger
    
    # Extract IDs from context
    event_id = context.get("event_id")
    finding_id = context.get("finding_id")
    correlation_id = context.get("correlation_id")
    
    # Get all Platform calls for this request
    ledger = get_call_ledger()
    records = ledger.get_records_for_request(request_id)
    call_ids = [r.call_id for r in records]
    
    # Check chain completeness
    missing_links = []
    
    if not event_id:
        missing_links.append("event_id")
    
    if not finding_id:
        missing_links.append("finding_id")
    
    if not call_ids:
        missing_links.append("platform_calls")
    
    chain_complete = len(missing_links) == 0
    
    return EvidenceChain(
        event_id=event_id,
        finding_id=finding_id,
        call_ids=call_ids,
        correlation_id=correlation_id,
        chain_complete=chain_complete,
        missing_links=missing_links,
    )


def validate_evidence_chain(chain: EvidenceChain) -> tuple[bool, List[str]]:
    """
    Validate that evidence chain is complete and verifiable.
    
    Args:
        chain: Evidence chain to validate
        
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    # Check required fields
    if not chain.event_id:
        errors.append("Missing event_id - cannot trace to originating event")
    
    if not chain.finding_id:
        errors.append("Missing finding_id - cannot trace to risk finding")
    
    if not chain.call_ids:
        errors.append("Missing call_ids - no Platform API calls recorded")
    
    # Verify call_ids exist in ledger
    if chain.call_ids:
        from core.call_ledger import get_call_ledger
        ledger = get_call_ledger()
        
        for call_id in chain.call_ids:
            record = ledger.get_record(call_id)
            if not record:
                errors.append(f"call_id {call_id} not found in ledger")
    
    return len(errors) == 0, errors


def get_evidence_summary(chain: EvidenceChain) -> str:
    """
    Generate human-readable evidence summary.
    
    Args:
        chain: Evidence chain
        
    Returns:
        Summary text
    """
    if chain.chain_complete:
        return (
            f"Complete evidence chain: "
            f"Event {chain.event_id} → "
            f"Finding {chain.finding_id} → "
            f"{len(chain.call_ids)} Platform API calls"
        )
    else:
        missing = ", ".join(chain.missing_links)
        return f"Incomplete evidence chain (missing: {missing})"


def enrich_actions_with_evidence(
    actions: List[Dict[str, Any]],
    chain: EvidenceChain
) -> List[Dict[str, Any]]:
    """
    Enrich actions with evidence chain references.
    
    Args:
        actions: List of action recommendations
        chain: Evidence chain
        
    Returns:
        Actions with evidence_required field
    """
    enriched = []
    
    for action in actions:
        enriched_action = action.copy()
        
        # Build evidence_required list
        evidence_required = []
        
        if chain.event_id:
            evidence_required.append(chain.event_id)
        
        if chain.finding_id:
            evidence_required.append(chain.finding_id)
        
        # Add call_ids as evidence
        evidence_required.extend(chain.call_ids)
        
        enriched_action["evidence_required"] = evidence_required
        
        enriched.append(enriched_action)
    
    return enriched


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    import json
    
    # Example 1: Complete chain
    context1 = {
        "event_id": "evt-123",
        "finding_id": "find-456",
        "entity_id": "customer-db",
        "correlation_id": "corr-789"
    }
    
    # Mock request_id (in real usage, this comes from server)
    request_id1 = "req-001"
    
    # Build chain
    chain1 = build_evidence_chain(context1, request_id1)
    
    print("Example 1: Complete chain")
    print(json.dumps(chain1.to_dict(), indent=2))
    print(f"Summary: {get_evidence_summary(chain1)}")
    
    # Validate
    is_valid, errors = validate_evidence_chain(chain1)
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    
    # Example 2: Incomplete chain (missing event_id)
    context2 = {
        "finding_id": "find-456",
        "entity_id": "customer-db"
    }
    
    chain2 = build_evidence_chain(context2, "req-002")
    
    print("\nExample 2: Incomplete chain")
    print(json.dumps(chain2.to_dict(), indent=2))
    print(f"Summary: {get_evidence_summary(chain2)}")
    
    # Example 3: Enrich actions with evidence
    actions = [
        {
            "action": "isolate_entity",
            "target": "customer-db",
            "reason": "High risk",
            "confidence": 0.85
        }
    ]
    
    enriched_actions = enrich_actions_with_evidence(actions, chain1)
    
    print("\nExample 3: Actions enriched with evidence")
    print(json.dumps(enriched_actions, indent=2))
