# core/output_validator.py
"""
Output Validator - Validate all responses against strict schema.

Prevents LLM hallucinations from reaching users.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of output validation."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class OutputValidator:
    """
    Validates all Dmitry outputs against strict schemas.
    
    Prevents:
    - Invalid action types
    - Missing required fields
    - Out-of-range values
    - Hallucinated evidence
    """
    
    @staticmethod
    def validate_chat_response(response: Dict[str, Any], request_id: str) -> ValidationResult:
        """
        Validate /chat response.
        
        Required fields:
        - answer (str)
        - citations (list)
        - sources (list)
        - confidence (float 0.0-1.0)
        - data_dependencies (list)
        - request_id (str)
        - schema_version (str)
        - producer_version (str)
        """
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = [
            "answer", "citations", "sources", "confidence",
            "data_dependencies", "request_id", "schema_version", "producer_version"
        ]
        
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: {field}")
        
        # Validate types
        if "answer" in response and not isinstance(response["answer"], str):
            errors.append("Field 'answer' must be string")
        
        if "citations" in response and not isinstance(response["citations"], list):
            errors.append("Field 'citations' must be list")
        
        if "sources" in response and not isinstance(response["sources"], list):
            errors.append("Field 'sources' must be list")
        
        if "data_dependencies" in response and not isinstance(response["data_dependencies"], list):
            errors.append("Field 'data_dependencies' must be list")
        
        # Validate confidence
        if "confidence" in response:
            conf = response["confidence"]
            if not isinstance(conf, (int, float)):
                errors.append("Field 'confidence' must be number")
            elif conf < 0.0 or conf > 1.0:
                errors.append(f"Field 'confidence' must be 0.0-1.0, got {conf}")
        
        # Validate request_id matches
        if "request_id" in response and response["request_id"] != request_id:
            errors.append(f"request_id mismatch: expected {request_id}, got {response['request_id']}")
        
        # Validate citations have required fields
        if "citations" in response:
            for i, citation in enumerate(response["citations"]):
                if not isinstance(citation, dict):
                    errors.append(f"Citation {i} must be dict")
                    continue
                
                required_citation_fields = ["call_id", "endpoint", "timestamp"]
                for field in required_citation_fields:
                    if field not in citation:
                        errors.append(f"Citation {i} missing field: {field}")
        
        # Validate sources have required fields
        if "sources" in response:
            for i, source in enumerate(response["sources"]):
                if not isinstance(source, dict):
                    errors.append(f"Source {i} must be dict")
                    continue
                
                required_source_fields = ["type", "endpoint"]
                for field in required_source_fields:
                    if field not in source:
                        errors.append(f"Source {i} missing field: {field}")
        
        # Warnings
        if "answer" in response and len(response["answer"]) < 10:
            warnings.append("Answer is very short (< 10 chars)")
        
        if "citations" in response and len(response["citations"]) == 0:
            warnings.append("No citations provided")
        
        if "confidence" in response and response["confidence"] < 0.5:
            warnings.append(f"Low confidence: {response['confidence']}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    @staticmethod
    def validate_advise_response(response: Dict[str, Any], request_id: str) -> ValidationResult:
        """
        Validate /advise response.
        
        Required fields:
        - recommended_actions (list)
        - reasoning (str)
        - sources (list)
        - confidence (float 0.0-1.0)
        - data_dependencies (list)
        - request_id (str)
        - schema_version (str)
        - producer_version (str)
        """
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = [
            "recommended_actions", "reasoning", "sources", "confidence",
            "data_dependencies", "request_id", "schema_version", "producer_version"
        ]
        
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: {field}")
        
        # Validate types
        if "recommended_actions" in response and not isinstance(response["recommended_actions"], list):
            errors.append("Field 'recommended_actions' must be list")
        
        if "reasoning" in response and not isinstance(response["reasoning"], str):
            errors.append("Field 'reasoning' must be string")
        
        # Validate confidence
        if "confidence" in response:
            conf = response["confidence"]
            if not isinstance(conf, (int, float)):
                errors.append("Field 'confidence' must be number")
            elif conf < 0.0 or conf > 1.0:
                errors.append(f"Field 'confidence' must be 0.0-1.0, got {conf}")
        
        # Validate request_id matches
        if "request_id" in response and response["request_id"] != request_id:
            errors.append(f"request_id mismatch: expected {request_id}, got {response['request_id']}")
        
        # Validate actions
        if "recommended_actions" in response:
            actions = response["recommended_actions"]
            
            if len(actions) == 0:
                warnings.append("No actions recommended")
            
            for i, action in enumerate(actions):
                action_errors = OutputValidator._validate_action(action, i)
                errors.extend(action_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    @staticmethod
    def _validate_action(action: Dict[str, Any], index: int) -> List[str]:
        """Validate a single action."""
        errors = []
        
        if not isinstance(action, dict):
            return [f"Action {index} must be dict"]
        
        # Required fields
        required_fields = [
            "action", "target", "reason", "risk_reduction_estimate",
            "confidence", "priority", "approval_required",
            "blast_radius", "impact_level", "evidence_count"
        ]
        
        for field in required_fields:
            if field not in action:
                errors.append(f"Action {index} missing field: {field}")
        
        # Validate action type (must be from allow-list)
        if "action" in action:
            from core.action_safety import ActionType
            try:
                ActionType(action["action"])
            except ValueError:
                errors.append(f"Action {index} has invalid action type: {action['action']}")
        
        # Validate target
        if "target" in action:
            if not isinstance(action["target"], str):
                errors.append(f"Action {index} target must be string")
            elif action["target"] == "unknown":
                errors.append(f"Action {index} target cannot be 'unknown'")
        
        # Validate risk_reduction_estimate
        if "risk_reduction_estimate" in action:
            rre = action["risk_reduction_estimate"]
            if not isinstance(rre, (int, float)):
                errors.append(f"Action {index} risk_reduction_estimate must be number")
            elif rre < 0.0 or rre > 1.0:
                errors.append(f"Action {index} risk_reduction_estimate must be 0.0-1.0, got {rre}")
        
        # Validate confidence
        if "confidence" in action:
            conf = action["confidence"]
            if not isinstance(conf, (int, float)):
                errors.append(f"Action {index} confidence must be number")
            elif conf < 0.0 or conf > 1.0:
                errors.append(f"Action {index} confidence must be 0.0-1.0, got {conf}")
        
        # Validate priority
        if "priority" in action:
            valid_priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            if action["priority"] not in valid_priorities:
                errors.append(f"Action {index} priority must be one of {valid_priorities}, got {action['priority']}")
        
        # Validate approval_required
        if "approval_required" in action:
            if not isinstance(action["approval_required"], bool):
                errors.append(f"Action {index} approval_required must be boolean")
        
        # Validate blast_radius
        if "blast_radius" in action:
            valid_radii = ["entity_only", "segment", "org_wide"]
            if action["blast_radius"] not in valid_radii:
                errors.append(f"Action {index} blast_radius must be one of {valid_radii}, got {action['blast_radius']}")
        
        # Validate impact_level
        if "impact_level" in action:
            valid_levels = ["low", "medium", "high", "critical"]
            if action["impact_level"] not in valid_levels:
                errors.append(f"Action {index} impact_level must be one of {valid_levels}, got {action['impact_level']}")
        
        # Validate evidence_count
        if "evidence_count" in action:
            if not isinstance(action["evidence_count"], int):
                errors.append(f"Action {index} evidence_count must be integer")
            elif action["evidence_count"] < 0:
                errors.append(f"Action {index} evidence_count cannot be negative")
        
        return errors


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    import json
    
    # Example 1: Valid chat response
    response1 = {
        "answer": "The risk score is 85/100...",
        "citations": [
            {
                "call_id": "abc-123",
                "endpoint": "platform_get_risk_findings",
                "timestamp": "2026-02-19T10:30:00Z"
            }
        ],
        "sources": [
            {
                "type": "platform_api",
                "endpoint": "platform_get_risk_findings"
            }
        ],
        "confidence": 0.87,
        "data_dependencies": ["platform_get_risk_findings"],
        "request_id": "req-123",
        "schema_version": "1.0",
        "producer_version": "1.2"
    }
    
    result1 = OutputValidator.validate_chat_response(response1, "req-123")
    print("Example 1: Valid chat response")
    print(f"Is valid: {result1.is_valid}")
    print(f"Errors: {result1.errors}")
    print(f"Warnings: {result1.warnings}")
    
    # Example 2: Invalid chat response (missing fields)
    response2 = {
        "answer": "The risk score is 85/100...",
        "confidence": 1.5,  # Out of range
    }
    
    result2 = OutputValidator.validate_chat_response(response2, "req-456")
    print("\nExample 2: Invalid chat response")
    print(f"Is valid: {result2.is_valid}")
    print(f"Errors: {result2.errors}")
    
    # Example 3: Valid advise response
    response3 = {
        "recommended_actions": [
            {
                "action": "isolate_entity",
                "target": "customer-db",
                "reason": "High risk",
                "risk_reduction_estimate": 0.35,
                "confidence": 0.85,
                "priority": "HIGH",
                "approval_required": True,
                "blast_radius": "entity_only",
                "impact_level": "high",
                "evidence_count": 3
            }
        ],
        "reasoning": "Based on high risk score...",
        "sources": [],
        "confidence": 0.82,
        "data_dependencies": [],
        "request_id": "req-789",
        "schema_version": "1.0",
        "producer_version": "1.2"
    }
    
    result3 = OutputValidator.validate_advise_response(response3, "req-789")
    print("\nExample 3: Valid advise response")
    print(f"Is valid: {result3.is_valid}")
    print(f"Errors: {result3.errors}")
    print(f"Warnings: {result3.warnings}")
    
    # Example 4: Invalid action
    response4 = {
        "recommended_actions": [
            {
                "action": "delete_everything",  # Not in allow-list
                "target": "unknown",  # Invalid target
                "reason": "Bad idea",
                "risk_reduction_estimate": 1.5,  # Out of range
                "confidence": 0.9,
                "priority": "SUPER_HIGH",  # Invalid priority
                "approval_required": "yes",  # Wrong type
                "blast_radius": "universe",  # Invalid
                "impact_level": "catastrophic",  # Invalid
                "evidence_count": -1  # Negative
            }
        ],
        "reasoning": "...",
        "sources": [],
        "confidence": 0.8,
        "data_dependencies": [],
        "request_id": "req-101",
        "schema_version": "1.0",
        "producer_version": "1.2"
    }
    
    result4 = OutputValidator.validate_advise_response(response4, "req-101")
    print("\nExample 4: Invalid action")
    print(f"Is valid: {result4.is_valid}")
    print(f"Errors ({len(result4.errors)}):")
    for error in result4.errors:
        print(f"  - {error}")
