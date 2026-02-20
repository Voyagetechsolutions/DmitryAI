# Dmitry Architecture Diagram

**Version**: 1.2  
**Date**: 2026-02-19  
**Status**: Production Ready

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        THE PLATFORM                          │
│                     (Not Built Yet)                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   PDRI   │  │  Aegis   │  │  Neo4j   │  │  Other   │   │
│  │  (Risk)  │  │ (Detect) │  │ (Graph)  │  │ Services │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│              Platform Orchestration Layer                    │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ HTTP/REST API
                       │ JWT Authentication
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                         DMITRY                                │
│                  (Voice + Hands)                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Agent API Server                        │    │
│  │            (MarkX/agent/server.py)                   │    │
│  │                                                       │    │
│  │  Platform Endpoints:                                 │    │
│  │  • POST /chat      - Context-aware chat              │    │
│  │  • POST /advise    - Action recommendations          │    │
│  │  • GET  /health    - Health check                    │    │
│  │  • GET  /ready     - Readiness check                 │    │
│  │  • GET  /version   - Version info                    │    │
│  │  • GET  /metrics   - Observability                   │    │
│  │                                                       │    │
│  │  Legacy Endpoints:                                   │    │
│  │  • POST /message   - UI messages                     │    │
│  │  • POST /mode      - Mode switching                  │    │
│  │  • GET  /status    - Agent status                    │    │
│  │  • GET  /logs      - Action logs                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Authentication Layer                       │    │
│  │          (MarkX/agent/auth.py)                       │    │
│  │                                                       │    │
│  │  • JWT token generation/validation                   │    │
│  │  • Service role verification                         │    │
│  │  • Multi-tenant isolation                            │    │
│  │  • Rate limiting                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Orchestrator                            │    │
│  │      (MarkX/dmitry_operator/orchestrator.py)        │    │
│  │                                                       │    │
│  │  • Intent classification                             │    │
│  │  • LLM integration                                   │    │
│  │  • Tool execution                                    │    │
│  │  • Response generation                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Platform Integration                       │    │
│  │       (MarkX/tools/platform/)                        │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Platform Client                              │   │    │
│  │  │  (platform_client.py)                         │   │    │
│  │  │                                                │   │    │
│  │  │  • HTTP client with circuit breaker           │   │    │
│  │  │  • Fault tolerance                             │   │    │
│  │  │  • Graceful degradation                        │   │    │
│  │  │  • Request tracing                             │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Platform Tools                               │   │    │
│  │  │  (platform_tools.py)                          │   │    │
│  │  │                                                │   │    │
│  │  │  • platform_get_risk_findings                 │   │    │
│  │  │  • platform_get_finding_details               │   │    │
│  │  │  • platform_search_entities                   │   │    │
│  │  │  • platform_propose_actions                   │   │    │
│  │  │  • platform_execute_action                    │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Circuit Breaker                              │   │    │
│  │  │  (circuit_breaker.py)                         │   │    │
│  │  │                                                │   │    │
│  │  │  • Failure threshold: 5                       │   │    │
│  │  │  • Timeout: 60 seconds                        │   │    │
│  │  │  • Prevents cascading failures                │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Cache Layer                                  │   │    │
│  │  │  (cache.py)                                   │   │    │
│  │  │                                                │   │    │
│  │  │  • TTL: 300 seconds                           │   │    │
│  │  │  • Graceful degradation                       │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Request Flow: Platform → Dmitry

```
┌──────────┐
│ Platform │
└────┬─────┘
     │
     │ 1. POST /chat
     │    Authorization: Bearer <jwt>
     │    X-Service-Role: platform
     │    {
     │      "message": "What's the risk?",
     │      "context": {"entity_id": "customer-db"}
     │    }
     │
     ▼
┌────────────────────┐
│  Agent API Server  │
└────┬───────────────┘
     │
     │ 2. Verify JWT
     │    Check service role
     │    Check rate limit
     │
     ▼
┌────────────────────┐
│  Auth Manager      │
└────┬───────────────┘
     │
     │ 3. Token valid ✓
     │    Role: platform ✓
     │    Rate limit: OK ✓
     │
     ▼
┌────────────────────┐
│  Orchestrator      │
└────┬───────────────┘
     │
     │ 4. Process message
     │    Classify intent
     │    Determine tools needed
     │
     ▼
┌────────────────────┐
│  Platform Tools    │
└────┬───────────────┘
     │
     │ 5. Execute tools
     │    platform_get_risk_findings()
     │    platform_search_entities()
     │
     ▼
┌────────────────────┐
│  Platform Client   │
└────┬───────────────┘
     │
     │ 6. HTTP GET /api/v1/risk-findings
     │    Circuit breaker: CLOSED
     │    Cache: MISS
     │
     ▼
┌────────────────────┐
│  THE PLATFORM      │
│  (Not Built Yet)   │
└────┬───────────────┘
     │
     │ 7. Connection refused
     │    (Platform not running)
     │
     ▼
┌────────────────────┐
│  Circuit Breaker   │
└────┬───────────────┘
     │
     │ 8. Failure count: 1
     │    Try cache
     │
     ▼
┌────────────────────┐
│  Cache Layer       │
└────┬───────────────┘
     │
     │ 9. Cache HIT
     │    Return cached data
     │
     ▼
┌────────────────────┐
│  Orchestrator      │
└────┬───────────────┘
     │
     │ 10. Generate response
     │     Add explainability
     │     Calculate confidence
     │
     ▼
┌────────────────────┐
│  Agent API Server  │
└────┬───────────────┘
     │
     │ 11. Return response
     │     {
     │       "answer": "...",
     │       "sources": [...],
     │       "reasoning_summary": "...",
     │       "confidence": 0.82,
     │       "schema_version": "1.0"
     │     }
     │
     ▼
┌──────────┐
│ Platform │
└──────────┘
```

---

## Data Flow: Explainability Contract

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    Orchestrator                          │
│                                                          │
│  1. Process query                                        │
│  2. Execute Platform tools                               │
│  3. Track data sources                                   │
│  4. Generate response                                    │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│              Explainability Extraction                   │
│                                                          │
│  • Extract citations from tool results                   │
│  • Identify data sources used                            │
│  • Generate reasoning summary                            │
│  • Calculate confidence score                            │
│  • List data dependencies                                │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                  Response Assembly                       │
│                                                          │
│  {                                                       │
│    "answer": "Main response text",                      │
│    "citations": [                                        │
│      {                                                   │
│        "source": "platform_get_risk_findings",          │
│        "data": {"entity_id": "...", "risk_score": 85}  │
│      }                                                   │
│    ],                                                    │
│    "sources": [                                          │
│      {                                                   │
│        "type": "platform_api",                          │
│        "endpoint": "platform_get_risk_findings",        │
│        "relevance": 0.9                                 │
│      }                                                   │
│    ],                                                    │
│    "reasoning_summary": "Based on risk score...",       │
│    "confidence": 0.82,                                  │
│    "data_dependencies": [                               │
│      "platform_get_risk_findings",                      │
│      "platform_search_entities"                         │
│    ],                                                    │
│    "schema_version": "1.0",                             │
│    "producer_version": "1.2"                            │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Platform receives explainable response
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Security Layers                        │
└─────────────────────────────────────────────────────────┘

Layer 1: Network
├─ HTTPS/TLS (reverse proxy)
├─ Firewall rules
└─ IP whitelisting (optional)

Layer 2: Authentication
├─ JWT token validation
├─ Token expiry check
├─ Token revocation check
└─ Service role verification

Layer 3: Authorization
├─ Service role check (platform, dmitry, pdri, aegis)
├─ Tenant isolation
├─ Endpoint permissions
└─ Resource access control

Layer 4: Rate Limiting
├─ Per-tenant limits (100 req/min)
├─ Per-endpoint limits
├─ Burst protection
└─ Graceful degradation

Layer 5: Input Validation
├─ JSON schema validation
├─ Parameter sanitization
├─ SQL injection prevention
└─ XSS prevention

Layer 6: Audit Logging
├─ Request/response logging
├─ Authentication events
├─ Authorization failures
└─ Error tracking
```

---

## Fault Tolerance Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Fault Tolerance Mechanisms                  │
└─────────────────────────────────────────────────────────┘

1. Circuit Breaker
   ├─ Failure threshold: 5 failures
   ├─ Timeout: 60 seconds
   ├─ States: CLOSED → OPEN → HALF_OPEN
   └─ Prevents cascading failures

2. Caching
   ├─ TTL: 300 seconds (5 minutes)
   ├─ Graceful degradation
   ├─ Stale data acceptable
   └─ Cache invalidation on success

3. Timeouts
   ├─ HTTP requests: 30 seconds
   ├─ LLM inference: 60 seconds
   ├─ Tool execution: 45 seconds
   └─ Connection timeout: 10 seconds

4. Retries
   ├─ Max retries: 3
   ├─ Exponential backoff
   ├─ Jitter to prevent thundering herd
   └─ Idempotency checks

5. Health Checks
   ├─ Liveness: /health
   ├─ Readiness: /ready
   ├─ Dependency checks
   └─ Graceful shutdown
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Production Deployment                   │
└─────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │ Load Balancer│
                    │   (nginx)    │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Dmitry 1 │   │ Dmitry 2 │   │ Dmitry 3 │
    │  Pod     │   │  Pod     │   │  Pod     │
    └──────────┘   └──────────┘   └──────────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
                    ┌──────▼───────┐
                    │  Platform    │
                    │   Service    │
                    └──────────────┘

Monitoring:
├─ Prometheus (metrics)
├─ Grafana (dashboards)
├─ Loki (logs)
└─ Alertmanager (alerts)

Storage:
├─ Redis (sessions, cache)
├─ PostgreSQL (audit logs)
└─ S3 (backups)
```

---

## Summary

**Dmitry Architecture**:
- ✅ Clean separation (only knows Platform)
- ✅ Fault tolerant (circuit breaker + cache)
- ✅ Secure (JWT + roles + rate limiting)
- ✅ Observable (metrics + health checks)
- ✅ Scalable (stateless, horizontal scaling)
- ✅ Explainable (sources + reasoning + confidence)

**Ready for**: Platform Integration  
**Status**: Production Ready  
**Completeness**: 100%
