# Developer Quick Reference: Clean Architecture

## The Golden Rule

> Every service produces or consumes contracts.
> Only the Platform owns relationships.

## Service Boundaries

### Dmitry (Voice + Hands)
**Knows**: Platform API endpoint
**Doesn't Know**: PDRI, Aegis, Neo4j exist

```python
# ✅ GOOD: Call Platform
platform.get_risk_findings(filters)

# ❌ BAD: Call PDRI directly
pdri.get_risk_score(entity_id)
```

### PDRI (Risk Intelligence)
**Knows**: How to calculate risk scores
**Doesn't Know**: Dmitry, Aegis exist

```python
# ✅ GOOD: Emit events to Platform
platform.send_event({
    "source": "pdri",
    "event_type": "risk_score_update",
    "entity_id": "customer-db",
    "risk_score": 85
})

# ❌ BAD: Call Dmitry directly
dmitry.notify_risk_alert(entity_id)
```

### Aegis (Security Detection)
**Knows**: How to detect threats
**Doesn't Know**: PDRI, Dmitry exist

```python
# ✅ GOOD: Emit events to Platform
platform.send_event({
    "source": "aegis",
    "event_type": "ai_tool_detection",
    "actor": "user@example.com",
    "severity": "HIGH"
})

# ❌ BAD: Call PDRI directly
pdri.update_risk_score(entity_id)
```

### Platform (Orchestrator)
**Knows**: All services
**Doesn't Know**: Nothing (it's the boss)

```python
# ✅ GOOD: Orchestrate everything
def get_risk_findings(filters):
    # Query PDRI for risk scores
    pdri_data = pdri_client.get_scores()
    
    # Query Aegis for detections
    aegis_data = aegis_client.get_detections()
    
    # Query Neo4j for relationships
    neo4j_data = neo4j_client.query()
    
    # Combine and return
    return combine(pdri_data, aegis_data, neo4j_data)
```

## Environment Variables

### Dmitry
```bash
# Only needs Platform
PLATFORM_API_URL=http://localhost:9000
PLATFORM_API_KEY=secret
```

### PDRI
```bash
# Only needs Platform
PLATFORM_API_URL=http://localhost:9000
PLATFORM_API_KEY=secret
```

### Aegis
```bash
# Only needs Platform
PLATFORM_API_URL=http://localhost:9000
PLATFORM_API_KEY=secret
```

### Platform
```bash
# Knows about all services
PDRI_API_URL=http://localhost:8000
AEGIS_API_URL=http://localhost:8001
NEO4J_URI=bolt://localhost:7687
```

## API Contracts

### Platform API (for Dmitry)
```
GET  /api/v1/health
GET  /api/v1/risk-findings
GET  /api/v1/risk-findings/{id}
GET  /api/v1/entities/search
GET  /api/v1/risk-findings/{id}/actions
POST /api/v1/actions/execute
```

### Platform API (for PDRI/Aegis)
```
POST /api/v1/events
```

## Adding a New Service

### ❌ WRONG: Direct Integration
```
New Service → Dmitry
New Service → PDRI
New Service → Aegis
```

### ✅ RIGHT: Platform Integration
```
New Service → Platform
Platform → (handles everything)
```

## Testing

### Dmitry Tests
```python
# Mock Platform API
with mock_platform():
    result = dmitry.query("What's the risk?")
    assert result.status == "success"
```

### PDRI Tests
```python
# Mock Platform event endpoint
with mock_platform():
    pdri.calculate_risk("customer-db")
    assert platform.received_event("risk_score_update")
```

### Aegis Tests
```python
# Mock Platform event endpoint
with mock_platform():
    aegis.detect_threat(user_action)
    assert platform.received_event("ai_tool_detection")
```

## Deployment

### Independent Services
```bash
# Deploy Dmitry
docker-compose up dmitry

# Deploy PDRI
docker-compose up pdri

# Deploy Aegis
docker-compose up aegis

# Deploy Platform
docker-compose up platform
```

### Scaling
```bash
# Scale Dmitry only
docker-compose up --scale dmitry=3

# Scale PDRI only
docker-compose up --scale pdri=2

# Scale Platform only
docker-compose up --scale platform=5
```

## Debugging

### Dmitry Issues
1. Check Platform API is reachable
2. Check Platform API key is valid
3. Check Platform logs for errors
4. Don't check PDRI/Aegis (Dmitry doesn't know they exist)

### PDRI Issues
1. Check Platform event endpoint is reachable
2. Check PDRI is sending events correctly
3. Check Platform logs for event ingestion
4. Don't check Dmitry/Aegis (PDRI doesn't know they exist)

### Aegis Issues
1. Check Platform event endpoint is reachable
2. Check Aegis is sending events correctly
3. Check Platform logs for event ingestion
4. Don't check Dmitry/PDRI (Aegis doesn't know they exist)

### Platform Issues
1. Check all service connections
2. Check Neo4j is reachable
3. Check event ingestion pipeline
4. Check API response times

## Common Mistakes

### ❌ Mistake 1: Direct Service Calls
```python
# In Dmitry
from pdri_client import PDRIClient
pdri = PDRIClient()
risk = pdri.get_risk_score("customer-db")
```

### ✅ Fix: Use Platform
```python
# In Dmitry
from platform_client import PlatformClient
platform = PlatformClient()
findings = platform.get_risk_findings({"entity_id": "customer-db"})
```

### ❌ Mistake 2: Service-Specific Logic
```python
# In Dmitry
if message.startswith("PDRI"):
    # PDRI-specific handling
    ...
```

### ✅ Fix: Generic Handling
```python
# In Dmitry
# Just process the message normally
# Platform handles service-specific logic
```

### ❌ Mistake 3: Shared Configuration
```python
# In .env
PDRI_API_URL=http://localhost:8000  # Used by Dmitry
AEGIS_API_URL=http://localhost:8001  # Used by Dmitry
```

### ✅ Fix: Service-Specific Config
```python
# In Dmitry .env
PLATFORM_API_URL=http://localhost:9000  # Only Platform

# In Platform .env
PDRI_API_URL=http://localhost:8000
AEGIS_API_URL=http://localhost:8001
```

## Quick Checklist

Before committing code, ask:

- [ ] Does this service know about other services?
- [ ] Does this service call other services directly?
- [ ] Does this service have service-specific logic?
- [ ] Does this service share configuration with other services?

If you answered YES to any of these, you're breaking clean architecture.

## When in Doubt

Ask yourself:
> "If I removed PDRI/Aegis/Dmitry, would this service still work?"

If the answer is NO, you have coupling.

## Resources

- `CLEAN_ARCHITECTURE_ACHIEVED.md` - Full architecture guide
- `PLATFORM_IMPLEMENTATION_CHECKLIST.md` - Platform implementation
- `BEFORE_AFTER_COMPARISON.md` - Before/after comparison
- `EXECUTIVE_SUMMARY.md` - Executive summary

---

**Remember**: Clean boundaries = Scalable product
