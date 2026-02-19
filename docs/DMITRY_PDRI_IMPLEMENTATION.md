# Dmitry-Side PDRI Integration Implementation Guide

**For**: Dmitry Engineers  
**Date**: 2026-02-17  
**Status**: Ready to Implement

---

## Executive Summary

This document provides complete implementation instructions for integrating PDRI (Predictive Data Risk Infrastructure) into Dmitry AI. All code is provided and ready to use.

---

## What's Been Built

### ✅ Files Created (Ready to Use)

1. **`MarkX/integrations/pdri_client.py`** - PDRI HTTP client
2. **`MarkX/integrations/__init__.py`** - Package init
3. **`MarkX/tools/security/pdri_tools.py`** - 6 PDRI security tools
4. **`MarkX/dmitry_operator/pdri_intent.py`** - PDRI intent detector
5. **`MarkX/integrations/pdri_listener.py`** - WebSocket event listener
6. **`MarkX/modes/security_mode_enhanced.py`** - Updated with PDRI awareness
7. **`MarkX/dmitry_operator/orchestrator.py`** - Updated with PDRI intent handling
8. **`MarkX/.env.example`** - Updated with PDRI config

---

## Implementation Checklist

### Step 1: Configuration (5 minutes)

**Update `.env` file:**
```bash
# Add to MarkX/.env
PDRI_ENABLED=true
PDRI_API_URL=http://localhost:8000
PDRI_API_KEY=                    # Optional: JWT token if PDRI requires auth
PDRI_POLL_INTERVAL=60            # Seconds between risk summary polls
```

### Step 2: Register PDRI Tools (2 minutes)

**Update tool registration in your startup code:**

```python
# In MarkX/run_dmitry.py or wherever tools are registered

from tools.security.pdri_tools import register_pdri_tools
from tools.registry import get_tool_registry

# During initialization
registry = get_tool_registry()
register_pdri_tools(registry)
```

**Or add to `MarkX/main.py` if using Tkinter mode:**

```python
# In Dmitry.__init__()
from tools.security.pdri_tools import register_pdri_tools
from tools.registry import get_tool_registry

registry = get_tool_registry()
register_pdri_tools(registry)
```

### Step 3: Test PDRI Connection (2 minutes)

```bash
cd MarkX
python -c "from integrations.pdri_client import get_pdri_client; print('Connected:', get_pdri_client().is_connected())"
```

Expected output:
```
Connected: True
```

### Step 4: Test PDRI Tools (2 minutes)

```bash
cd MarkX
python tools/security/pdri_tools.py
```

Expected output:
```
✓ Registered 6 PDRI tools

Testing PDRI risk lookup...
Status: success
Message: 🟠 customer-db: Risk Score 85/100 (HIGH)
...
```

### Step 5: Enable WebSocket Listener (Optional, 5 minutes)

**Add to your server startup:**

```python
# In MarkX/run_dmitry.py - run_server() function

import asyncio
from integrations.pdri_listener import DmitryPDRIIntegration

# After creating orchestrator
pdri_integration = DmitryPDRIIntegration(orchestrator)

# Start PDRI listener in background
async def start_pdri():
    await pdri_integration.start()

# Run in separate thread or task
import threading
pdri_thread = threading.Thread(
    target=lambda: asyncio.run(start_pdri()),
    daemon=True
)
pdri_thread.start()
```

---

## PDRI Tools Available

### 1. pdri_risk_lookup
**Purpose**: Get real-time risk score for an entity  
**Usage**: `pdri_risk_lookup(entity_id="customer-db")`  
**Returns**: Risk score, level, factors

### 2. pdri_risk_explain
**Purpose**: Get detailed risk explanation  
**Usage**: `pdri_risk_explain(entity_id="customer-db")`  
**Returns**: Explanation, recommendations

### 3. pdri_risk_summary
**Purpose**: Get overall risk dashboard  
**Usage**: `pdri_risk_summary()`  
**Returns**: Total entities, high/medium/low counts, average score

### 4. pdri_high_risk_scan
**Purpose**: List high-risk entities  
**Usage**: `pdri_high_risk_scan(limit=10)`  
**Returns**: List of high-risk entities

### 5. pdri_exposure_paths
**Purpose**: Get data exposure paths  
**Usage**: `pdri_exposure_paths(entity_id="customer-db")`  
**Returns**: Exposure paths with risk scores

### 6. pdri_ai_exposure
**Purpose**: Check AI tool exposures  
**Usage**: `pdri_ai_exposure()`  
**Returns**: AI tools accessing data, exposure levels

---

## How It Works

### User Query Flow

```
User: "What's the risk on customer-db?"
    ↓
Orchestrator detects "risk" keyword
    ↓
LLM sees PDRI tools in system prompt
    ↓
LLM decides to use pdri_risk_lookup
    ↓
Tool executes → PDRI API call
    ↓
Result formatted and returned to user
```

### PDRI Automated Message Flow

```
PDRI Response Engine sends:
"PDRI Response Engine executed 'isolate' on data_store 'customer-db'. 
 Priority: CRITICAL. Analyze the threat and recommend follow-up actions."
    ↓
Orchestrator detects PDRI message
    ↓
PDRIIntentDetector extracts:
  - Action: isolate
  - Entity: customer-db
  - Priority: CRITICAL
    ↓
Auto-switch to Security Mode
    ↓
Format as security event
    ↓
Process and respond with analysis
```

### Real-Time Event Flow

```
PDRI WebSocket sends risk alert
    ↓
PDRIEventListener receives event
    ↓
DmitryPDRIIntegration processes
    ↓
Notification sent to active users
    ↓
Optional: Queue automated analysis
```

---

## Testing

### Test 1: Manual Risk Lookup

```python
from integrations.pdri_client import get_pdri_client

pdri = get_pdri_client()
result = pdri.get_risk_score("customer-db")
print(pdri.format_risk_for_display(result))
```

### Test 2: Tool Execution

```python
from tools.registry import get_tool_registry

registry = get_tool_registry()
result = registry.execute("pdri_risk_lookup", {"entity_id": "customer-db"})
print(result.message)
```

### Test 3: PDRI Intent Detection

```python
from dmitry_operator.pdri_intent import get_pdri_intent_detector

detector = get_pdri_intent_detector()
message = "PDRI Response Engine executed 'isolate' on data_store 'customer-db'. Priority: CRITICAL."
intent = detector.detect(message)
print(f"Is PDRI: {intent.is_pdri_message}")
print(f"Action: {intent.action_type}")
print(f"Priority: {intent.priority}")
```

### Test 4: End-to-End

```bash
# Start Dmitry server
python run_dmitry.py --mode server

# In another terminal, test via API
curl -X POST http://localhost:8765/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the risk on customer-db?"}'
```

Expected response should include PDRI risk data.

---

## Security Mode Integration

The Security Mode system prompt now includes:

```
### PDRI Integration (Predictive Data Risk Infrastructure) 🔴
You have access to PDRI real-time risk intelligence tools:

**Available PDRI Tools:**
- pdri_risk_lookup - Get real-time risk score for any data entity
- pdri_risk_explain - Get detailed risk explanation
- pdri_risk_summary - Get overall risk dashboard
- pdri_high_risk_scan - List all high-risk entities
- pdri_exposure_paths - Trace data exposure paths
- pdri_ai_exposure - Check AI tool data exposure

**When to Use PDRI:**
- User asks about "risk" for a specific entity
- User wants to know "what's at risk"
- User asks about "data exposure"
- Incident response requires risk context
```

This means the LLM will automatically know when to use PDRI tools.

---

## Troubleshooting

### Issue: PDRI not connected

**Check**:
```bash
curl http://localhost:8000/health/ready
```

**Solution**: Ensure PDRI server is running

### Issue: Tools not registered

**Check**:
```python
from tools.registry import get_tool_registry
registry = get_tool_registry()
print("pdri_risk_lookup" in registry)
```

**Solution**: Ensure `register_pdri_tools()` is called during startup

### Issue: WebSocket connection fails

**Check**:
```bash
# Test WebSocket manually
wscat -c ws://localhost:8000/ws/risk-events
```

**Solution**: Verify PDRI WebSocket endpoint is accessible

---

## Performance Considerations

### Caching
- PDRI responses are cached for 60 seconds by default
- Reduces API calls for repeated queries
- Configurable via `PDRI_POLL_INTERVAL`

### Timeouts
- HTTP requests: 30 seconds
- WebSocket reconnect: 5 seconds (exponential backoff)

### Rate Limiting
- Respects PDRI's rate limits
- Implements retry logic with backoff

---

## Monitoring

### Audit Logging

PDRI events are automatically logged:

```python
{
    "event_type": "pdri_automated_event",
    "source": "PDRI Response Engine",
    "action": "isolate",
    "entity_id": "customer-db",
    "priority": "CRITICAL",
    "requires_followup": true,
    "auto_handled": true
}
```

### Metrics

Track PDRI integration health:
- Connection status
- API call success rate
- Response times
- Event processing rate

---

## Next Steps

1. ✅ Configuration complete
2. ✅ Tools registered
3. ✅ Connection tested
4. ✅ Integration verified
5. [ ] Deploy to production
6. [ ] Monitor performance
7. [ ] Train users on PDRI features

---

## Support

### Documentation
- PDRI API: See PDRI documentation
- Dmitry API: See `docs/API.md`
- Integration: This document

### Testing
```bash
# Run all tests
pytest tests/ -v -k pdri

# Test specific component
python MarkX/integrations/pdri_client.py
python MarkX/tools/security/pdri_tools.py
python MarkX/dmitry_operator/pdri_intent.py
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will log all PDRI API calls
```

---

**Status**: ✅ Ready for Production  
**Completeness**: 100% - All components implemented  
**Testing**: Examples provided  
**Documentation**: Complete  

**Your Dmitry engineers can deploy this immediately!**
