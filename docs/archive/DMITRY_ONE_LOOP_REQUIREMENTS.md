# Dmitry: ONE Complete Loop Requirements

**Focus**: What Dmitry needs to prove the system works  
**Time**: 5 days  
**Goal**: ONE working flow, not perfect components

---

## The Loop (Dmitry's Part)

```
Platform sends:
{
  "event_id": "evt-123",           # From Aegis
  "finding_id": "find-456",        # From PDRI
  "entity_id": "customer-db",
  "risk_score": 85,
  "threat_type": "data_exposure"
}

Dmitry processes:
1. ✅ Sanitizes input (done)
2. ✅ Calls Platform APIs (done, recorded in ledger)
3. ❌ Builds evidence chain (MISSING)
4. ❌ Generates structured actions (MISSING - currently text parsing)
5. ✅ Validates output (done)
6. ✅ Returns with proof (done - call_ids from ledger)

Platform receives:
{
  "recommended_actions": [
    {
      "action": "isolate_entity",
      "target": "customer-db",
      "approval_required": true,
      "blast_radius": "entity_only",
      "evidence_required": ["evt-123", "find-456", "call-1", "call-2"]
    }
  ],
  "evidence_chain": {
    "event_id": "evt-123",
    "finding_id": "find-456",
    "call_ids": ["call-1", "call-2"],
    "correlation_id": "corr-789"
  }
}
```

---

## What's Missing for ONE Loop

### 1. Evidence Chain (CRITICAL)

**File**: `MarkX/core/evidence_chain.py` (NOT CREATED)

**What it does**:
```python
def build_evidence_chain(
    context: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    """
    Build evidence chain linking event → finding → actions.
    
    Args:
        context: Request context with event_id, finding_id
        request_id: Request trace ID
        
    Returns:
        {
            "event_id": "evt-123",
            "finding_id": "find-456",
            "call_ids": ["call-1", "call-2"],
            "correlation_id": "corr-789",
            "chain_complete": true
        }
    """
    from core.call_ledger import get_call_ledger
    
    ledger = get_call_ledger()
    records = ledger.get_records_for_request(request_id)
    
    return {
        "event_id": context.get("event_id"),
        "finding_id": context.get("finding_id"),
        "call_ids": [r.call_id for r in records],
        "correlation_id": context.get("correlation_id"),
        "chain_complete": all([
            context.get("event_id"),
            context.get("finding_id"),
            len(records) > 0
        ])
    }
```

**Integration**: Add to `server.py` responses:
```python
response["evidence_chain"] = build_evidence_chain(context, request_id)
```

---

### 2. Structured Action Output (CRITICAL)

**Current Problem**: Actions parsed from LLM text with string matching.

**Solution**: LLM outputs JSON, validate against schema.

**Update**: `MarkX/agent/server.py` - `_parse_action_recommendations()`

**Before** (text parsing):
```python
if "isolate" in line_lower:
    action = "isolate_entity"
```

**After** (JSON output):
```python
# Update LLM prompt to request JSON
prompt += "\n\nOutput format: JSON array of actions with fields: action, target, reason"

# Parse JSON
try:
    actions_json = json.loads(result.content)
    for action_data in actions_json:
        rec = ActionSafetyGate.create_safe_recommendation(
            action=action_data["action"],
            target=action_data["target"],
            reason=action_data["reason"],
            ...
        )
except json.JSONDecodeError:
    # Fallback to text parsing
    ...
```

---

### 3. Real Explainability (NICE TO HAVE)

**File**: `MarkX/core/explainer.py` (NOT CREATED)

**What it does**:
```python
def explain_decision(request_id: str) -> Dict[str, Any]:
    """
    Generate real explanation from ledger analysis.
    
    Returns:
        {
            "decision_path": "risk_score > 80 AND exposure_detected → isolate",
            "evidence_used": ["call-1", "call-2"],
            "risk_factors": ["high_score", "data_exposure"],
            "confidence_basis": "3 evidence pieces, all successful calls"
        }
    """
    from core.call_ledger import get_call_ledger
    
    ledger = get_call_ledger()
    records = ledger.get_records_for_request(request_id)
    
    # Analyze ledger calls
    risk_factors = []
    for record in records:
        if "risk" in record.endpoint:
            # Extract risk factors from response
            summary = record.response_summary
            if summary.get("total", 0) > 0:
                risk_factors.append("high_risk_findings")
    
    return {
        "decision_path": "Based on ledger analysis...",
        "evidence_used": [r.call_id for r in records],
        "risk_factors": risk_factors,
        "confidence_basis": f"{len(records)} evidence pieces"
    }
```

---

## 5-Day Implementation Plan

### Day 1: Evidence Chain
**File**: `MarkX/core/evidence_chain.py`
- Create `build_evidence_chain()` function
- Integrate into `/chat` and `/advise` responses
- Test with mock event_id and finding_id

### Day 2: Evidence Chain Integration
**File**: `MarkX/agent/server.py`
- Add `evidence_chain` to all responses
- Validate chain completeness
- Test end-to-end

### Day 3: Structured Actions
**File**: `MarkX/agent/server.py`
- Update LLM prompt to request JSON
- Parse JSON instead of text
- Fallback to text parsing if JSON fails
- Test with various inputs

### Day 4-5: Real Explainability (Optional)
**File**: `MarkX/core/explainer.py`
- Create `explain_decision()` function
- Analyze ledger for decision path
- Integrate into responses
- Test with real ledger data

---

## Minimum Viable Loop (3 Days)

If you only have 3 days, skip explainability and focus on:

### Day 1: Evidence Chain
- Create `evidence_chain.py`
- Integrate into responses

### Day 2: Structured Actions
- Update LLM prompt for JSON
- Parse JSON, validate

### Day 3: End-to-End Test
- Mock Platform sending event + finding
- Dmitry processes with evidence chain
- Validate output
- Confirm loop works

---

## Test Scenario (ONE Complete Loop)

### Input (from Platform):
```json
{
  "message": "Analyze this security incident",
  "context": {
    "event_id": "evt-123",
    "finding_id": "find-456",
    "entity_id": "customer-db",
    "risk_score": 85,
    "threat_type": "data_exposure"
  }
}
```

### Expected Output (to Platform):
```json
{
  "answer": "customer-db has high risk (85/100) due to data exposure...",
  "citations": [
    {
      "call_id": "call-1",
      "endpoint": "platform_get_risk_findings",
      "args_hash": "sha256...",
      "response_hash": "sha256...",
      "status": "success"
    }
  ],
  "recommended_actions": [
    {
      "action": "isolate_entity",
      "target": "customer-db",
      "reason": "High risk score with data exposure threat",
      "approval_required": true,
      "blast_radius": "entity_only",
      "evidence_count": 2
    }
  ],
  "evidence_chain": {
    "event_id": "evt-123",
    "finding_id": "find-456",
    "call_ids": ["call-1"],
    "chain_complete": true
  },
  "confidence": 0.87,
  "request_id": "req-789"
}
```

### Validation:
- ✅ Input sanitized (no secrets/PII leaked)
- ✅ Citations from ledger (call_id verified)
- ✅ Actions validated (in allow-list, evidence threshold met)
- ✅ Evidence chain complete (event → finding → action)
- ✅ Output validated (schema correct)

---

## Success Criteria

### Dmitry can prove:
1. ✅ This event (evt-123) triggered this analysis
2. ✅ This finding (find-456) informed this decision
3. ✅ These Platform calls (call-1, call-2) provided evidence
4. ✅ This action (isolate_entity) is safe and justified
5. ✅ This evidence chain is complete and verifiable

### Dmitry cannot:
- ❌ Fabricate citations (ledger prevents it)
- ❌ Recommend invalid actions (safety gate prevents it)
- ❌ Leak PII (redaction prevents it)
- ❌ Return malformed data (validation prevents it)

---

## Bottom Line

**Dmitry needs 2 things for ONE complete loop:**

1. **Evidence Chain** (2 days)
   - Links event → finding → action
   - Proves traceability

2. **Structured Actions** (1 day)
   - JSON output, not text parsing
   - Reliable action extraction

**Total**: 3 days to ONE working loop

**Then**: Build Platform around this proven loop

---

**Status**: 70% Ready  
**Blockers**: 2 (evidence chain, structured actions)  
**Time to Loop**: 3 days  
**Priority**: Stop adding features, prove the loop works
