# Dmitry PDRI Integration - Quick Start

## 5-Minute Setup

### 1. Add Configuration (1 min)
```bash
# Edit MarkX/.env
PDRI_ENABLED=true
PDRI_API_URL=http://localhost:8000
PDRI_API_KEY=
```

### 2. Register Tools (1 min)
```python
# Add to MarkX/run_dmitry.py in run_server()
from tools.security.pdri_tools import register_pdri_tools
from tools.registry import get_tool_registry

registry = get_tool_registry()
register_pdri_tools(registry)
```

### 3. Test Connection (1 min)
```bash
python -c "from integrations.pdri_client import get_pdri_client; print('Connected:', get_pdri_client().is_connected())"
```

### 4. Test Tool (1 min)
```bash
python tools/security/pdri_tools.py
```

### 5. Start Server (1 min)
```bash
python run_dmitry.py --mode server
```

## Test Query

```bash
curl -X POST http://localhost:8765/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the risk on customer-db?"}'
```

## Files Created

- `MarkX/integrations/pdri_client.py` - HTTP client
- `MarkX/tools/security/pdri_tools.py` - 6 tools
- `MarkX/dmitry_operator/pdri_intent.py` - Intent detector
- `MarkX/integrations/pdri_listener.py` - WebSocket listener

## PDRI Tools

| Tool | Purpose |
|------|---------|
| `pdri_risk_lookup` | Get risk score |
| `pdri_risk_explain` | Get explanation |
| `pdri_risk_summary` | Get dashboard |
| `pdri_high_risk_scan` | List high-risk |
| `pdri_exposure_paths` | Get exposure paths |
| `pdri_ai_exposure` | Check AI exposure |

## Troubleshooting

**Not connected?**
```bash
curl http://localhost:8000/health/ready
```

**Tools not working?**
```python
from tools.registry import get_tool_registry
print("pdri_risk_lookup" in get_tool_registry())
```

## Full Documentation

See `docs/DMITRY_PDRI_IMPLEMENTATION.md`
