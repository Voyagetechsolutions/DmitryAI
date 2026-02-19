# Dmitry API Documentation

## Overview

Dmitry provides a WebSocket-based API for real-time interaction with the AI assistant. The API supports authentication, multiple cognitive modes, and comprehensive security features.

## Base URL

```
ws://localhost:8765
```

## Authentication

### Generate Token

```python
from agent.auth import AuthManager

auth = AuthManager()
token = auth.generate_token(user_id="user123", expires_hours=24)
```

### Connect with Token

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_token_here'
  }));
};
```

## Message Format

### Request

```json
{
  "type": "message",
  "text": "Your message here",
  "mode": "security",
  "context": {
    "session_id": "session123",
    "user_id": "user123"
  }
}
```

### Response

```json
{
  "type": "response",
  "text": "Dmitry's response",
  "intent": "general_query",
  "mode": "security",
  "metadata": {
    "timestamp": "2026-02-17T10:30:00Z",
    "processing_time": 1.23
  }
}
```

## Cognitive Modes

### Available Modes

1. **utility** - System operations and file management
2. **general** - General conversation and queries
3. **design** - UI/UX design assistance
4. **developer** - Code development and debugging
5. **research** - Research and information gathering
6. **security** - Security operations and analysis
7. **simulation** - Scenario simulation and modeling

### Switch Mode

```json
{
  "type": "switch_mode",
  "mode": "security"
}
```

## Security Mode Sub-Modes

### Available Sub-Modes

1. **threat_hunting** - Proactive threat detection
2. **vulnerability_assessment** - Vulnerability scanning and analysis
3. **ai_security_audit** - AI model security auditing
4. **compliance_audit** - Compliance checking
5. **incident_response** - Incident handling and response
6. **cloud_security_posture** - Cloud security assessment
7. **penetration_testing** - Security testing

### Switch Sub-Mode

```json
{
  "type": "switch_sub_mode",
  "sub_mode": "threat_hunting"
}
```

## Security Tools

### Threat Intelligence Lookup

```json
{
  "type": "tool_call",
  "tool": "threat_intel_lookup",
  "parameters": {
    "ioc": "192.168.1.100",
    "ioc_type": "ip"
  }
}
```

### Vulnerability Scan

```json
{
  "type": "tool_call",
  "tool": "vulnerability_scanner",
  "parameters": {
    "target": "example.com",
    "scan_type": "full"
  }
}
```

### Compliance Check

```json
{
  "type": "tool_call",
  "tool": "compliance_checker",
  "parameters": {
    "framework": "soc2",
    "system_config": {
      "encryption": true,
      "mfa": true
    }
  }
}
```

### AI Security Audit

```json
{
  "type": "tool_call",
  "tool": "ai_security_audit",
  "parameters": {
    "model_config": {
      "name": "my-model",
      "type": "llm"
    }
  }
}
```

## Rate Limiting

- Default: 100 requests per minute per user
- Configurable via `API_RATE_LIMIT` environment variable
- Returns 429 status when limit exceeded

## Error Handling

### Error Response Format

```json
{
  "type": "error",
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Common Error Codes

- `AUTH_FAILED` - Authentication failed
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INVALID_MODE` - Invalid cognitive mode
- `TOOL_ERROR` - Tool execution failed
- `PROMPT_INJECTION_DETECTED` - Malicious input detected

## Audit Logging

All API calls are automatically logged with:
- User ID
- Timestamp
- Action performed
- Parameters
- Result
- Risk level

Query audit logs:

```python
from core.audit_log import AuditLogger

logger = AuditLogger()
logs = logger.query_logs(user_id="user123", limit=100)
```

## Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "modes": ["utility", "general", "design", "developer", "research", "security", "simulation"]
}
```

## Metrics

Prometheus metrics available at:
```
GET /metrics
```

Key metrics:
- `dmitry_requests_total` - Total requests
- `dmitry_request_duration_seconds` - Request latency
- `dmitry_active_sessions` - Active sessions
- `dmitry_tool_executions_total` - Tool executions
- `dmitry_security_events_total` - Security events

## Examples

### Python Client

```python
import asyncio
import websockets
import json

async def chat_with_dmitry():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # Authenticate
        await websocket.send(json.dumps({
            "type": "auth",
            "token": "your_token"
        }))
        
        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "text": "Scan for vulnerabilities in example.com",
            "mode": "security"
        }))
        
        # Receive response
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(chat_with_dmitry())
```

### JavaScript Client

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_token'
  }));
  
  // Send message
  ws.send(JSON.stringify({
    type: 'message',
    text: 'Check SOC2 compliance',
    mode: 'security'
  }));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(response);
};
```

## Best Practices

1. **Always authenticate** before sending messages
2. **Use appropriate modes** for different tasks
3. **Handle rate limiting** gracefully
4. **Monitor audit logs** for security events
5. **Implement retry logic** for transient failures
6. **Validate responses** before using data
7. **Keep tokens secure** and rotate regularly

## Support

For issues or questions:
- Check audit logs for detailed error information
- Run validation: `python MarkX/validate_setup.py`
- Review documentation in `docs/` directory
