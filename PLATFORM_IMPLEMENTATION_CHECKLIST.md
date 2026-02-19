# Platform Implementation Checklist

## Overview

Dmitry has been decoupled from PDRI and Aegis. Now the Platform needs to be implemented to orchestrate all three services.

## Platform Responsibilities

The Platform is the ONLY component that knows about all three services:
- Receives events from PDRI (risk scores, alerts)
- Receives events from Aegis (detections, findings)
- Stores everything in Neo4j
- Provides unified API for Dmitry

## Required Endpoints

### Health & Status
- [ ] `GET /api/v1/health`
  - Returns Platform health
  - Returns status of PDRI, Aegis, Neo4j
  - Used by Dmitry to check connectivity

### Risk Findings
- [ ] `GET /api/v1/risk-findings`
  - Query risk findings with filters
  - Filters: risk_level, entity_type, date_range
  - Returns paginated results
  - Aggregates data from PDRI + Aegis + Neo4j

- [ ] `GET /api/v1/risk-findings/{id}`
  - Get detailed finding information
  - Includes risk factors, exposure paths, recommendations
  - Enriched with Neo4j relationship data

### Entity Search
- [ ] `GET /api/v1/entities/search?q={query}`
  - Search for entities across platform
  - Searches Neo4j graph
  - Returns entities with risk scores
  - Supports filters: entity_type, risk_level

### Actions
- [ ] `GET /api/v1/risk-findings/{id}/actions`
  - Get recommended actions for a finding
  - Uses PDRI risk data + Aegis detections
  - Returns prioritized action list

- [ ] `POST /api/v1/actions/execute`
  - Execute a security action
  - Routes to appropriate service (Aegis for blocks, etc.)
  - Returns execution result
  - Logs to audit trail

### Event Ingestion
- [ ] `POST /api/v1/events`
  - Accept events from PDRI and Aegis
  - Validate event schema
  - Store in Neo4j
  - Trigger alerts if needed
  - Used by PDRI and Aegis to send events

## Event Schemas

### PDRI Event Schema
```json
{
  "source": "pdri",
  "event_type": "risk_score_update",
  "timestamp": "2026-02-19T10:30:00Z",
  "entity_id": "customer-db",
  "risk_score": 85,
  "risk_level": "HIGH",
  "factors": ["..."],
  "metadata": {}
}
```

### Aegis Event Schema
```json
{
  "source": "aegis",
  "event_type": "ai_tool_detection",
  "timestamp": "2026-02-19T10:30:00Z",
  "actor": "user@example.com",
  "target": "customer-db",
  "tool_name": "ChatGPT",
  "severity": "HIGH",
  "metadata": {}
}
```

## Neo4j Schema

### Nodes
- [ ] Entity (database, system, user, etc.)
- [ ] RiskFinding (from PDRI or Aegis)
- [ ] Action (recommended or executed)
- [ ] Event (audit trail)

### Relationships
- [ ] Entity -[HAS_RISK]-> RiskFinding
- [ ] RiskFinding -[RECOMMENDS]-> Action
- [ ] Entity -[EXPOSES]-> Entity (exposure paths)
- [ ] Event -[AFFECTS]-> Entity

## Authentication

- [ ] JWT-based authentication
- [ ] API key support for service-to-service
- [ ] Rate limiting per client
- [ ] Audit logging for all requests

## Configuration

Platform needs these environment variables:

```bash
# Platform
PLATFORM_PORT=9000
PLATFORM_HOST=0.0.0.0

# PDRI Connection
PDRI_API_URL=http://localhost:8000
PDRI_API_KEY=secret

# Aegis Connection
AEGIS_API_URL=http://localhost:8001
AEGIS_API_KEY=secret

# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Security
JWT_SECRET=generate_random_secret
API_RATE_LIMIT=100

# Logging
LOG_LEVEL=INFO
AUDIT_LOG_PATH=logs/platform-audit.log
```

## Implementation Phases

### Phase 1: Core API (Week 1)
- [ ] Set up FastAPI/Flask project
- [ ] Implement health endpoint
- [ ] Implement event ingestion endpoint
- [ ] Set up Neo4j connection
- [ ] Basic authentication

### Phase 2: Risk Findings (Week 1-2)
- [ ] Implement risk findings query endpoint
- [ ] Implement finding details endpoint
- [ ] Connect to PDRI for real-time data
- [ ] Store findings in Neo4j

### Phase 3: Entity Search (Week 2)
- [ ] Implement entity search endpoint
- [ ] Neo4j graph queries
- [ ] Risk score enrichment

### Phase 4: Actions (Week 2-3)
- [ ] Implement action recommendation endpoint
- [ ] Implement action execution endpoint
- [ ] Connect to Aegis for action execution
- [ ] Audit logging

### Phase 5: Integration (Week 3)
- [ ] Test with Dmitry
- [ ] Test with PDRI event flow
- [ ] Test with Aegis event flow
- [ ] End-to-end testing

### Phase 6: Production Ready (Week 4)
- [ ] Error handling and retries
- [ ] Rate limiting
- [ ] Monitoring and metrics
- [ ] Documentation
- [ ] Deployment scripts

## Testing Checklist

### Unit Tests
- [ ] Event ingestion validation
- [ ] Risk finding queries
- [ ] Entity search
- [ ] Action execution

### Integration Tests
- [ ] Dmitry → Platform communication
- [ ] PDRI → Platform event flow
- [ ] Aegis → Platform event flow
- [ ] Neo4j data persistence

### Load Tests
- [ ] 100 requests/second
- [ ] 1000 concurrent connections
- [ ] Event ingestion throughput

## Monitoring

- [ ] Prometheus metrics endpoint
- [ ] Request latency tracking
- [ ] Error rate monitoring
- [ ] Service health checks
- [ ] Neo4j query performance

## Documentation

- [ ] API documentation (OpenAPI/Swagger)
- [ ] Integration guide for Dmitry
- [ ] Integration guide for PDRI
- [ ] Integration guide for Aegis
- [ ] Deployment guide
- [ ] Troubleshooting guide

## Deployment

- [ ] Docker container
- [ ] Docker Compose for local dev
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline
- [ ] Health check endpoints
- [ ] Graceful shutdown

## Success Criteria

✅ Dmitry can query risk findings through Platform
✅ PDRI can send events to Platform
✅ Aegis can send events to Platform
✅ All data persists in Neo4j
✅ Actions execute through Platform
✅ Services run independently
✅ < 100ms API response time (p95)
✅ 99.9% uptime

## Timeline

- Week 1: Core API + Event Ingestion
- Week 2: Risk Findings + Entity Search
- Week 3: Actions + Integration Testing
- Week 4: Production Hardening + Deployment

Total: 4 weeks to production-ready Platform

## Resources Needed

- 1 Backend Engineer (Python/FastAPI)
- 1 DevOps Engineer (Docker/K8s)
- Access to Neo4j instance
- Access to PDRI and Aegis APIs
- Staging environment for testing

## Questions to Answer

1. What's the expected event volume from PDRI/Aegis?
2. What's the retention policy for events in Neo4j?
3. What's the SLA for API response times?
4. What's the disaster recovery plan?
5. What's the backup strategy for Neo4j?

---

**Status**: Ready to Implement
**Owner**: Platform Team
**Priority**: P0 (Blocking Dmitry deployment)
**Estimated Effort**: 4 weeks
