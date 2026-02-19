# core/structured_actions.py
"""
Structured Action Parser - Parse LLM output as JSON, not text.

Reliable action extraction with fallback to text parsing.
"""

import json
import re
from typing import Dict, Any, List
from core.action_safety import ActionSafetyGate


def parse_structured_actions(
    llm_output: str,
    context: Dict[str, Any],
    evidence_call_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Parse actions from LLM output (JSON preferred, text fallback).
    
    Args:
        llm_output: LLM response text
        context: Request context
        evidence_call_ids: Call IDs from ledger
        
    Returns:
        List of validated action recommendations
    """
    # Try JSON parsing first
    actions = _try_json_parse(llm_output, context, evidence_call_ids)
    
    if actions:
        return actions
    
    # Fallback to text parsing
    return _fallback_text_parse(llm_output, context, evidence_call_ids)


def _try_json_parse(
    llm_output: str,
    context: Dict[str, Any],
    evidence_call_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Try to parse LLM output as JSON.
    
    Returns:
        List of actions, or empty list if parsing fails
    """
    actions = []
    
    # Look for JSON array in output
    json_match = re.search(r'\[[\s\S]*\]', llm_output)
    if not json_match:
        return []
    
    try:
        json_str = json_match.group(0)
        actions_data = json.loads(json_str)
        
        if not isinstance(actions_data, list):
            return []
        
        # Validate and create safe recommendations
        for action_data in actions_data:
            if not isinstance(action_data, dict):
                continue
            
            # Extract fields with defaults
            action = action_data.get("action", "investigate")
            target = action_data.get("target", context.get("entity_id", "unknown"))
            reason = action_data.get("reason", "No reason provided")
            risk_reduction = action_data.get("risk_reduction_estimate", 0.2)
            confidence = action_data.get("confidence", 0.7)
            priority = action_data.get("priority", "MEDIUM")
            
            # Create safe recommendation
            rec = ActionSafetyGate.create_safe_recommendation(
                action=action,
                target=target,
                reason=reason,
                risk_reduction_estimate=risk_reduction,
                confidence=confidence,
                priority=priority,
                evidence_call_ids=evidence_call_ids,
            )
            
            if rec.is_valid:
                actions.append({
                    "action": rec.action,
                    "target": rec.target,
                    "reason": rec.reason,
                    "risk_reduction_estimate": rec.risk_reduction_estimate,
                    "confidence": rec.confidence,
                    "priority": rec.priority,
                    "approval_required": rec.approval_required,
                    "blast_radius": rec.blast_radius,
                    "impact_level": rec.impact_level,
                    "evidence_count": rec.evidence_count,
                })
        
        return actions
        
    except json.JSONDecodeError:
        return []


def _fallback_text_parse(
    llm_output: str,
    context: Dict[str, Any],
    evidence_call_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Fallback text parsing when JSON fails.
    
    Returns:
        List of actions parsed from text
    """
    actions = []
    lines = llm_output.split("\n")
    
    for line in lines:
        line_lower = line.lower()
        
        # Skip lines without action keywords
        if not any(word in line_lower for word in ["recommend", "suggest", "should", "action"]):
            continue
        
        # Detect action type
        action_type = None
        if "isolate" in line_lower:
            action_type = "isolate_entity"
            risk_reduction = 0.4
            priority = "HIGH"
        elif "block" in line_lower:
            action_type = "block_access"
            risk_reduction = 0.35
            priority = "HIGH"
        elif "quarantine" in line_lower:
            action_type = "quarantine"
            risk_reduction = 0.45
            priority = "HIGH"
        elif "monitor" in line_lower:
            action_type = "increase_monitoring"
            risk_reduction = 0.15
            priority = "MEDIUM"
        elif "alert" in line_lower or "notify" in line_lower:
            action_type = "alert"
            risk_reduction = 0.1
            priority = "LOW"
        elif "investigate" in line_lower:
            action_type = "investigate"
            risk_reduction = 0.25
            priority = "MEDIUM"
        
        if not action_type:
            continue
        
        # Create safe recommendation
        rec = ActionSafetyGate.create_safe_recommendation(
            action=action_type,
            target=context.get("entity_id", "unknown"),
            reason=line.strip(),
            risk_reduction_estimate=risk_reduction,
            confidence=0.7,
            priority=priority,
            evidence_call_ids=evidence_call_ids,
        )
        
        if rec.is_valid:
            actions.append({
                "action": rec.action,
                "target": rec.target,
                "reason": rec.reason,
                "risk_reduction_estimate": rec.risk_reduction_estimate,
                "confidence": rec.confidence,
                "priority": rec.priority,
                "approval_required": rec.approval_required,
                "blast_radius": rec.blast_radius,
                "impact_level": rec.impact_level,
                "evidence_count": rec.evidence_count,
            })
    
    # If no actions found and high risk, provide default
    if not actions and context.get("risk_score", 0) > 70:
        rec = ActionSafetyGate.create_safe_recommendation(
            action="investigate",
            target=context.get("entity_id", "unknown"),
            reason="High risk score detected, investigation recommended",
            risk_reduction_estimate=0.25,
            confidence=0.8,
            priority="HIGH",
            evidence_call_ids=evidence_call_ids,
        )
        
        if rec.is_valid:
            actions.append({
                "action": rec.action,
                "target": rec.target,
                "reason": rec.reason,
                "risk_reduction_estimate": rec.risk_reduction_estimate,
                "confidence": rec.confidence,
                "priority": rec.priority,
                "approval_required": rec.approval_required,
                "blast_radius": rec.blast_radius,
                "impact_level": rec.impact_level,
                "evidence_count": rec.evidence_count,
            })
    
    return actions


def get_structured_prompt_suffix() -> str:
    """
    Get prompt suffix to request structured JSON output.
    
    Returns:
        Prompt text to append to LLM requests
    """
    return """

IMPORTANT: Respond with a JSON array of action recommendations. Each action must have:
- action: one of (investigate, monitor, alert, increase_monitoring, block_access, isolate_entity, quarantine)
- target: entity identifier
- reason: brief explanation
- risk_reduction_estimate: number 0.0-1.0
- confidence: number 0.0-1.0
- priority: one of (LOW, MEDIUM, HIGH, CRITICAL)

Example:
[
  {
    "action": "isolate_entity",
    "target": "customer-db",
    "reason": "High risk score with data exposure",
    "risk_reduction_estimate": 0.35,
    "confidence": 0.85,
    "priority": "HIGH"
  }
]
"""


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    import json
    
    # Example 1: JSON output (preferred)
    llm_output1 = """
Based on the analysis, I recommend:

[
  {
    "action": "isolate_entity",
    "target": "customer-db",
    "reason": "High risk score (85/100) with data exposure threat",
    "risk_reduction_estimate": 0.35,
    "confidence": 0.87,
    "priority": "HIGH"
  },
  {
    "action": "increase_monitoring",
    "target": "customer-db",
    "reason": "Monitor for further suspicious activity",
    "risk_reduction_estimate": 0.15,
    "confidence": 0.90,
    "priority": "MEDIUM"
  }
]
"""
    
    context1 = {
        "entity_id": "customer-db",
        "risk_score": 85
    }
    
    actions1 = parse_structured_actions(llm_output1, context1, ["call-1", "call-2", "call-3"])
    
    print("Example 1: JSON output (preferred)")
    print(json.dumps(actions1, indent=2))
    
    # Example 2: Text output (fallback)
    llm_output2 = """
Based on the high risk score, I recommend:

1. Isolate the customer-db entity to prevent further exposure
2. Increase monitoring on all related systems
3. Alert the security team immediately
"""
    
    actions2 = parse_structured_actions(llm_output2, context1, ["call-1", "call-2"])
    
    print("\nExample 2: Text output (fallback)")
    print(json.dumps(actions2, indent=2))
    
    # Example 3: Get prompt suffix
    prompt_suffix = get_structured_prompt_suffix()
    print("\nExample 3: Prompt suffix to request JSON")
    print(prompt_suffix)
