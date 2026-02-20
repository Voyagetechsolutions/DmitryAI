# Changelog

All notable changes to Dmitry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-02-19

### Added - Service Mesh Integration
- **Service Registry** - Registration with Platform on startup
- **Heartbeat Mechanism** - Send heartbeat every 10 seconds
- **Health Endpoints** - `/health`, `/ready`, `/live` for Kubernetes
- **Shared Contracts** - Pydantic models matching Platform schema
- **AdviseRequest/AdviseResponse** - Standardized contract for action recommendations
- **Graceful Shutdown** - Deregister from Platform on shutdown

### Changed
- `/advise` endpoint now accepts `AdviseRequest` model (breaking change)
- `/advise` endpoint now returns `AdviseResponse` model (breaking change)
- `/health` endpoint now returns `ServiceHealth` model with detailed checks
- `AgentServer.__init__()` now accepts optional `platform_url` parameter

### Files Added
- `MarkX/shared/contracts/dmitry.py` - Dmitry-specific contracts
- `MarkX/shared/contracts/base.py` - Base contracts
- `MarkX/shared/registry.py` - Service registration
- `MarkX/test_service_mesh.py` - Service mesh integration tests

### Test Results
- 11/12 tests passing (1 requires Platform)
- Service mesh integration verified

---

## [1.1.0] - 2026-02-18

### Added - Production Trust Enforcement
- **Call Ledger** - Immutable audit trail with SHA-256 hashes
- **Action Safety Gate** - 15 allow-listed actions with evidence thresholds
- **Input Sanitizer** - Strips secrets, redacts PII, prevents SQL injection
- **Output Validator** - Strict schema validation before returning responses
- **Evidence Chain** - Links event_id → finding_id → call_ids
- **Structured Actions** - JSON parsing with text fallback

### Security Guarantees
- ✅ Cannot lie about sources (ledger-enforced)
- ✅ Cannot recommend invalid actions (allow-list)
- ✅ Cannot leak PII (automatic redaction)
- ✅ Cannot return malformed data (schema validation)
- ✅ Cannot lose traceability (evidence chain)

### Files Added
- `MarkX/core/call_ledger.py` - Immutable audit trail
- `MarkX/core/action_safety.py` - Action validation
- `MarkX/core/input_sanitizer.py` - Input sanitation
- `MarkX/core/output_validator.py` - Output validation
- `MarkX/core/evidence_chain.py` - Evidence traceability
- `MarkX/core/structured_actions.py` - JSON action parsing
- `MarkX/test_complete_loop.py` - End-to-end integration test

### Changed
- `MarkX/agent/server.py` - Integrated all trust enforcement components
- `MarkX/tools/platform/platform_client.py` - Integrated call ledger
- `/chat` endpoint now includes evidence chain in responses
- `/advise` endpoint now validates actions against safety gate

### Test Results
- 7/7 production component tests passing
- Complete loop verified (event → finding → action)

---

## [1.0.0] - 2026-02-17

### Added - Platform Integration
- **Platform Client** - Resilient client with circuit breaker
- **Circuit Breaker** - Fail fast, auto-recovery after cooldown
- **Retry Logic** - Exponential backoff with jitter
- **Connection Pooling** - Efficient connection reuse
- **5 Platform Tools** - get_risk_findings, get_finding_details, search_entities, propose_actions, execute_action

### Features
- Clean architecture (Dmitry only knows Platform, not PDRI/Aegis)
- Fault tolerance (graceful degradation with cached responses)
- JWT authentication with service roles
- Rate limiting and request throttling

### Files Added
- `MarkX/tools/platform/platform_client.py` - Resilient Platform client
- `MarkX/tools/platform/platform_tools.py` - 5 Platform tools
- `MarkX/tools/platform/circuit_breaker.py` - Fault tolerance

### Endpoints
- `POST /message` - Legacy UI chat
- `POST /chat` - Platform chat with context
- `POST /advise` - Action recommendations
- `POST /mode` - Switch cognitive mode
- `POST /confirm` - Confirm/deny action
- `GET /logs` - Action logs
- `GET /status` - Agent status
- `GET /health` - Basic health check
- `GET /ready` - Readiness check
- `GET /version` - Version info
- `GET /metrics` - Observability metrics

---

## [0.9.0] - 2026-02-15

### Added - MVP Foundation
- Basic agent server with HTTP API
- LLM integration (OpenAI/Anthropic)
- Cognitive mode switching
- Action confirmation workflow
- Basic logging and metrics

### Files Added
- `MarkX/agent/server.py` - HTTP server
- `MarkX/agent/auth.py` - JWT authentication
- `MarkX/core/audit_log.py` - Audit logging

---

## [Unreleased]

### Planned
- OpenTelemetry tracing integration
- Redis caching for Platform responses
- Enhanced CI/CD pipeline with security scanning
- Pre-commit hooks for code quality
- Performance benchmarks
- Load testing suite

---

## Migration Guides

### Migrating to 1.2.0 (Service Mesh)

**Breaking Changes:**
- `/advise` endpoint now requires `AdviseRequest` format
- `/advise` endpoint returns `AdviseResponse` format

**Before (1.1.0):**
```json
POST /advise
{
  "context": {"entity_id": "db-1", "risk_score": 85},
  "question": "What should we do?"
}
```

**After (1.2.0):**
```json
POST /advise
{
  "finding_id": "find-456",
  "tenant_id": "tenant-1",
  "entity": {
    "type": "database",
    "id": "db-1",
    "name": "Database 1"
  },
  "severity": "high",
  "risk_score": 85.0,
  "evidence_refs": ["evt-123"]
}
```

**Server Initialization:**
```python
# Before
server = AgentServer(port=8765)

# After (with Platform registration)
server = AgentServer(port=8765, platform_url="http://platform:8000")
```

### Migrating to 1.1.0 (Trust Enforcement)

**No Breaking Changes** - All existing endpoints remain compatible.

**New Features:**
- All responses now include `evidence_chain`
- All responses now include verified `citations` from call ledger
- All actions now include `evidence_required` field

---

## Version History

- **1.2.0** (2026-02-19) - Service Mesh Integration
- **1.1.0** (2026-02-18) - Production Trust Enforcement
- **1.0.0** (2026-02-17) - Platform Integration
- **0.9.0** (2026-02-15) - MVP Foundation

---

**For detailed changes, see commit history on GitHub.**
