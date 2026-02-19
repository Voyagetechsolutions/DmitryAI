# PDRI Integration Brief for Dmitry AI

**For**: Senior Engineers  
**Date**: 2026-02-17  
**Status**: Production Ready  
**Integration Type**: PDRI DmitryClient → Dmitry AI Backend

---

## Executive Summary

This document provides precise, actionable instructions for integrating PDRI's DmitryClient with the Dmitry AI backend. All file paths, function signatures, and integration points are mapped based on actual Dmitry codebase analysis.

---

## 1. Dmitry Architecture Overview

### Core Components

```
Dmitry AI
├── Agent Server (HTTP API)          → MarkX/agent/server.py
├── Orchestrator (Brain Router)      → MarkX/dmitry_operator/orchestrator.py
├── LLM Integration                  → MarkX/llm.py
├── Tool Registry                    → MarkX/tools/registry.py
├── Operator Tools (Actions)         → MarkX/dmitry_operator/tools.py
└── Mode Manager (7 Modes)           → MarkX/modes/mode_manager.py
```

### Request Flow

```
PDRI Client → HTTP POST /message → AgentServer → Orchestrator → LLM + Tools → Response
```

---

## 2. Integration Points

### A. HTTP API Endpoints (Primary Integration)

**Base URL**: `http://127.0.0.1:8765`

#### Endpoint 1: Send Message
```http
POST /message
Content-Type: application/json

{
  "message": "User query or command"
}
```

**Response**:
```json
{
  "text": "Dmitry's response",
  "intent": "chat|action|security_alert",
  "mode": "general|security|developer|...",
  "tool_executed": "tool_name",  // if action performed
  "tool_result": "result message",
  "log": {
    "tool": "tool_name",
    "status": "success|failed",
    "message": "details",
    "time": "HH:MM:SS"
  }
}
```

#### Endpoint 2: Switch Mode
```http
POST /mode
Content-Type: application/json

{
  "mode": "security"  // utility|general|design|developer|research|security|simulation
}
```

#### Endpoint 3: Get Status
```http
GET /status
```

**Response**:
```json
{
  "connected": true,
  "mode": "security",
  "pending_confirmations": 0,
  "timestamp": "2026-02-17T10:30:00Z"
}
```

#### Endpoint 4: Get Logs
```http
GET /logs?limit=50
```

**Response**:
```json
{
  "logs": [
    {
      "tool": "threat_intel_lookup",
      "status": "success",
      "message": "IOC analyzed",
      "time": "10:30:15",
      "timestamp": "2026-02-17T10:30:15Z"
    }
  ],
  "total": 150
}
```

---

## 3. PDRI DmitryClient Integration

### File to Create/Modify

**Location**: `PDRI/integrations/dmitry_client.py` (or your equivalent)

### Implementation


```python
# PDRI/integrations/dmitry_client.py
"""
PDRI → Dmitry AI Integration Client

Connects PDRI's strategic advisor capabilities with Dmitry's
AI backend for natural language processing and action execution.
"""

import requests
from typing import Dict, Any, Optional, List
import json


class DmitryClient:
    """
    Client for communicating with Dmitry AI backend.
    
    Provides 15+ methods for natural language interaction,
    strategic advisory, and security operations.
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8765"):
        """
        Initialize Dmitry client.
        
        Args:
            base_url: Dmitry agent server URL
        """
        self.base_url = base_url.rstrip('/')
        self.current_mode = "general"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "PDRI-DmitryClient/1.0"
        })
    
    # ========== CORE METHODS ==========
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a message to Dmitry and get response.
        
        Args:
            message: Natural language query or command
            
        Returns:
            {
                "text": "Response text",
                "intent": "chat|action|security_alert",
                "mode": "current_mode",
                "tool_executed": "tool_name",  // optional
                "tool_result": "result",        // optional
                "log": {...}                    // optional
            }
        """
        try:
            response = self.session.post(
                f"{self.base_url}/message",
                json={"message": message},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "text": f"Connection error: {str(e)}",
                "intent": "error",
                "error": str(e)
            }
    
    def switch_mode(self, mode: str) -> Dict[str, Any]:
        """
        Switch Dmitry's cognitive mode.
        
        Args:
            mode: One of: utility, general, design, developer, 
                  research, security, simulation
                  
        Returns:
            {
                "success": true,
                "message": "Switched to security mode",
                "mode": "security"
            }
        """
        try:
            response = self.session.post(
                f"{self.base_url}/mode",
                json={"mode": mode},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                self.current_mode = mode
            return result
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get Dmitry's current status.
        
        Returns:
            {
                "connected": true,
                "mode": "security",
                "pending_confirmations": 0,
                "timestamp": "2026-02-17T10:30:00Z"
            }
        """
        try:
            response = self.session.get(
                f"{self.base_url}/status",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    def get_logs(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get recent action logs.
        
        Args:
            limit: Maximum number of logs to retrieve
            
        Returns:
            {
                "logs": [...],
                "total": 150
            }
        """
        try:
            response = self.session.get(
                f"{self.base_url}/logs?limit={limit}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "logs": [],
                "total": 0,
                "error": str(e)
            }
    
    # ========== STRATEGIC ADVISOR METHODS ==========
    
    def analyze_threat(self, threat_description: str) -> Dict[str, Any]:
        """
        Analyze a security threat using Dmitry's security mode.
        
        Args:
            threat_description: Description of the threat
            
        Returns:
            Dmitry's analysis and recommendations
        """
        # Switch to security mode
        self.switch_mode("security")
        
        # Send analysis request
        prompt = f"""Analyze this security threat and provide:
1. Threat classification
2. Risk level
3. Recommended actions
4. Mitigation strategies

Threat: {threat_description}"""
        
        return self.send_message(prompt)
    
    def get_strategic_advice(self, context: str, question: str) -> Dict[str, Any]:
        """
        Get strategic advice from Dmitry.
        
        Args:
            context: Business/technical context
            question: Specific question
            
        Returns:
            Strategic recommendations
        """
        prompt = f"""Context: {context}

Question: {question}

Provide strategic advice with:
1. Analysis
2. Options
3. Recommendations
4. Risks and considerations"""
        
        return self.send_message(prompt)
    
    def format_for_natural_language(self, data: Dict[str, Any]) -> str:
        """
        Format structured data for natural language presentation.
        
        Args:
            data: Structured data to format
            
        Returns:
            Natural language formatted string
        """
        prompt = f"""Format this data in clear, natural language:

{json.dumps(data, indent=2)}

Make it readable and professional."""
        
        result = self.send_message(prompt)
        return result.get("text", "")
    
    def explain_technical_concept(self, concept: str, audience: str = "executive") -> Dict[str, Any]:
        """
        Explain a technical concept for specific audience.
        
        Args:
            concept: Technical concept to explain
            audience: Target audience (executive, technical, general)
            
        Returns:
            Explanation tailored to audience
        """
        prompt = f"""Explain this technical concept for a {audience} audience:

{concept}

Use appropriate language and examples."""
        
        return self.send_message(prompt)
    
    def generate_report_summary(self, report_data: Dict[str, Any]) -> str:
        """
        Generate executive summary from report data.
        
        Args:
            report_data: Raw report data
            
        Returns:
            Executive summary text
        """
        prompt = f"""Generate an executive summary from this data:

{json.dumps(report_data, indent=2)}

Focus on:
- Key findings
- Critical issues
- Recommendations
- Next steps"""
        
        result = self.send_message(prompt)
        return result.get("text", "")
    
    # ========== SECURITY OPERATIONS ==========
    
    def lookup_threat_intelligence(self, ioc: str, ioc_type: str = "auto") -> Dict[str, Any]:
        """
        Lookup threat intelligence for an IOC.
        
        Args:
            ioc: Indicator of Compromise (IP, domain, hash, etc.)
            ioc_type: Type of IOC (auto-detect if not specified)
            
        Returns:
            Threat intelligence data
        """
        self.switch_mode("security")
        
        prompt = f"""Lookup threat intelligence for this IOC:

IOC: {ioc}
Type: {ioc_type}

Provide:
- Reputation
- Known associations
- Threat level
- Recommendations"""
        
        return self.send_message(prompt)
    
    def check_compliance(self, framework: str, system_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compliance against a framework.
        
        Args:
            framework: Compliance framework (soc2, iso27001, nist, etc.)
            system_config: System configuration to check
            
        Returns:
            Compliance assessment
        """
        self.switch_mode("security")
        
        prompt = f"""Check compliance against {framework}:

System Configuration:
{json.dumps(system_config, indent=2)}

Provide:
- Compliance status
- Gaps identified
- Recommendations
- Priority actions"""
        
        return self.send_message(prompt)
    
    def analyze_vulnerability(self, vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze vulnerability and provide remediation advice.
        
        Args:
            vulnerability_data: Vulnerability details
            
        Returns:
            Analysis and remediation recommendations
        """
        self.switch_mode("security")
        
        prompt = f"""Analyze this vulnerability:

{json.dumps(vulnerability_data, indent=2)}

Provide:
- Severity assessment
- Exploitability
- Impact analysis
- Remediation steps
- Priority level"""
        
        return self.send_message(prompt)
    
    def assess_ai_model_risk(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess AI model security risks.
        
        Args:
            model_config: AI model configuration
            
        Returns:
            Risk assessment
        """
        self.switch_mode("security")
        
        prompt = f"""Assess AI model security risks:

Model Configuration:
{json.dumps(model_config, indent=2)}

Evaluate:
- Prompt injection vulnerabilities
- Data poisoning risks
- Model bias
- Security controls
- OWASP LLM Top 10 compliance"""
        
        return self.send_message(prompt)
    
    # ========== UTILITY METHODS ==========
    
    def is_connected(self) -> bool:
        """Check if Dmitry is connected and responsive."""
        status = self.get_status()
        return status.get("connected", False)
    
    def get_current_mode(self) -> str:
        """Get current cognitive mode."""
        status = self.get_status()
        return status.get("mode", self.current_mode)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Dmitry connection.
        
        Returns:
            {
                "healthy": true,
                "mode": "security",
                "latency_ms": 45,
                "version": "1.2"
            }
        """
        import time
        start = time.time()
        
        status = self.get_status()
        latency = int((time.time() - start) * 1000)
        
        return {
            "healthy": status.get("connected", False),
            "mode": status.get("mode", "unknown"),
            "latency_ms": latency,
            "version": "1.2"
        }


# ========== USAGE EXAMPLES ==========

def example_usage():
    """Example usage of DmitryClient."""
    
    # Initialize client
    dmitry = DmitryClient()
    
    # Check connection
    if not dmitry.is_connected():
        print("❌ Dmitry not connected")
        return
    
    print("✅ Connected to Dmitry")
    
    # Example 1: Strategic advice
    advice = dmitry.get_strategic_advice(
        context="Cloud migration project",
        question="Should we migrate to multi-cloud or single cloud?"
    )
    print(f"\nStrategic Advice:\n{advice['text']}")
    
    # Example 2: Threat analysis
    threat = dmitry.analyze_threat(
        "Suspicious login attempts from multiple IPs in Russia"
    )
    print(f"\nThreat Analysis:\n{threat['text']}")
    
    # Example 3: Compliance check
    compliance = dmitry.check_compliance(
        framework="soc2",
        system_config={
            "encryption": True,
            "mfa": True,
            "logging": True,
            "backup": False
        }
    )
    print(f"\nCompliance Check:\n{compliance['text']}")
    
    # Example 4: Format data for presentation
    data = {
        "vulnerabilities": 15,
        "critical": 3,
        "high": 7,
        "medium": 5
    }
    formatted = dmitry.format_for_natural_language(data)
    print(f"\nFormatted Data:\n{formatted}")
    
    # Example 5: Get recent logs
    logs = dmitry.get_logs(limit=10)
    print(f"\nRecent Actions: {len(logs['logs'])} logs")


if __name__ == "__main__":
    example_usage()
```

---

## 4. Integration Steps

### Step 1: Start Dmitry Agent Server

```bash
cd MarkX
python run_dmitry.py --mode server
```

**Expected Output**:
```
==================================================
  DMITRY v1.2 - Agent Mode
==================================================

✓ Mode: general
✓ Orchestrator: Ready (Hands & Eyes active)

Agent ready. Connect with Electron UI or API client.
Press Ctrl+C to stop.

✓ Agent API server started on http://127.0.0.1:8765
```

### Step 2: Test Connection

```python
import requests

response = requests.get("http://127.0.0.1:8765/status")
print(response.json())
# Expected: {"connected": true, "mode": "general", ...}
```

### Step 3: Integrate DmitryClient into PDRI

```python
# In your PDRI application
from integrations.dmitry_client import DmitryClient

# Initialize
dmitry = DmitryClient()

# Use in your workflows
result = dmitry.send_message("Analyze this threat: ...")
```

---

## 5. Data Contracts

### Request Format (PDRI → Dmitry)

```python
{
    "message": str,  # Required: Natural language query/command
}
```

### Response Format (Dmitry → PDRI)

```python
{
    "text": str,              # Main response text
    "intent": str,            # "chat", "action", "security_alert"
    "mode": str,              # Current cognitive mode
    "tool_executed": str,     # Optional: Tool that was executed
    "tool_result": str,       # Optional: Tool execution result
    "log": {                  # Optional: Action log entry
        "tool": str,
        "status": str,        # "success", "failed"
        "message": str,
        "time": str,
        "timestamp": str
    },
    "security_alert": bool,   # Optional: True if security issue detected
    "detection": {            # Optional: Security detection details
        "risk_score": int,
        "injection_type": str,
        "matched_patterns": list,
        "recommended_action": str
    }
}
```

---

## 6. Security Mode Integration

### Switching to Security Mode

```python
dmitry.switch_mode("security")
```

### Security Sub-Modes Available

1. **Threat Hunting** - Proactive threat detection
2. **Vulnerability Assessment** - Vulnerability scanning
3. **AI Security Audit** - AI model security
4. **Compliance Audit** - Compliance checking
5. **Incident Response** - Incident handling
6. **Cloud Security Posture** - Cloud security
7. **Penetration Testing** - Security testing

### Security Tools Available

- `threat_intel_lookup` - IOC enrichment
- `vulnerability_scanner` - Vulnerability scanning
- `compliance_checker` - Compliance validation
- `ai_security_audit` - AI security assessment

---

## 7. Error Handling

### Connection Errors

```python
try:
    result = dmitry.send_message("query")
except requests.exceptions.ConnectionError:
    # Dmitry server not running
    print("Dmitry server not available")
except requests.exceptions.Timeout:
    # Request took too long
    print("Request timeout")
```

### Response Validation

```python
result = dmitry.send_message("query")

if result.get("intent") == "error":
    print(f"Error: {result.get('error')}")
elif result.get("security_alert"):
    print(f"Security Alert: {result.get('text')}")
else:
    print(f"Response: {result.get('text')}")
```

---

## 8. Performance Considerations

### Timeouts

- `/message`: 30 seconds (LLM processing)
- `/mode`: 10 seconds
- `/status`: 5 seconds
- `/logs`: 10 seconds

### Rate Limiting

- Default: 100 requests/minute
- Configurable via `API_RATE_LIMIT` env variable

### Caching

- Dmitry caches LLM responses internally
- Repeated queries return faster

---

## 9. Testing

### Unit Test Example

```python
import unittest
from integrations.dmitry_client import DmitryClient

class TestDmitryIntegration(unittest.TestCase):
    
    def setUp(self):
        self.dmitry = DmitryClient()
    
    def test_connection(self):
        """Test Dmitry connection."""
        self.assertTrue(self.dmitry.is_connected())
    
    def test_send_message(self):
        """Test sending message."""
        result = self.dmitry.send_message("Hello")
        self.assertIn("text", result)
        self.assertIn("intent", result)
    
    def test_mode_switch(self):
        """Test mode switching."""
        result = self.dmitry.switch_mode("security")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("mode"), "security")
    
    def test_threat_analysis(self):
        """Test threat analysis."""
        result = self.dmitry.analyze_threat("Suspicious activity")
        self.assertIn("text", result)
    
    def test_compliance_check(self):
        """Test compliance checking."""
        result = self.dmitry.check_compliance("soc2", {
            "encryption": True,
            "mfa": True
        })
        self.assertIn("text", result)
```

---

## 10. Deployment Checklist

### Prerequisites
- [ ] Dmitry server running on port 8765
- [ ] Network connectivity between PDRI and Dmitry
- [ ] Python requests library installed

### Configuration
- [ ] Set Dmitry base URL in PDRI config
- [ ] Configure timeout values
- [ ] Set up error logging
- [ ] Configure retry logic

### Testing
- [ ] Test connection health check
- [ ] Test message sending
- [ ] Test mode switching
- [ ] Test security operations
- [ ] Test error handling

### Monitoring
- [ ] Monitor connection status
- [ ] Track response times
- [ ] Log errors and failures
- [ ] Monitor rate limits

---

## 11. Support & Troubleshooting

### Common Issues

**Issue**: Connection refused
**Solution**: Ensure Dmitry server is running: `python run_dmitry.py --mode server`

**Issue**: Timeout errors
**Solution**: Increase timeout values or check network latency

**Issue**: Mode switch fails
**Solution**: Verify mode name is valid (utility, general, design, developer, research, security, simulation)

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

dmitry = DmitryClient()
# Will log all HTTP requests/responses
```

### Health Check

```python
health = dmitry.health_check()
print(f"Healthy: {health['healthy']}")
print(f"Latency: {health['latency_ms']}ms")
print(f"Mode: {health['mode']}")
```

---

## 12. Next Steps

1. **Implement DmitryClient** in PDRI codebase
2. **Test integration** with sample queries
3. **Configure error handling** and retries
4. **Set up monitoring** for connection health
5. **Deploy to production** environment

---

**Contact**: See main README.md for support resources
**Documentation**: See docs/API.md for complete API reference
**Version**: Dmitry 1.2 / PDRI Integration v1.0
