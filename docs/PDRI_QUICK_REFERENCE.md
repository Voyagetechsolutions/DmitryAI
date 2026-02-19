# PDRI → Dmitry Integration - Quick Reference

## Connection

```python
from integrations.dmitry_client import DmitryClient

dmitry = DmitryClient("http://127.0.0.1:8765")
```

## Core Methods

| Method | Purpose | Example |
|--------|---------|---------|
| `send_message(msg)` | Send query/command | `dmitry.send_message("Analyze threat")` |
| `switch_mode(mode)` | Change cognitive mode | `dmitry.switch_mode("security")` |
| `get_status()` | Check connection | `dmitry.get_status()` |
| `get_logs(limit)` | Get action history | `dmitry.get_logs(50)` |

## Strategic Advisor Methods

| Method | Purpose |
|--------|---------|
| `analyze_threat(desc)` | Security threat analysis |
| `get_strategic_advice(context, question)` | Strategic recommendations |
| `format_for_natural_language(data)` | Format data for presentation |
| `explain_technical_concept(concept, audience)` | Explain technical topics |
| `generate_report_summary(data)` | Generate executive summaries |

## Security Operations

| Method | Purpose |
|--------|---------|
| `lookup_threat_intelligence(ioc, type)` | IOC lookup |
| `check_compliance(framework, config)` | Compliance checking |
| `analyze_vulnerability(vuln_data)` | Vulnerability analysis |
| `assess_ai_model_risk(model_config)` | AI model risk assessment |

## Cognitive Modes

- `utility` - System operations
- `general` - General conversation
- `design` - UI/UX design
- `developer` - Code development
- `research` - Research tasks
- `security` - Security operations (7 sub-modes)
- `simulation` - Scenario modeling

## Response Structure

```python
{
    "text": "Response text",
    "intent": "chat|action|security_alert",
    "mode": "current_mode",
    "tool_executed": "tool_name",  # optional
    "tool_result": "result",        # optional
    "security_alert": bool          # optional
}
```

## Quick Examples

### Example 1: Threat Analysis
```python
result = dmitry.analyze_threat(
    "Multiple failed login attempts from 192.168.1.100"
)
print(result['text'])
```

### Example 2: Compliance Check
```python
result = dmitry.check_compliance("soc2", {
    "encryption": True,
    "mfa": True,
    "logging": True
})
print(result['text'])
```

### Example 3: Strategic Advice
```python
result = dmitry.get_strategic_advice(
    context="Cloud migration project",
    question="Multi-cloud vs single cloud?"
)
print(result['text'])
```

### Example 4: Format Data
```python
data = {"vulnerabilities": 15, "critical": 3}
formatted = dmitry.format_for_natural_language(data)
print(formatted)
```

## Error Handling

```python
result = dmitry.send_message("query")

if result.get("intent") == "error":
    print(f"Error: {result.get('error')}")
elif result.get("security_alert"):
    print(f"Security Alert: {result.get('text')}")
else:
    print(f"Response: {result.get('text')}")
```

## Health Check

```python
if dmitry.is_connected():
    print("✅ Connected")
else:
    print("❌ Not connected")

health = dmitry.health_check()
print(f"Latency: {health['latency_ms']}ms")
```

## Start Dmitry Server

```bash
cd MarkX
python run_dmitry.py --mode server
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/message` | POST | Send message |
| `/mode` | POST | Switch mode |
| `/status` | GET | Get status |
| `/logs` | GET | Get logs |

## Timeouts

- `/message`: 30s
- `/mode`: 10s
- `/status`: 5s
- `/logs`: 10s

## Rate Limits

- Default: 100 requests/minute
- Configurable via `API_RATE_LIMIT`

---

**Full Documentation**: See `PDRI_INTEGRATION_BRIEF.md`
