# PDRI → Dmitry Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         PDRI Platform                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              PDRI DmitryClient                          │    │
│  │  (integrations/dmitry_client.py)                       │    │
│  │                                                          │    │
│  │  Methods:                                               │    │
│  │  • send_message()                                       │    │
│  │  • analyze_threat()                                     │    │
│  │  • get_strategic_advice()                               │    │
│  │  • check_compliance()                                   │    │
│  │  • format_for_natural_language()                        │    │
│  │  • assess_ai_model_risk()                               │    │
│  │  • + 10 more methods                                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            │ HTTP/JSON                           │
│                            │ (requests library)                  │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Dmitry AI Backend                           │
│                   (http://127.0.0.1:8765)                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           AgentServer (HTTP API)                        │    │
│  │           MarkX/agent/server.py                         │    │
│  │                                                          │    │
│  │  Endpoints:                                             │    │
│  │  • POST /message    → Process query                     │    │
│  │  • POST /mode       → Switch cognitive mode             │    │
│  │  • GET  /status     → Health check                      │    │
│  │  • GET  /logs       → Action history                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Orchestrator (Brain Router)                     │    │
│  │         MarkX/dmitry_operator/orchestrator.py           │    │
│  │                                                          │    │
│  │  • Classifies intent (Transform vs Act)                │    │
│  │  • Routes to LLM or Tools                               │    │
│  │  • Manages execution flow                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                     │
│              ┌─────────────┴─────────────┐                      │
│              ▼                           ▼                       │
│  ┌──────────────────────┐    ┌──────────────────────┐         │
│  │   LLM Integration    │    │   Tool Execution     │         │
│  │   MarkX/llm.py       │    │   MarkX/dmitry_      │         │
│  │                      │    │   operator/tools.py  │         │
│  │  • OpenRouter API    │    │                      │         │
│  │  • Prompt injection  │    │  • OS operations     │         │
│  │    detection         │    │  • File operations   │         │
│  │  • Mode-aware        │    │  • Browser control   │         │
│  │    prompts           │    │  • Security tools    │         │
│  │  • RAG context       │    │                      │         │
│  └──────────────────────┘    └──────────────────────┘         │
│              │                           │                       │
│              └─────────────┬─────────────┘                      │
│                            ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Mode Manager                               │    │
│  │              MarkX/modes/mode_manager.py                │    │
│  │                                                          │    │
│  │  7 Cognitive Modes:                                     │    │
│  │  • Utility      • General    • Design                   │    │
│  │  • Developer    • Research   • Simulation               │    │
│  │  • Security (7 sub-modes)                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Security Mode (Enhanced)                        │    │
│  │         MarkX/modes/security_mode_enhanced.py           │    │
│  │                                                          │    │
│  │  Sub-Modes:                                             │    │
│  │  1. Threat Hunting                                      │    │
│  │  2. Vulnerability Assessment                            │    │
│  │  3. AI Security Audit                                   │    │
│  │  4. Compliance Audit                                    │    │
│  │  5. Incident Response                                   │    │
│  │  6. Cloud Security Posture                              │    │
│  │  7. Penetration Testing                                 │    │
│  │                                                          │    │
│  │  Tools:                                                 │    │
│  │  • Threat Intel Lookup                                  │    │
│  │  • Vulnerability Scanner                                │    │
│  │  • Compliance Checker                                   │    │
│  │  • AI Security Audit                                    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

```
PDRI Application
    │
    │ 1. Call dmitry.send_message("Analyze threat X")
    ▼
DmitryClient
    │
    │ 2. HTTP POST /message
    │    {"message": "Analyze threat X"}
    ▼
AgentServer
    │
    │ 3. Route to Orchestrator
    ▼
Orchestrator
    │
    │ 4. Classify intent → ACT (security operation)
    │ 5. Switch to Security Mode
    ▼
LLM Integration
    │
    │ 6. Check for prompt injection
    │ 7. Build security-aware prompt
    │ 8. Call OpenRouter API
    ▼
Security Mode
    │
    │ 9. Execute threat analysis
    │ 10. Use threat intel tools
    ▼
Response
    │
    │ 11. Format response
    │ 12. Return JSON
    ▼
DmitryClient
    │
    │ 13. Parse response
    │ 14. Return to PDRI
    ▼
PDRI Application
```

## Data Flow

```
┌──────────────────────────────────────────────────────────┐
│ PDRI Request                                              │
├──────────────────────────────────────────────────────────┤
│ {                                                         │
│   "message": "Analyze this threat: Multiple failed       │
│               login attempts from 192.168.1.100"         │
│ }                                                         │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ Dmitry Processing                                         │
├──────────────────────────────────────────────────────────┤
│ 1. Prompt injection check → PASS                         │
│ 2. Intent classification → ACT (security)                │
│ 3. Mode switch → Security Mode                           │
│ 4. LLM analysis → Generate threat assessment             │
│ 5. Tool execution → Lookup IOC reputation                │
│ 6. Format response → Natural language                    │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ Dmitry Response                                           │
├──────────────────────────────────────────────────────────┤
│ {                                                         │
│   "text": "Threat Analysis:\n                            │
│            - Classification: Brute Force Attack\n         │
│            - Risk Level: HIGH\n                           │
│            - IP Reputation: Known malicious\n             │
│            - Recommended Actions:\n                       │
│              1. Block IP immediately\n                    │
│              2. Review affected accounts\n                │
│              3. Enable MFA\n                              │
│              4. Monitor for similar patterns",            │
│   "intent": "action",                                     │
│   "mode": "security",                                     │
│   "tool_executed": "threat_intel_lookup",                 │
│   "tool_result": "IOC analyzed: 192.168.1.100"            │
│ }                                                         │
└──────────────────────────────────────────────────────────┘
```

## Integration Points

```
┌─────────────────────────────────────────────────────────┐
│ Integration Layer                                        │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  PDRI Side                    Dmitry Side                │
│  ─────────                    ───────────                │
│                                                           │
│  DmitryClient                 AgentServer                │
│  └─ send_message()            └─ POST /message           │
│  └─ switch_mode()             └─ POST /mode              │
│  └─ get_status()              └─ GET /status             │
│  └─ get_logs()                └─ GET /logs               │
│                                                           │
│  Strategic Methods            Orchestrator               │
│  └─ analyze_threat()          └─ Intent classification   │
│  └─ get_strategic_advice()    └─ LLM routing             │
│  └─ check_compliance()        └─ Tool execution          │
│                                                           │
│  Security Methods             Security Mode              │
│  └─ lookup_threat_intel()     └─ Threat hunting          │
│  └─ assess_ai_model_risk()    └─ AI security audit       │
│  └─ analyze_vulnerability()   └─ Vuln assessment         │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## File Locations

```
PDRI Project
└── integrations/
    └── dmitry_client.py          ← Create this file
        └── DmitryClient class    ← Copy from integration brief

Dmitry Project
├── MarkX/
│   ├── agent/
│   │   └── server.py             ← HTTP API server
│   ├── dmitry_operator/
│   │   ├── orchestrator.py       ← Brain router
│   │   └── tools.py              ← Action tools
│   ├── modes/
│   │   ├── mode_manager.py       ← Mode management
│   │   └── security_mode_enhanced.py  ← Security mode
│   ├── tools/
│   │   └── security/             ← Security tools
│   │       ├── threat_intel_lookup.py
│   │       ├── compliance_checker.py
│   │       └── ai_security_audit.py
│   ├── llm.py                    ← LLM integration
│   └── run_dmitry.py             ← Launcher
```

## Network Communication

```
┌──────────────┐                    ┌──────────────┐
│     PDRI     │                    │   Dmitry     │
│  Application │                    │   Backend    │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │ HTTP POST /message                │
       │ Content-Type: application/json    │
       │ {"message": "query"}              │
       ├──────────────────────────────────>│
       │                                   │
       │                                   │ Process
       │                                   │ (50-500ms)
       │                                   │
       │ HTTP 200 OK                       │
       │ Content-Type: application/json    │
       │ {"text": "response", ...}         │
       │<──────────────────────────────────┤
       │                                   │
```

## Error Handling Flow

```
PDRI Request
    │
    ▼
Try Connection
    │
    ├─ Success ──────────────────────────┐
    │                                     │
    └─ ConnectionError ──> Retry (3x) ───┤
    └─ Timeout ──────────> Log Error ────┤
    └─ Other Error ──────> Log Error ────┤
                                          │
                                          ▼
                                    Parse Response
                                          │
                                          ├─ intent: "chat" ──> Normal response
                                          ├─ intent: "action" ─> Action executed
                                          ├─ intent: "error" ──> Handle error
                                          └─ security_alert ───> Security alert
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Production Environment                                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐         ┌──────────────────┐     │
│  │  PDRI Server     │         │  Dmitry Server   │     │
│  │  (Your infra)    │         │  (Port 8765)     │     │
│  │                  │         │                  │     │
│  │  DmitryClient ───┼────────>│  AgentServer     │     │
│  │                  │  HTTP   │                  │     │
│  └──────────────────┘         └──────────────────┘     │
│                                         │                │
│                                         ▼                │
│                                ┌──────────────────┐     │
│                                │  ChromaDB        │     │
│                                │  (Vector Store)  │     │
│                                └──────────────────┘     │
│                                         │                │
│                                         ▼                │
│                                ┌──────────────────┐     │
│                                │  Redis           │     │
│                                │  (Cache)         │     │
│                                └──────────────────┘     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

**See Also**:
- `PDRI_INTEGRATION_BRIEF.md` - Complete integration guide
- `PDRI_QUICK_REFERENCE.md` - Quick reference
- `API.md` - Full API documentation
