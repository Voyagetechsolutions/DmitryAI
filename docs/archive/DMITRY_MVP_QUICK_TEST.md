# Dmitry MVP Quick Test Guide

**Purpose**: Verify Dmitry MVP implementation  
**Time**: 5 minutes  
**Prerequisites**: Python 3.8+, dependencies installed

---

## 1. Start Dmitry Server

```bash
cd MarkX
python run_dmitry.py --mode server
```

**Expected Output**:
```
==================================================
  DMITRY v1.2 - Agent Mode
==================================================

✓ Mode: general
✓ Orchestrator: Ready (Hands & Eyes active)

Agent ready. Connect with Electron UI or API client.
Press Ctrl+C to stop.

✓ Agent API server started on http://127.0.0.1:8765
```

---

## 2. Test Health Endpoints

### Health Check
```bash
curl http://127.0.0.1:8765/health
```

**Expected**:
```json
{
  "status": "healthy",
  "version": "1.2",
  "uptime": 10,
  "timestamp": "2026-02-19T10:30:00Z"
}
```

### Readiness Check
```bash
curl http://127.0.0.1:8765/ready
```

**Expected**:
```json
{
  "ready": true,
  "dependencies": {
    "llm": "healthy",
    "platform": "unavailable"
  },
  "timestamp": "2026-02-19T10:30:00Z"
}
```

**Note**: Platform will show "unavailable" until Platform is built.

### Version Info
```bash
curl http://127.0.0.1:8765/version
```

**Expected**:
```json
{
  "version": "1.2",
  "build": "2026-02-19",
  "capabilities": [
    "chat",
    "advise",
    "vision",
    "security_tools",
    "platform_integration"
  ],
  "schema_version": "1.0"
}
```

### Metrics
```bash
curl http://127.0.0.1:8765/metrics
```

**Expected**:
```json
{
  "requests_total": 0,
  "requests_success": 0,
  "requests_failed": 0,
  "avg_latency_ms": 0,
  "llm_inference_time_ms": 0,
  "active_sessions": 0,
  "timestamp": "2026-02-19T10:30:00Z"
}
```

---

## 3. Test Chat Endpoint

```bash
curl -X POST http://127.0.0.1:8765/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what can you do?",
    "context": {}
  }'
```

**Expected Structure**:
```json
{
  "answer": "...",
  "citations": [],
  "proposed_actions": [],
  "sources": [],
  "reasoning_summary": "...",
  "confidence": 0.5,
  "data_dependencies": [],
  "schema_version": "1.0",
  "producer_version": "1.2"
}
```

---

## 4. Test Advise Endpoint

```bash
curl -X POST http://127.0.0.1:8765/advise \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "entity_id": "customer-db",
      "risk_score": 85,
      "threat_type": "data_exposure"
    },
    "question": "What should we do?"
  }'
```

**Expected Structure**:
```json
{
  "recommended_actions": [
    {
      "action": "investigate",
      "target": "customer-db",
      "reason": "High risk score detected...",
      "risk_reduction_estimate": 0.25,
      "confidence": 0.8,
      "priority": "HIGH"
    }
  ],
  "reasoning": "...",
  "sources": [],
  "confidence": 0.5,
  "data_dependencies": [],
  "schema_version": "1.0",
  "producer_version": "1.2"
}
```

---

## 5. Test Authentication

### Generate Token

```python
# In Python shell
from agent.auth import auth_manager

token = auth_manager.generate_token(
    user_id="test-platform",
    service_role="platform",
    tenant_id="test-tenant"
)

print(f"Token: {token}")
```

### Verify Token

```python
payload = auth_manager.verify_token(token)
print(f"Valid: {payload is not None}")
print(f"User: {payload.get('user_id')}")
print(f"Role: {payload.get('service_role')}")
```

### Test Rate Limiting

```python
# Test rate limit
for i in range(105):
    allowed, error = auth_manager.check_rate_limit("test-user")
    if not allowed:
        print(f"Rate limited at request {i}: {error}")
        break
```

---

## 6. Test Platform Client

### Check Connection

```python
from tools.platform.platform_client import get_platform_client

platform = get_platform_client()
health = platform.health_check()

print(f"Connected: {health.get('connected')}")
print(f"Status: {health.get('status')}")
```

**Expected** (Platform not running):
```
Connected: False
Status: unhealthy
```

### Test Circuit Breaker

```python
# Make multiple failed requests
for i in range(10):
    result = platform.get_risk_findings()
    print(f"Request {i}: {result.get('error', 'success')}")
```

**Expected**: After 5 failures, circuit breaker opens:
```
Request 5: Platform temporarily unavailable (circuit breaker open)
```

---

## 7. Test Platform Tools

```python
from tools.registry import get_tool_registry
from tools.platform.platform_tools import register_platform_tools

# Register tools
registry = get_tool_registry()
register_platform_tools(registry)

# List tools
print("Registered tools:")
for tool_name in registry.list_tools():
    if tool_name.startswith("platform_"):
        print(f"  - {tool_name}")
```

**Expected**:
```
Registered tools:
  - platform_get_risk_findings
  - platform_get_finding_details
  - platform_search_entities
  - platform_propose_actions
  - platform_execute_action
```

---

## 8. Test Legacy Endpoints

### Message
```bash
curl -X POST http://127.0.0.1:8765/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### Status
```bash
curl http://127.0.0.1:8765/status
```

### Logs
```bash
curl http://127.0.0.1:8765/logs?limit=10
```

---

## Success Criteria

✅ All health endpoints return 200  
✅ `/chat` returns explainability contract  
✅ `/advise` returns action recommendations  
✅ Authentication generates valid tokens  
✅ Rate limiting blocks after threshold  
✅ Platform client handles failures gracefully  
✅ Circuit breaker opens after failures  
✅ All 5 Platform tools registered  

---

## Troubleshooting

### Issue: Server won't start

**Check**:
```bash
# Verify Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "jwt|requests"
```

**Solution**: Install dependencies
```bash
pip install -r requirements_production.txt
```

### Issue: Import errors

**Check**:
```bash
# Verify you're in MarkX directory
pwd  # Should end with /MarkX
```

**Solution**: Change to MarkX directory
```bash
cd MarkX
```

### Issue: Port already in use

**Check**:
```bash
# Windows
netstat -ano | findstr :8765

# Linux/Mac
lsof -i :8765
```

**Solution**: Kill process or use different port
```bash
python run_dmitry.py --mode server --port 8766
```

---

## Next Steps

After successful testing:

1. **Configure Platform URL** (when Platform is ready):
   ```bash
   export PLATFORM_API_URL=http://localhost:9000
   export PLATFORM_API_KEY=platform-secret
   ```

2. **Test Platform Integration**:
   ```bash
   curl http://127.0.0.1:8765/ready
   # Should show platform: "healthy"
   ```

3. **Deploy to Production**:
   - Generate secure JWT secret
   - Configure HTTPS/TLS
   - Set up monitoring
   - Configure logging

---

**Status**: ✅ Ready to Test  
**Time Required**: 5 minutes  
**Difficulty**: Easy
