# Dmitry Architecture Flow

**Visual guide to how all components connect**

---

## Startup Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Load Configuration                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  config.py (Pydantic Settings)                        │  │
│  │  • Reads .env file                                    │  │
│  │  • Validates settings                                 │  │
│  │  • Returns type-safe config                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Setup Logging                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/logging.py (structlog)                          │  │
│  │  • Configures log level                               │  │
│  │  • Sets up file/console output                        │  │
│  │  • Enables JSON format                                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Setup Tracing (if enabled)                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/tracing.py (OpenTelemetry)                      │  │
│  │  • Configures OTLP exporter                           │  │
│  │  • Sets up span processors                            │  │
│  │  • Enables distributed tracing                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Start HTTP Server                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  agent/server.py (AgentServer)                        │  │
│  │  • Starts HTTP server on configured port              │  │
│  │  • Registers with Platform (if URL set)               │  │
│  │  • Starts heartbeat thread                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Configure Orchestrator (if available)              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  dmitry_operator.py (DmitryOrchestrator)              │  │
│  │  • Sets up LLM integration                            │  │
│  │  • Configures knowledge retrieval                     │  │
│  │  • Enables action execution                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Server Running ✅                         │
│  • HTTP API available on port 8765                          │
│  • All endpoints active                                     │
│  • Logging to console and file                              │
│  • Tracing enabled (if configured)                          │
│  • Platform registration complete (if configured)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Incoming HTTP Request                                      │
│  POST /advise                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Logging                                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/logging.py                                      │  │
│  │  logger.info("request_received", request_id="...")    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Tracing (if enabled)                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/tracing.py                                      │  │
│  │  with trace_request("req-123", "/advise"):            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Input Sanitization                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/input_sanitizer.py                              │  │
│  │  • Strip secrets (API keys, passwords)                │  │
│  │  • Redact PII (emails, SSNs)                          │  │
│  │  • Prevent SQL injection                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Process Request                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  agent/server.py → dmitry_operator.py                 │  │
│  │  • Call Platform APIs                                 │  │
│  │  • Call LLM                                            │  │
│  │  • Generate recommendations                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Platform Calls (with tracing)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  tools/platform/platform_client.py                    │  │
│  │  • Circuit breaker check                              │  │
│  │  • Make API call with retry                           │  │
│  │  • Record in call ledger                              │  │
│  │  • Trace span created                                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Call Ledger                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/call_ledger.py                                  │  │
│  │  • Record call with SHA-256 hashes                    │  │
│  │  • Store args and response                            │  │
│  │  • Generate call_id                                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 7: Action Safety Validation                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/action_safety.py                                │  │
│  │  • Check action against allow-list                    │  │
│  │  • Validate evidence threshold                        │  │
│  │  • Set approval requirements                          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 8: Evidence Chain                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/evidence_chain.py                               │  │
│  │  • Link event_id → finding_id → call_ids             │  │
│  │  • Enrich actions with evidence                       │  │
│  │  • Validate chain completeness                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 9: Output Validation                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  core/output_validator.py                             │  │
│  │  • Validate response schema                           │  │
│  │  • Check required fields                              │  │
│  │  • Verify value ranges                                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 10: Send Response                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  agent/server.py                                      │  │
│  │  • Log response                                        │  │
│  │  • Close trace span                                   │  │
│  │  • Return JSON                                         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Response Sent ✅                                            │
│  • Status: 200 OK                                           │
│  • Body: AdviseResponse (validated)                         │
│  • Logs: Structured JSON                                    │
│  • Trace: Complete span                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Dependencies

```
main.py
  ├─ config.py (Configuration)
  │   └─ .env file
  │
  ├─ core/logging.py (Logging)
  │   └─ structlog
  │
  ├─ core/tracing.py (Tracing)
  │   └─ OpenTelemetry
  │
  └─ agent/server.py (HTTP Server)
      ├─ core/input_sanitizer.py
      ├─ core/output_validator.py
      ├─ core/call_ledger.py
      ├─ core/action_safety.py
      ├─ core/evidence_chain.py
      ├─ core/structured_actions.py
      │
      ├─ tools/platform/platform_client.py
      │   ├─ tools/platform/circuit_breaker.py
      │   └─ core/call_ledger.py
      │
      ├─ shared/registry.py (Service Registration)
      │   └─ shared/contracts/
      │
      └─ dmitry_operator.py (Orchestrator)
          ├─ llm.py
          ├─ modes/
          └─ knowledge/
```

---

## Data Flow

```
┌──────────────┐
│  User/Client │
└──────────────┘
       │
       │ HTTP Request
       ▼
┌──────────────────────────────────────────────────────────┐
│                    agent/server.py                       │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. Log request (core/logging.py)                  │  │
│  │  2. Start trace span (core/tracing.py)             │  │
│  │  3. Sanitize input (core/input_sanitizer.py)       │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              dmitry_operator.py                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. Process with LLM                               │  │
│  │  2. Call Platform APIs                             │  │
│  │  3. Generate recommendations                        │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│         tools/platform/platform_client.py                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. Check circuit breaker                          │  │
│  │  2. Make API call with retry                       │  │
│  │  3. Record in call ledger                          │  │
│  │  4. Trace Platform call                            │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                 core/call_ledger.py                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │  • Store call with SHA-256 hashes                  │  │
│  │  • Generate call_id                                │  │
│  │  • Immutable audit trail                           │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              Back to agent/server.py                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │  1. Validate actions (core/action_safety.py)       │  │
│  │  2. Build evidence chain (core/evidence_chain.py)  │  │
│  │  3. Validate output (core/output_validator.py)     │  │
│  │  4. Log response (core/logging.py)                 │  │
│  │  5. Close trace span (core/tracing.py)             │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
       │
       │ HTTP Response
       ▼
┌──────────────┐
│  User/Client │
└──────────────┘
```

---

## Summary

**All components are connected through main.py:**

1. **Configuration** → Loaded first, used by all components
2. **Logging** → Set up second, used throughout request flow
3. **Tracing** → Set up third, wraps all operations
4. **HTTP Server** → Started fourth, handles all requests
5. **Trust Enforcement** → Integrated in server, validates all I/O
6. **Platform Integration** → Called by server, records in ledger
7. **Service Mesh** → Automatic registration and heartbeat

**Everything flows through main.py and is fully integrated!** ✅

---

**To see it in action:**
```bash
cd MarkX
python main.py
```

**Then make a request:**
```bash
curl http://127.0.0.1:8765/health
```

**Watch the logs to see all components working together!**
