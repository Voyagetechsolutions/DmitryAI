# Dmitry Reality Check - What's Actually Missing

**Date**: 2026-02-19  
**Brutal Truth**: Dmitry has features, not trust

---

## What Dmitry Actually Has ✅

1. ✅ Call ledger (immutable, cryptographic hashes)
2. ✅ Action safety gate (allow-list, evidence thresholds)
3. ✅ PII redaction
4. ✅ Platform client with circuit breaker
5. ✅ JWT auth with service roles

---

## What Dmitry Is MISSING 🔴

### 1. Real Explainability (Not LLM Fluff)

**Current State**:
```python
# server.py extracts "reasoning" from LLM output
reasoning = result.content.split(".")[0] + "."
```

**Problem**: This is LLM-generated fluff, not real reasoning.

**What's Needed**:
```python
# Reasoning MUST come from ledger analysis
reasoning = {
    "called_endpoints": ["platform_get_risk_findings", "platform_search_entities"],
    "evidence_count": 3,
    "risk_factors": ["high_score", "data_exposure", "recent_incidents"],
    "decision_path": "risk_score > 80 AND exposure_detected → recommend_isolation"
}
```

**Where to Fix**: `MarkX/agent/server.py` - `_extract_reasoning()` method

---

### 2. Input Sanitation (Treat All Text as Untrusted)

**Current State**: Context is passed directly to LLM without validation.

**Problem**: Secrets, PII, injection attacks can leak through.

**What's Needed**:
```python
# Before processing ANY user input
sanitized_context = sanitize_input(context)
# - Strip secrets (api_key, password, token)
# - Redact PII (email, ssn, credit_card)
# - Validate schema
# - Escape injection attempts
```

**Where to Fix**: `MarkX/agent/server.py` - Add `_sanitize_input()` before processing

---

### 3. Output Validation (Strict Schema)

**Current State**: LLM output is parsed with simple string matching.

**Problem**: LLM can hallucinate actions, targets, or evidence.

**What's Needed**:
```python
# Validate EVERY output against strict schema
validated_response = validate_output_schema(response)
# - All actions must be in allow-list
# - All targets must exist in context
# - All evidence must exist in ledger
# - All confidence scores must be 0.0-1.0
```

**Where to Fix**: `MarkX/agent/server.py` - Add `_validate_output()` before returning

---

### 4. Evidence Chain (Not Just Call IDs)

**Current State**: Citations include call_id but no evidence chain.

**Problem**: Can't trace "this event → this finding → this action".

**What's Needed**:
```python
# Every response must include evidence chain
evidence_chain = {
    "event_id": "evt-123",        # From Aegis (via Platform)
    "finding_id": "find-456",     # From PDRI (via Platform)
    "call_ids": ["call-1", "call-2"],  # From ledger
    "correlation_id": "corr-789"  # Links event → finding
}
```

**Where to Fix**: `MarkX/agent/server.py` - Add `_build_evidence_chain()` method

---

### 5. Strict Action Schema (Not Parsed from LLM)

**Current State**: Actions are parsed from LLM text with string matching.

**Problem**: LLM can hallucinate actions, miss required fields.

**What's Needed**:
```python
# LLM should output structured JSON, not text
# Then validate against strict schema
action_schema = {
    "action": str,  # MUST be in allow-list
    "target": str,  # MUST exist in context
    "reason": str,  # MUST reference evidence
    "approval_required": bool,  # From policy
    "blast_radius": str,  # From policy
    "evidence_required": List[str]  # call_ids from ledger
}
```

**Where to Fix**: `MarkX/agent/server.py` - Replace `_parse_action_recommendations()` with structured output

---

## What Dmitry Needs for ONE Working Loop

### The Loop (Dmitry's Part Only)

```
Platform sends:
{
  "event_id": "evt-123",
  "finding_id": "find-456",
  "entity_id": "customer-db",
  "risk_score": 85,
  "threat_type": "data_exposure"
}

Dmitry:
1. Sanitizes input ✅ (call ledger does this)
2. Calls Platform APIs (recorded in ledger) ✅
3. Builds evidence chain ❌ MISSING
4. Generates structured actions ❌ MISSING (currently parsed from text)
5. Validates output schema ❌ MISSING
6. Returns with proof ✅ (call_ids from ledger)

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
    "call_ids": ["call-1", "call-2"]
  }
}
```

---

## Dmitry's 7-Day Fix List (ONLY Dmitry)

### Day 1-2: Input Sanitation + Output Validation

**File**: `MarkX/core/input_sanitizer.py` (NEW)
- Strip secrets from context
- Redact PII
- Validate input schema
- Escape injection attempts

**File**: `MarkX/core/output_validator.py` (NEW)
- Validate response schema
- Check actions against allow-list
- Verify targets exist
- Confirm evidence exists in ledger

**File**: `MarkX/agent/server.py` (MODIFY)
- Add `_sanitize_input()` to `/chat` and `/advise`
- Add `_validate_output()` before returning

---

### Day 3-4: Evidence Chain + Structured Actions

**File**: `MarkX/core/evidence_chain.py` (NEW)
- Build evidence chain from context + ledger
- Link event_id → finding_id → call_ids
- Validate chain completeness

**File**: `MarkX/agent/server.py` (MODIFY)
- Replace text parsing with structured output
- Use LLM to generate JSON, not text
- Validate JSON against action schema
- Build evidence chain for every response

---

### Day 5-6: Real Explainability

**File**: `MarkX/core/explainer.py` (NEW)
- Analyze ledger calls (not LLM output)
- Extract decision path from evidence
- Generate reasoning from facts, not fluff

**File**: `MarkX/agent/server.py` (MODIFY)
- Replace `_extract_reasoning()` with ledger analysis
- Include decision path in response
- Show which evidence led to which conclusion

---

### Day 7: ONE Complete Flow Test

**Test**: Aegis event → Platform → Dmitry → Action

**File**: `MarkX/test_complete_flow.py` (NEW)
- Mock Platform sending event + finding
- Dmitry processes with full evidence chain
- Validate output has all required fields
- Verify evidence chain is complete
- Confirm actions are safe and validated

---

## What Dmitry Does NOT Need

❌ More endpoints  
❌ More documentation  
❌ More features  
❌ More tools  
❌ More modes  

---

## Dmitry's Actual Readiness

| Component | Status | Blocker |
|-----------|--------|---------|
| Call Ledger | ✅ Done | None |
| Action Safety | ✅ Done | None |
| PII Redaction | ✅ Done | None |
| Input Sanitation | ❌ Missing | No validation before LLM |
| Output Validation | ❌ Missing | No schema enforcement |
| Evidence Chain | ❌ Missing | Can't trace event → finding → action |
| Real Explainability | ❌ Missing | LLM fluff, not facts |
| Structured Actions | ❌ Missing | Parsed from text, not JSON |

**Overall**: 40% production-ready

---

## The Fix (Dmitry Only)

### Priority 1: Input Sanitation (2 days)
- Create `input_sanitizer.py`
- Integrate into `/chat` and `/advise`
- Test with malicious inputs

### Priority 2: Output Validation (2 days)
- Create `output_validator.py`
- Validate all responses before returning
- Test with invalid outputs

### Priority 3: Evidence Chain (2 days)
- Create `evidence_chain.py`
- Link event_id → finding_id → call_ids
- Include in every response

### Priority 4: Structured Actions (1 day)
- Replace text parsing with JSON schema
- Validate against action schema
- Test with LLM JSON output

### Priority 5: Real Explainability (2 days)
- Create `explainer.py`
- Analyze ledger, not LLM output
- Generate decision path from evidence

**Total**: 9 days to production-ready

---

## Bottom Line

**Dmitry has the foundation (ledger, safety gate, auth) but lacks trust enforcement.**

The missing pieces:
1. Input sanitation (treat all text as untrusted)
2. Output validation (strict schema)
3. Evidence chain (event → finding → action)
4. Real explainability (facts, not LLM fluff)
5. Structured actions (JSON, not text parsing)

**Once these are fixed, Dmitry is production-ready.**

**Then and ONLY then, build Platform.**

---

**Status**: 40% Production Ready  
**Blockers**: 5 critical gaps  
**Time to Fix**: 9 days  
**Next Step**: Stop adding features, fix trust
