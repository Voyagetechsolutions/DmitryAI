# Dmitry Service Mesh Requirements

**Focus**: Only what Dmitry needs to integrate with Platform  
**Architecture**: Indestructible service mesh with resilience

---

## What Dmitry Must Implement

### 1. Service Registration & Heartbeat
- Register with Platform on startup
- Send heartbeat every 10 seconds
- Deregister on shutdown

### 2. Health Endpoints
- `GET /health` - Detailed health with checks
- `GET /ready` - Kubernetes readiness probe
- `GET /live` - Kubernetes liveness probe

### 3. Shared Contracts
- Use exact same Pydantic models as Platform
- No drift, no surprises

### 4. Resilient Client (Already Have)
- Circuit breaker ✅ (already implemented)
- Retry logic ✅ (already implemented)
- Connection pooling ✅ (already implemented)

---

## Dmitry's Contract (What Platform Calls)

### Request: AdviseRequest
```python
{
    "finding_id": "find-456",
    "tenant_id": "tenant-1",
    "entity": {
        "type": "database",
        "id": "customer-db",
        "name": "Customer Database",
        "attributes": {}
    },
    "severity": "high",
    "risk_score": 85.0,
    "exposure_paths": [...],
    "evidence_refs": ["evt-123", "find-456"],
    "policy_context": {}
}
```

### Response: AdviseResponse
```python
{
    "summary": "High risk detected on customer-db...",
    "risk_factors": [
        {
            "factor": "high_risk_score",
            "severity": "high",
            "description": "Risk score of 85/100",
            "evidence": ["find-456"]
        }
    ],
    "impact_analysis": "Data exposure threat...",
    "recommended_actions": [
        {
            "action_type": "isolate_entity",
            "target_type": "database",
            "target_id": "customer-db",
            "target_name": "Customer Database",
            "reason": "High risk with data exposure",
            "confidence": 0.87,
            "evidence_refs": ["evt-123", "find-456", "call-1"],
            "blast_radius": "low",
            "priority": 8
        }
    ],
    "evidence_chain": [
        {"type": "event", "id": "evt-123"},
        {"type": "finding", "id": "find-456"},
        {"type": "platform_call", "id": "call-1"}
    ],
    "confidence": 0.87,
    "citations": ["platform_get_risk_findings"],
    "processing_time_ms": 245
}
```

---

## What Dmitry Needs to Add

### 1. Shared Contracts (New)
**File**: `MarkX/shared/contracts/dmitry.py`
- Pydantic models matching Platform exactly
- No custom serialization

### 2. Service Registry (New)
**File**: `MarkX/shared/registry.py`
- Register on startup
- Heartbeat every 10s
- Deregister on shutdown

### 3. Health Endpoints (New)
**File**: `MarkX/agent/server.py` (extend)
- `/health` with detailed checks
- `/ready` for K8s
- `/live` for K8s

### 4. FastAPI Migration (Optional but Recommended)
**Current**: Custom HTTP server  
**Better**: FastAPI with lifespan management

---

## Implementation Priority

### Must Have (For Platform Integration)
1. ✅ Shared contracts (Pydantic models)
2. ✅ Service registration
3. ✅ Health endpoints
4. ✅ Resilient client (already have)

### Already Have
- ✅ Circuit breaker
- ✅ Retry logic
- ✅ Connection pooling
- ✅ Call ledger
- ✅ Action safety
- ✅ Evidence chain

### Don't Need (Platform Handles)
- ❌ Kafka integration (Platform does this)
- ❌ Service discovery (Platform does this)
- ❌ Dead letter queue (Platform does this)

---

## Dmitry's Minimal Changes

### Change 1: Add Shared Contracts
Create `MarkX/shared/contracts/dmitry.py` with exact Pydantic models.

### Change 2: Add Service Registry
Create `MarkX/shared/registry.py` for registration and heartbeat.

### Change 3: Extend Health Endpoints
Add `/health`, `/ready`, `/live` to `server.py`.

### Change 4: Update /advise Endpoint
Accept `AdviseRequest`, return `AdviseResponse` (exact schema).

---

## What Dmitry Keeps

### Current Architecture (Don't Change)
- ✅ Call ledger
- ✅ Action safety gate
- ✅ Input sanitation
- ✅ Output validation
- ✅ Evidence chain
- ✅ Structured actions

### Current Client (Don't Change)
- ✅ `platform_client.py` with circuit breaker
- ✅ Fault tolerance
- ✅ Graceful degradation

---

## Bottom Line

**Dmitry needs 3 things for service mesh:**

1. **Shared contracts** - Pydantic models matching Platform
2. **Service registration** - Register + heartbeat
3. **Health endpoints** - `/health`, `/ready`, `/live`

**Everything else Dmitry already has.**

---

**Next**: Implement these 3 things, keep everything else as-is.
