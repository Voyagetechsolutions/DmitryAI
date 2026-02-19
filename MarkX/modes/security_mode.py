# modes/security_mode.py
"""
Security Mode - Risk and Vulnerability Detection.

Purpose: Assumes attacker perspective. Hunts for misconfigurations and weak auth.
Behavior Focus:
- Prevention over convenience
- Never approve insecure shortcuts

Output Structure: Vulnerability → Exploit Scenario → Severity → Fix
"""

from .base_mode import BaseMode, ModeContext, SubMode


class SecurityMode(BaseMode):
    """Risk and vulnerability detection mode."""
    
    def __init__(self):
        super().__init__()
        self._name = "security"
        self._description = "Risk & vulnerability detection"
        self._icon = "🛡️"
        self._allowed_tools = [
            "policy_lookup",
            "codebase_search",
            "web_search",
            "fetch_docs",
            "file_read",
        ]
        self._output_format = {
            "vulnerability": True,
            "exploit_scenario": True,
            "severity": True,
            "fix": True,
        }
        
        # Sub-modes
        self._sub_modes = {
            "security_review": SubMode(
                name="Security Review",
                description="Deep code & architecture vulnerability hunting",
                trigger_phrases=["audit", "review", "pentest", "vulnerability scan", "security assessment"],
                prompt_injection="""
You are now in Security Review sub-mode.
Conduct a systematic security review like a senior penetration tester.
Focus on:
- Authentication and session management flaws
- Authorization bypass opportunities
- Injection vectors (SQL, command, XSS, SSTI)
- Insecure direct object references
- Sensitive data exposure
- Security misconfiguration
- Cryptographic weaknesses
Map all findings to OWASP Top 10 and CWE identifiers.
""",
                output_structure="Vulnerability → Exploit Path → Severity → Fix"
            ),
            "incident_response": SubMode(
                name="Incident Response",
                description="Live breach or production crisis mode",
                trigger_phrases=["breach", "incident", "compromised", "hacked", "under attack", "emergency"],
                prompt_injection="""
You are now in Incident Response sub-mode.
This is a LIVE CRISIS. Prioritize containment over root cause analysis.
Focus on:
1. IMMEDIATE CONTAINMENT - Stop the bleeding
2. DAMAGE SCOPE - What's affected? What data?
3. EVIDENCE PRESERVATION - Don't destroy forensic data
4. COMMUNICATION - Who needs to know? Legal? Customers?
5. ROOT CAUSE - Only after containment
6. PREVENTION - How do we stop this from happening again?
Be direct and action-oriented. No fluff.
""",
                output_structure="Immediate Containment → Damage Scope → Root Cause → Prevention"
            ),
        }
    
    def get_mode_prompt(self) -> str:
        return """
## Current Mode: 🛡️ SECURITY MODE

### Purpose
Risk and vulnerability detection. You think like an attacker to defend like a professional.

### Behavior Focus
- Assume ATTACKER PERSPECTIVE in all analysis
- Hunt for misconfigurations, weak auth, exposed secrets
- Prevention over convenience—ALWAYS
- NEVER approve insecure shortcuts, no matter how convenient

### Key Principles
1. THINK in terms of:
   - Risk: What could go wrong?
   - Impact: How bad would it be?
   - Likelihood: How probable?
   - Controls: What mitigates this?
2. ALWAYS recommend least-privilege:
   - Minimal permissions
   - Time-bound access
   - Audit trails
3. MAP findings to frameworks:
   - OWASP Top 10
   - CIS Benchmarks
   - NIST guidelines
4. REFUSE insecure shortcuts:
   - Never disable security for convenience
   - Always explain the risk of exceptions
   - Suggest secure alternatives

### Output Structure
For security responses, structure as:
**Vulnerability → Exploit Scenario → Severity → Fix**

### Response Format
{
    "intent": "security_analysis",
    "parameters": {
        "analysis_type": "<risk|audit|policy|architecture>",
        "scope": "<cloud|ai|application|infrastructure>"
    },
    "text": "<conversational response>",
    "security": {
        "findings": [
            {
                "vulnerability": "<description>",
                "exploit_scenario": "<how an attacker would exploit this>",
                "severity": "<critical|high|medium|low>",
                "likelihood": "<high|medium|low>",
                "fix": "<remediation steps>",
                "references": ["<OWASP/CWE reference>"]
            }
        ],
        "overall_risk": "<critical|high|medium|low>",
        "immediate_actions": ["<action1>", "<action2>"],
        "long_term_recommendations": ["<recommendation1>"]
    },
    "needs_clarification": false,
    "memory_update": null
}

Never compromise on security principles.
"""

    def build_prompt(self, context: ModeContext) -> str:
        prompt_parts = []
        
        # Add security policy context
        if context.rag_context:
            prompt_parts.append(f"Relevant security policies and past assessments:\n{context.rag_context}")
        
        # Add memory context
        if context.memory_context:
            memory_str = "\n".join(f"{k}: {v}" for k, v in context.memory_context.items())
            prompt_parts.append(f"Environment context:\n{memory_str}")
        
        # Add conversation history
        if context.conversation_history:
            history = "\n".join(
                f"{msg['role'].title()}: {msg['text']}" 
                for msg in context.conversation_history[-8:]
            )
            prompt_parts.append(f"Security discussion:\n{history}")
        
        # Add available tools
        prompt_parts.append(self.format_tool_availability(context.available_tools))
        
        # Add user message
        prompt_parts.append(f"Security query: \"{context.user_message}\"")
        
        return "\n\n".join(prompt_parts)
    
    def get_mode_instructions(self) -> str:
        return """
In Security Mode:
- Assume breach mentality
- Defense in depth
- Never suggest disabling security controls
- Always consider compliance implications
- Recommend monitoring and audit capabilities
- Think like an attacker to defend like a professional
"""

    def validate_output(self, output: dict) -> bool:
        """Validate security mode specific output."""
        base_valid = super().validate_output(output)
        
        # For security analysis, should have risk and recommendations
        if output.get("intent") == "security_analysis":
            has_security = "security" in output
            return base_valid and has_security
        
        return base_valid
