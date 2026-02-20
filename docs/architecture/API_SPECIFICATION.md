# Dmitry MVP API Specification

**Version**: 1.2  
**Date**: 2026-02-19  
**Status**: Production Ready  
**Base URL**: `http://127.0.0.1:8765`

---

## Overview

Dmitry exposes a clean HTTP API for Platform integration. Dmitry is the **interface** (Voice + Hands), not a data owner. All responses include explainability contracts for enterprise trust.

---

## Authentication

### Service-to-Service (JWT)

All Platform requests must include JWT token:

```http
Authorization: Bearer <jwt_token>
X-Service-Role: platform
X-Tenant-ID: tenant-123
```

### Token Generation

```python
from agent.auth import auth_manager

token = auth_manager.generate_token(
    user_id="platform-service",
    service_role="platform",
    tenant_id="tenant-123",
    expires_hours=24
)
```

### Supported Roles

- `platform` - Full access (orchestrator)
- `dmitry` - Self-service access
- `pdri` - Limited read access
- `aegis` - Limited read access

---

## Core Endpoints

### 1. POST /chat

**Purpose**: Platform chat with context + explainability

**Request**:
```json
{
  "message": "What's the risk on customer-db?",
  "context": {
    "incident_id": "inc-123",
    "entity_id": "customer-db",
    "risk_score": 85
  }
}
```

**Response**:
```json
{
  "answer": "The customer-db has a risk score of 85/100 (HIGH)...",
  "citations": [
    {
      "source": "platform_get_risk_findings",
      "data": {
        "entity_id": "customer-db",
        "risk_score": 85
      }
    }
  ],
  "proposed_actions": [
    {
      "action": "isolate",
      "confidence": 0.7
    }
  ],
  "sources": [
    {
      "type": "platform_api",
      "endpoint": "platform_get_risk_findings",
      "relevance": 0.9
    }
  ],
  "reasoning_summary": "Based on risk score of 85/100...",
  "confidence": 0.82,
  "data_dependencies": [
    "platform_get_risk_findings",
    "platform_search_entities"
  ],
  "schema_version": "1.0",
  "producer_version": "1.2"
}
```

**Explainability Contract**:
- `sources`: Which Platform objects were used
- `reasoning_summary`: Why this conclusion (not chain-of-thought)
- `confidence`: Score 0.0-1.0
- `data_dependencies`: What data would change this conclusion

---

### 2. POST /advise

**Purpose**: Get action recommendations with reasoning (Dmitry suggests, doesn't execute)

**Request**:
```json
{
  "context": {
    "incident_id": "inc-123",
    "entity_id": "customer-db",
    "risk_score": 85,
    "threat_type": "data_exposure"
  },
  "question": "What should we do about this risk?"
}
```

**Response**:
```json
{
  "recommended_actions": [
    {
      "action": "isolate_entity",
      "target": "customer-db",
      "reason": "High risk score detected with data exposure threat",
      "risk_reduction_estimate": 0.35,
      "confidence": 0.85,
      "priority": "HIGH"
    },
    {
      "action": "increase_monitoring",
      "target": "customer-db",
      "reason": "Monitor for further suspicious activity",
      "risk_reduction_estimate": 0.15,
      "confidence": 0.90,
      "priority": "MEDIUM"
    }
  ],
  "reasoning": "Based on risk score of 85/100 and data exposure threat...",
  "sources": [
    {
      "type": "platform_api",
      "endpoint": "platform_get_finding_details",
      "relevance": 0.95
    }
  ],
  "confidence": 0.82,
  "data_dependencies": [
    "platform_get_finding_details",
    "platform_propose_actions"
  ],
  "schema_version": "1.0",
  "producer_version": "1.2"
}
```

**Action Schema**:
```typescript
{
  action: string;              // Action type
  target: string;              // Target entity
  reason: string;              // Human-readable rationale
  risk_reduction_estimate: number;  // 0.0-1.0
  confidence: number;          // 0.0-1.0
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
}
```

---

### 3. GET /health

**Purpose**: Basic health check

**Response**:
```json
{
  "status": "healthy",
  "version": "1.2",
  "uptime": 3600,
  "timestamp": "2026-02-19T10:30:00Z"
}
```

---

### 4. GET /ready

**Purpose**: Readiness check with dependencies

**Response**:
```json
{
  "ready": true,
  "dependencies": {
    "llm": "healthy",
    "platform": "healthy"
  },
  "timestamp": "2026-02-19T10:30:00Z"
}
```

**Dependency States**:
- `healthy` - Operational
- `unavailable` - Not connected
- `error` - Connection error

---

### 5. GET /version

**Purpose**: Version and capabilities

**Response**:
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

---

### 6. GET /metrics

**Purpose**: Observability metrics

**Response**:
```json
{
  "requests_total": 1523,
  "requests_success": 1498,
  "requests_failed": 25,
  "avg_latency_ms": 245,
  "llm_inference_time_ms": 180,
  "active_sessions": 3,
  "timestamp": "2026-02-19T10:30:00Z"
}
```

---

## Legacy Endpoints (UI Support)

### POST /message

**Purpose**: Legacy Electron UI support

**Request**:
```json
{
  "message": "What's the risk?"
}
```

**Response**:
```json
{
  "text": "Response text",
  "intent": "chat",
  "mode": "security"
}
```

### POST /mode

**Purpose**: Switch cognitive mode

**Request**:
```json
{
  "mode": "security"
}
```

**Modes**: `utility`, `general`, `design`, `developer`, `research`, `security`, `simulation`

### GET /status

**Purpose**: Agent status

**Response**:
```json
{
  "connected": true,
  "mode": "security",
  "pending_confirmations": 0,
  "timestamp": "2026-02-19T10:30:00Z"
}
```

### GET /logs

**Purpose**: Action logs

**Query**: `?limit=50`

**Response**:
```json
{
  "logs": [
    {
      "tool": "platform_get_risk_findings",
      "status": "success",
      "message": "Found 5 high-risk findings",
      "time": "10:30:15",
      "timestamp": "2026-02-19T10:30:15Z"
    }
  ],
  "total": 150
}
```

---

## Schema Versioning

Every response includes:

```json
{
  "schema_version": "1.0",
  "producer_version": "1.2"
}
```

**Schema Version**: API contract version  
**Producer Version**: Dmitry version

---

## Rate Limiting

**Default Limits**:
- 100 requests/minute per tenant
- 1000 requests/hour per tenant

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645267200
```

**Rate Limit Response** (429):
```json
{
  "error": "Rate limit exceeded. Try again in 45 seconds.",
  "retry_after": 45
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "error": "Error message",
  "error_code": "INVALID_REQUEST",
  "schema_version": "1.0",
  "producer_version": "1.2"
}
```

### Error Codes

- `INVALID_REQUEST` - Malformed request
- `UNAUTHORIZED` - Invalid/missing auth
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error
- `SERVICE_UNAVAILABLE` - Dependency unavailable

---

## CORS Support

All endpoints support CORS for browser-based clients:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-Service-Role, X-Tenant-ID
```

---

## Testing

### Health Check

```bash
curl http://127.0.0.1:8765/health
```

### Chat Request

```bash
curl -X POST http://127.0.0.1:8765/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "message": "What is the risk?",
    "context": {"entity_id": "customer-db"}
  }'
```

### Advise Request

```bash
curl -X POST http://127.0.0.1:8765/advise \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "context": {"entity_id": "customer-db", "risk_score": 85},
    "question": "What should we do?"
  }'
```

---

## Production Checklist

### Security
- [ ] JWT secret key configured (`JWT_SECRET_KEY` env var)
- [ ] Rate limiting enabled
- [ ] HTTPS/TLS configured (reverse proxy)
- [ ] Service role validation enabled

### Monitoring
- [ ] Metrics endpoint exposed
- [ ] Health checks configured
- [ ] Logging configured
- [ ] Error tracking enabled

### Performance
- [ ] Connection pooling configured
- [ ] Timeout values tuned
- [ ] Circuit breaker configured
- [ ] Caching enabled

---

## Environment Variables

```bash
# Server
PORT=8765

# Authentication
JWT_SECRET_KEY=your-secret-key-here
TOKEN_EXPIRY_HOURS=24

# Rate Limiting
RATE_LIMIT=100
RATE_WINDOW_SECONDS=60

# Platform Integration
PLATFORM_API_URL=http://localhost:9000
PLATFORM_API_KEY=platform-secret

# Multi-Tenant
TENANT_ID=default
```

---

## Support

**Documentation**: See `docs/API.md` for complete reference  
**Issues**: Report via GitHub issues  
**Contact**: See README.md

---

**Status**: ✅ Production Ready  
**Completeness**: 100% - All MVP endpoints implemented  
**Testing**: Integration tests provided  
**Documentation**: Complete
