#!/usr/bin/env python3
"""
Complete Loop Test - Verify Dmitry is 100% production ready.

Tests:
1. Input sanitation
2. Call ledger
3. Action safety
4. Evidence chain
5. Structured actions
6. Output validation
"""

import json
import sys


def test_input_sanitation():
    """Test input sanitation."""
    print("\n" + "="*60)
    print("TEST 1: Input Sanitation")
    print("="*60)
    
    from core.input_sanitizer import InputSanitizer
    
    # Test with secrets
    context = {
        "entity_id": "customer-db",
        "api_key": "sk_live_secret123",
        "password": "MyPassword123",
        "user_email": "john.doe@example.com"
    }
    
    result = InputSanitizer.sanitize_context(context)
    
    print(f"✓ Is safe: {result.is_safe}")
    print(f"✓ Redacted fields: {result.redacted_fields}")
    print(f"✓ Sanitized data: {json.dumps(result.sanitized_data, indent=2)}")
    
    # Verify secrets are redacted
    assert result.sanitized_data["api_key"] == "***REDACTED***"
    assert result.sanitized_data["password"] == "***REDACTED***"
    assert "[EMAIL_REDACTED]" in result.sanitized_data["user_email"]
    
    print("✅ Input sanitation PASSED")
    return True


def test_call_ledger():
    """Test call ledger."""
    print("\n" + "="*60)
    print("TEST 2: Call Ledger")
    print("="*60)
    
    from core.call_ledger import get_call_ledger, record_platform_call
    
    ledger = get_call_ledger()
    
    # Record a call
    call_id = record_platform_call(
        endpoint="platform_get_risk_findings",
        args={"filters": {"risk_level": "HIGH"}},
        response={"findings": [{"id": "f1", "score": 85}], "total": 1},
        status="success",
        latency_ms=245,
        request_id="test-req-001"
    )
    
    print(f"✓ Recorded call: {call_id}")
    
    # Verify citation
    valid = ledger.verify_citation(call_id, "platform_get_risk_findings")
    print(f"✓ Citation valid: {valid}")
    assert valid
    
    # Try to fabricate
    fake_valid = ledger.verify_citation("fake-id", "platform_get_risk_findings")
    print(f"✓ Fake citation rejected: {not fake_valid}")
    assert not fake_valid
    
    # Get citations
    citations = ledger.get_citations_for_request("test-req-001")
    print(f"✓ Citations retrieved: {len(citations)}")
    assert len(citations) == 1
    
    print("✅ Call ledger PASSED")
    return True


def test_action_safety():
    """Test action safety gate."""
    print("\n" + "="*60)
    print("TEST 3: Action Safety Gate")
    print("="*60)
    
    from core.action_safety import ActionSafetyGate
    
    gate = ActionSafetyGate()
    
    # Test valid action
    rec1 = gate.create_safe_recommendation(
        action="isolate_entity",
        target="customer-db",
        reason="High risk detected",
        risk_reduction_estimate=0.35,
        confidence=0.87,
        priority="HIGH",
        evidence_call_ids=["call-1", "call-2", "call-3"]
    )
    
    print(f"✓ Valid action: {rec1.action}")
    print(f"✓ Approval required: {rec1.approval_required}")
    print(f"✓ Blast radius: {rec1.blast_radius}")
    print(f"✓ Is valid: {rec1.is_valid}")
    assert rec1.is_valid
    
    # Test invalid action
    rec2 = gate.create_safe_recommendation(
        action="delete_everything",
        target="customer-db",
        reason="Bad idea",
        risk_reduction_estimate=0.5,
        confidence=0.9,
        priority="HIGH",
        evidence_call_ids=["call-1"]
    )
    
    print(f"✓ Invalid action rejected: {not rec2.is_valid}")
    print(f"✓ Errors: {rec2.validation_errors}")
    assert not rec2.is_valid
    
    # Test insufficient evidence
    rec3 = gate.create_safe_recommendation(
        action="isolate_entity",
        target="customer-db",
        reason="High risk",
        risk_reduction_estimate=0.35,
        confidence=0.87,
        priority="HIGH",
        evidence_call_ids=["call-1"]  # Only 1, needs 3
    )
    
    print(f"✓ Insufficient evidence rejected: {not rec3.is_valid}")
    assert not rec3.is_valid
    
    print("✅ Action safety gate PASSED")
    return True


def test_evidence_chain():
    """Test evidence chain."""
    print("\n" + "="*60)
    print("TEST 4: Evidence Chain")
    print("="*60)
    
    from core.evidence_chain import build_evidence_chain, validate_evidence_chain
    from core.call_ledger import record_platform_call
    
    # Record some calls
    request_id = "test-req-002"
    call_id1 = record_platform_call(
        endpoint="platform_get_risk_findings",
        args={},
        response={"findings": []},
        status="success",
        latency_ms=100,
        request_id=request_id
    )
    
    # Build complete chain
    context = {
        "event_id": "evt-123",
        "finding_id": "find-456",
        "entity_id": "customer-db"
    }
    
    chain = build_evidence_chain(context, request_id)
    
    print(f"✓ Event ID: {chain.event_id}")
    print(f"✓ Finding ID: {chain.finding_id}")
    print(f"✓ Call IDs: {chain.call_ids}")
    print(f"✓ Chain complete: {chain.chain_complete}")
    
    assert chain.chain_complete
    assert chain.event_id == "evt-123"
    assert chain.finding_id == "find-456"
    assert len(chain.call_ids) > 0
    
    # Validate chain
    is_valid, errors = validate_evidence_chain(chain)
    print(f"✓ Chain valid: {is_valid}")
    assert is_valid
    
    print("✅ Evidence chain PASSED")
    return True


def test_structured_actions():
    """Test structured action parsing."""
    print("\n" + "="*60)
    print("TEST 5: Structured Actions")
    print("="*60)
    
    from core.structured_actions import parse_structured_actions
    
    # Test JSON parsing
    llm_output_json = """
[
  {
    "action": "isolate_entity",
    "target": "customer-db",
    "reason": "High risk score detected",
    "risk_reduction_estimate": 0.35,
    "confidence": 0.87,
    "priority": "HIGH"
  }
]
"""
    
    context = {"entity_id": "customer-db", "risk_score": 85}
    actions_json = parse_structured_actions(llm_output_json, context, ["call-1", "call-2", "call-3"])
    
    print(f"✓ JSON parsing: {len(actions_json)} actions")
    assert len(actions_json) > 0
    assert actions_json[0]["action"] == "isolate_entity"
    assert "approval_required" in actions_json[0]
    assert "blast_radius" in actions_json[0]
    
    # Test text fallback
    llm_output_text = """
I recommend:
1. Isolate the customer-db entity
2. Increase monitoring
"""
    
    actions_text = parse_structured_actions(llm_output_text, context, ["call-1", "call-2"])
    
    print(f"✓ Text fallback: {len(actions_text)} actions")
    assert len(actions_text) > 0
    
    print("✅ Structured actions PASSED")
    return True


def test_output_validation():
    """Test output validation."""
    print("\n" + "="*60)
    print("TEST 6: Output Validation")
    print("="*60)
    
    from core.output_validator import OutputValidator
    
    # Test valid response
    response_valid = {
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
    
    result_valid = OutputValidator.validate_chat_response(response_valid, "req-123")
    print(f"✓ Valid response: {result_valid.is_valid}")
    assert result_valid.is_valid
    
    # Test invalid response
    response_invalid = {
        "answer": "Test",
        "confidence": 1.5,  # Out of range
    }
    
    result_invalid = OutputValidator.validate_chat_response(response_invalid, "req-456")
    print(f"✓ Invalid response rejected: {not result_invalid.is_valid}")
    print(f"✓ Errors: {len(result_invalid.errors)}")
    assert not result_invalid.is_valid
    
    print("✅ Output validation PASSED")
    return True


def test_complete_loop():
    """Test complete loop integration."""
    print("\n" + "="*60)
    print("TEST 7: Complete Loop Integration")
    print("="*60)
    
    from core.input_sanitizer import InputSanitizer
    from core.call_ledger import record_platform_call
    from core.evidence_chain import build_evidence_chain, enrich_actions_with_evidence
    from core.structured_actions import parse_structured_actions
    from core.output_validator import OutputValidator
    
    # 1. Sanitize input
    context = {
        "event_id": "evt-789",
        "finding_id": "find-101",
        "entity_id": "customer-db",
        "risk_score": 85,
        "api_key": "secret123"  # Should be redacted
    }
    
    sanitization = InputSanitizer.sanitize_context(context)
    assert sanitization.is_safe
    context = sanitization.sanitized_data
    print("✓ Step 1: Input sanitized")
    
    # 2. Record Platform calls
    request_id = "test-req-complete"
    call_id = record_platform_call(
        endpoint="platform_get_risk_findings",
        args={"entity_id": "customer-db"},
        response={"findings": [{"score": 85}]},
        status="success",
        latency_ms=200,
        request_id=request_id
    )
    print(f"✓ Step 2: Platform call recorded ({call_id})")
    
    # 3. Build evidence chain
    chain = build_evidence_chain(context, request_id)
    assert chain.chain_complete
    print(f"✓ Step 3: Evidence chain built (complete: {chain.chain_complete})")
    
    # 4. Parse actions
    llm_output = """
[
  {
    "action": "isolate_entity",
    "target": "customer-db",
    "reason": "High risk with data exposure",
    "risk_reduction_estimate": 0.35,
    "confidence": 0.87,
    "priority": "HIGH"
  }
]
"""
    actions = parse_structured_actions(llm_output, context, [call_id])
    assert len(actions) > 0
    print(f"✓ Step 4: Actions parsed ({len(actions)} actions)")
    
    # 5. Enrich with evidence
    actions = enrich_actions_with_evidence(actions, chain)
    assert "evidence_required" in actions[0]
    print(f"✓ Step 5: Actions enriched with evidence")
    
    # 6. Build response
    response = {
        "answer": "High risk detected on customer-db",
        "citations": [
            {
                "call_id": call_id,
                "endpoint": "platform_get_risk_findings",
                "timestamp": "2026-02-19T10:30:00Z"
            }
        ],
        "recommended_actions": actions,
        "sources": [
            {
                "type": "platform_api",
                "endpoint": "platform_get_risk_findings"
            }
        ],
        "confidence": 0.87,
        "data_dependencies": ["platform_get_risk_findings"],
        "evidence_chain": chain.to_dict(),
        "request_id": request_id,
        "schema_version": "1.0",
        "producer_version": "1.2"
    }
    print("✓ Step 6: Response built")
    
    # 7. Validate output
    validation = OutputValidator.validate_chat_response(response, request_id)
    assert validation.is_valid
    print(f"✓ Step 7: Output validated (valid: {validation.is_valid})")
    
    # 8. Verify evidence chain
    assert response["evidence_chain"]["event_id"] == "evt-789"
    assert response["evidence_chain"]["finding_id"] == "find-101"
    assert len(response["evidence_chain"]["call_ids"]) > 0
    print("✓ Step 8: Evidence chain verified")
    
    # 9. Verify actions have evidence
    assert "evidence_required" in response["recommended_actions"][0]
    assert "evt-789" in response["recommended_actions"][0]["evidence_required"]
    assert "find-101" in response["recommended_actions"][0]["evidence_required"]
    print("✓ Step 9: Actions have evidence references")
    
    print("\n✅ COMPLETE LOOP PASSED")
    print("\nEvidence chain:")
    print(f"  Event: {response['evidence_chain']['event_id']}")
    print(f"  → Finding: {response['evidence_chain']['finding_id']}")
    print(f"  → Platform calls: {len(response['evidence_chain']['call_ids'])}")
    print(f"  → Actions: {len(response['recommended_actions'])}")
    print(f"  → Evidence in actions: {len(response['recommended_actions'][0]['evidence_required'])}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DMITRY 100% PRODUCTION READINESS TEST")
    print("="*60)
    
    tests = [
        ("Input Sanitation", test_input_sanitation),
        ("Call Ledger", test_call_ledger),
        ("Action Safety", test_action_safety),
        ("Evidence Chain", test_evidence_chain),
        ("Structured Actions", test_structured_actions),
        ("Output Validation", test_output_validation),
        ("Complete Loop", test_complete_loop),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - DMITRY IS 100% PRODUCTION READY")
        return 0
    else:
        print(f"\n❌ {failed} TESTS FAILED - FIX BEFORE PRODUCTION")
        return 1


if __name__ == "__main__":
    sys.exit(main())
