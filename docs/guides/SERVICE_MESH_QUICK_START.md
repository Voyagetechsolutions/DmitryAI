# Dmitry Service Mesh - Quick Start

**3-minute guide to Platform integration**

---

## What Changed

### Before (Standalone)
```python
server = AgentServer(port=8765)
server.start()
```

### After (Service Mesh)
```python
server = AgentServer(
    port=8765,
    platform_url="http://platform:8000"  # NEW
)
server.start()
# Output: ✓ Registered with Platform, heartbeat started
```

---

## New Endpoints

### 1. Health Check (ServiceHealth model)
```bash
curl http://127.0.0.1:8765/health
```
```json
{
  "service": "dmitry",
  "status": "healthy",
  "version": "1.2",
  "uptime_seconds": 3600.5,
  "checks": {
    "llm": true,
    "platform": true,
    "call_ledger": true
  }
}
```

### 2. Readiness Probe (K8s)
```bash
curl http://127.0.0.1:8765/ready
```
```json
{
  "ready": true,
  "dependencies": {
    "llm": "healthy",
    "platform": "healthy"
  }
}
```

### 3. Liveness Probe (K8s)
```bash
curl http://127.0.0.1:8765/live
```
```json
{
  "alive": true
}
```

---

## New Contract: /advise

### Request (AdviseRequest)
```bash
curl -X POST http://127.0.0.1:8765/advise \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "find-456",
    "tenant_id": "tenant-1",
    "entity": {
      "type": "database",
      "id": "customer-db",
      "name": "Customer Database"
    },
    "severity": "high",
    "risk_score": 85.0,
    "evidence_refs": ["evt-123", "find-456"]
  }'
```

### Response (AdviseResponse)
```json
{
  "summary": "High risk detected...",
  "risk_factors": [
    {
      "factor": "high_risk_score",
      "severity": "high",
      "description": "Elevated risk score",
      "evidence": ["evt-123", "find-456"]
    }
  ],
  "impact_analysis": "Critical impact...",
  "recommended_actions": [
    {
      "action_type": "isolate_entity",
      "target_type": "database",
      "target_id": "customer-db",
      "reason": "High risk detected",
      "confidence": 0.87,
      "evidence_refs": ["evt-123", "find-456"],
      "blast_radius": "low",
      "priority": 8
    }
  ],
  "evidence_chain": [
    {"type": "event", "id": "evt-123"},
    {"type": "finding", "id": "find-456"}
  ],
  "confidence": 0.87,
  "citations": ["platform_get_risk_findings"],
  "processing_time_ms": 245
}
```

---

## Testing

### Run Tests
```bash
cd MarkX
python test_service_mesh.py
```

### Expected Output
```
✅ PASSED - Health Endpoint
✅ PASSED - Ready Endpoint
✅ PASSED - Live Endpoint
✅ PASSED - Advise Contract

🎉 ALL TESTS PASSED
```

---

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dmitry
spec:
  template:
    spec:
      containers:
      - name: dmitry
        image: dmitry:1.2
        env:
        - name: PLATFORM_URL
          value: "http://platform-service:8000"
        livenessProbe:
          httpGet:
            path: /live
            port: 8765
        readinessProbe:
          httpGet:
            path: /ready
            port: 8765
```

---

## What Didn't Change

### All Production Components Still Work ✅
- Call ledger (immutable audit trail)
- Action safety gate (allow-list + evidence)
- Input sanitation (secrets + PII)
- Output validation (strict schema)
- Evidence chain (event → finding → action)
- Structured actions (JSON parsing)

### All Platform Integration Still Works ✅
- Circuit breaker
- Retry logic
- Connection pooling
- Fault tolerance

---

## Summary

**3 things added:**
1. Service registration (startup/heartbeat/shutdown)
2. Health endpoints (/health, /ready, /live)
3. AdviseRequest/AdviseResponse contract

**Everything else unchanged.**

**Dmitry is Platform-ready.**

