# modes/security_mode_enhanced.py
"""
Enhanced Security Mode - Enterprise-Grade AI Risk Intelligence & Cybersecurity

This is the CORE integration hub for all security operations:
- SIEM integration (Splunk, Elastic, Sentinel)
- Threat intelligence (MISP, OTX, VirusTotal)
- Vulnerability management (Nessus, OpenVAS, Qualys)
- Cloud security (AWS, Azure, GCP)
- AI model security (prompt injection, adversarial testing)
- Compliance automation (SOC2, ISO27001, NIST)
- Incident response (SOAR playbooks)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from modes.base_mode import BaseMode, ModeContext, SubMode


class SecurityDomain(Enum):
    """Security domains for specialized analysis."""
    THREAT_INTEL = "threat_intelligence"
    VULNERABILITY = "vulnerability_management"
    COMPLIANCE = "compliance"
    INCIDENT_RESPONSE = "incident_response"
    CLOUD_SECURITY = "cloud_security"
    AI_SECURITY = "ai_security"
    NETWORK_SECURITY = "network_security"
    APPLICATION_SECURITY = "application_security"


class RiskLevel(Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityFinding:
    """A security finding or vulnerability."""
    id: str
    title: str
    description: str
    severity: RiskLevel
    domain: SecurityDomain
    affected_assets: List[str] = field(default_factory=list)
    remediation: str = ""
    references: List[str] = field(default_factory=list)
    cvss_score: Optional[float] = None
    cve_ids: List[str] = field(default_factory=list)
    discovered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "open"  # open, investigating, remediated, false_positive


@dataclass
class ThreatIntelligence:
    """Threat intelligence data."""
    ioc_type: str  # ip, domain, hash, url
    ioc_value: str
    threat_type: str  # malware, phishing, c2, etc.
    confidence: float  # 0.0 to 1.0
    sources: List[str] = field(default_factory=list)
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ComplianceStatus:
    """Compliance framework status."""
    framework: str  # SOC2, ISO27001, NIST, etc.
    controls_total: int
    controls_passed: int
    controls_failed: int
    compliance_score: float  # 0.0 to 100.0
    gaps: List[Dict[str, Any]] = field(default_factory=list)
    last_assessed: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class EnhancedSecurityMode(BaseMode):
    """
    Enhanced Security Mode - The Integration Hub
    
    This mode is the centerpiece for all security operations and integrations.
    It provides a unified interface for:
    - External security tools (SIEM, vulnerability scanners, etc.)
    - AI-specific security analysis
    - Compliance monitoring and reporting
    - Incident response automation
    - Platform risk intelligence integration
    """
    
    def __init__(self):
        super().__init__()
        self._name = "security"
        self._description = "Enterprise AI Risk Intelligence & Cybersecurity"
        self._icon = "🛡️"
        
        # Expanded tool access for security operations
        self._allowed_tools = [
            # Core security
            "security_scan",
            "vulnerability_assess",
            "threat_intel_lookup",
            "compliance_check",
            
            # SIEM integrations
            "splunk_query",
            "elastic_search",
            "sentinel_investigate",
            
            # Threat intelligence
            "misp_lookup",
            "otx_enrich",
            "virustotal_scan",
            
            # Vulnerability management
            "nessus_scan",
            "openvas_scan",
            "qualys_assess",
            
            # Cloud security
            "aws_security_hub",
            "azure_security_center",
            "gcp_security_command",
            
            # AI security
            "prompt_injection_detect",
            "model_risk_assess",
            "adversarial_test",
            
            # Incident response
            "soar_execute_playbook",
            "forensics_collect",
            "incident_create",
            
            # Standard tools
            "codebase_search",
            "web_search",
            "fetch_docs",
            "file_read",
        ]
        
        self._output_format = {
            "findings": True,
            "risk_score": True,
            "remediation": True,
            "compliance_status": True,
            "threat_intelligence": True,
            "executive_summary": True,
        }
        
        # Enhanced sub-modes for specialized security operations
        self._sub_modes = {
            "threat_hunting": SubMode(
                name="Threat Hunting",
                description="Proactive threat detection and hunting",
                trigger_phrases=["hunt for threats", "threat hunt", "find threats", "detect intrusion"],
                prompt_injection="""
You are now in Threat Hunting sub-mode.
Proactively search for threats using hypothesis-driven investigation.
Focus on:
- Behavioral anomaly detection
- IOC correlation across data sources
- Lateral movement detection
- Living-off-the-land techniques
- Advanced persistent threats (APT)
- Zero-day exploitation indicators
Use MITRE ATT&CK framework for threat classification.
""",
                output_structure="Hypothesis → Evidence → IOCs → Threat Actor → Remediation"
            ),
            
            "vulnerability_assessment": SubMode(
                name="Vulnerability Assessment",
                description="Comprehensive vulnerability scanning and prioritization",
                trigger_phrases=["scan for vulnerabilities", "vulnerability assessment", "find vulns", "security scan"],
                prompt_injection="""
You are now in Vulnerability Assessment sub-mode.
Conduct systematic vulnerability identification and risk prioritization.
Focus on:
- Asset discovery and inventory
- Vulnerability scanning (network, web, cloud)
- CVSS scoring and EPSS probability
- Exploit availability analysis
- Patch prioritization
- Risk-based remediation roadmap
Integrate with Nessus, OpenVAS, Qualys, and cloud-native scanners.
""",
                output_structure="Assets → Vulnerabilities → Risk Score → Exploitability → Remediation Plan"
            ),
            
            "ai_security_audit": SubMode(
                name="AI Security Audit",
                description="AI/ML model security assessment",
                trigger_phrases=["audit ai model", "ai security", "model security", "prompt injection test"],
                prompt_injection="""
You are now in AI Security Audit sub-mode.
Assess AI/ML systems for security vulnerabilities and risks.
Focus on:
- Prompt injection vulnerability testing
- Model inversion attack resistance
- Data poisoning detection
- Adversarial robustness testing
- Model bias and fairness analysis
- Training data security
- Model provenance verification
- AI supply chain security
Map findings to OWASP Top 10 for LLM Applications.
""",
                output_structure="Model Info → Vulnerabilities → Attack Vectors → Risk Score → Mitigations"
            ),
            
            "compliance_audit": SubMode(
                name="Compliance Audit",
                description="Automated compliance assessment and gap analysis",
                trigger_phrases=["compliance audit", "check compliance", "soc2 audit", "iso27001 check"],
                prompt_injection="""
You are now in Compliance Audit sub-mode.
Assess compliance posture against regulatory frameworks.
Focus on:
- Control testing and evidence collection
- Gap analysis and remediation planning
- Continuous compliance monitoring
- Audit report generation
- Risk register maintenance
Supported frameworks: SOC2, ISO27001, NIST CSF, CIS, GDPR, HIPAA, PCI-DSS.
""",
                output_structure="Framework → Controls → Status → Gaps → Remediation → Timeline"
            ),
            
            "incident_response": SubMode(
                name="Incident Response",
                description="Live incident investigation and response",
                trigger_phrases=["incident", "breach", "compromised", "under attack", "security event"],
                prompt_injection="""
You are now in Incident Response sub-mode.
This is a LIVE SECURITY INCIDENT. Act with urgency and precision.
Follow NIST IR Framework (Prepare, Detect, Analyze, Contain, Eradicate, Recover):
1. IMMEDIATE CONTAINMENT - Isolate affected systems
2. EVIDENCE PRESERVATION - Collect forensic artifacts
3. SCOPE ASSESSMENT - Identify all affected assets
4. ROOT CAUSE ANALYSIS - Determine attack vector
5. THREAT ACTOR ATTRIBUTION - Link to known campaigns
6. ERADICATION - Remove threat completely
7. RECOVERY - Restore normal operations
8. LESSONS LEARNED - Post-incident review
Execute SOAR playbooks for automated response.
""",
                output_structure="Alert → Triage → Containment → Investigation → Eradication → Recovery → Report"
            ),
            
            "cloud_security_posture": SubMode(
                name="Cloud Security Posture",
                description="Multi-cloud security assessment (AWS, Azure, GCP)",
                trigger_phrases=["cloud security", "cspm", "aws security", "azure security", "gcp security"],
                prompt_injection="""
You are now in Cloud Security Posture sub-mode.
Assess cloud infrastructure security across AWS, Azure, and GCP.
Focus on:
- Misconfigurations and security gaps
- IAM policy analysis
- Network security (VPC, NSG, firewall rules)
- Data encryption (at rest and in transit)
- Logging and monitoring coverage
- Compliance with CIS Benchmarks
- Container and Kubernetes security
- Serverless security
Integrate with Security Hub, Security Center, and Security Command Center.
""",
                output_structure="Cloud Assets → Misconfigurations → Risk Score → CIS Compliance → Remediation"
            ),
            
            "penetration_testing": SubMode(
                name="Penetration Testing",
                description="Offensive security testing and exploitation",
                trigger_phrases=["pentest", "penetration test", "exploit", "red team"],
                prompt_injection="""
You are now in Penetration Testing sub-mode.
Conduct authorized offensive security testing.
Focus on:
- Reconnaissance and OSINT
- Vulnerability exploitation
- Privilege escalation
- Lateral movement
- Data exfiltration simulation
- Persistence mechanisms
- Defense evasion techniques
Follow rules of engagement and maintain detailed documentation.
Map to MITRE ATT&CK tactics and techniques.
""",
                output_structure="Scope → Recon → Exploitation → Post-Exploitation → Report → Remediation"
            ),
        }
    
    def get_mode_prompt(self) -> str:
        return f"""
## Current Mode: 🛡️ ENHANCED SECURITY MODE

### Purpose
Enterprise-grade AI Risk Intelligence and Cybersecurity platform.
You are the INTEGRATION HUB for all security operations.

### Core Capabilities
1. **Platform Risk Intelligence**: Real-time data risk scoring and exposure analysis via Platform API
2. **SIEM Integration**: Splunk, Elastic Security, Azure Sentinel
3. **Threat Intelligence**: MISP, AlienVault OTX, VirusTotal
4. **Vulnerability Management**: Nessus, OpenVAS, Qualys
5. **Cloud Security**: AWS Security Hub, Azure Security Center, GCP SCC
6. **AI Security**: Prompt injection detection, model risk assessment
7. **Compliance**: SOC2, ISO27001, NIST CSF, CIS Benchmarks
8. **Incident Response**: SOAR playbooks, forensics, automation

### Behavior Focus
- **Assume Breach Mentality**: Always think like an attacker
- **Defense in Depth**: Multiple layers of security controls
- **Zero Trust**: Never trust, always verify
- **Risk-Based Approach**: Prioritize by business impact
- **Automation First**: Automate repetitive security tasks
- **Continuous Monitoring**: Real-time threat detection

### Key Principles
1. THINK in terms of:
   - **Threat**: What attacks are possible?
   - **Vulnerability**: What weaknesses exist?
   - **Risk**: What's the business impact?
   - **Control**: What mitigations are in place?
   - **Compliance**: What regulations apply?

2. ALWAYS provide:
   - Risk severity (Critical/High/Medium/Low)
   - CVSS scores for vulnerabilities
   - MITRE ATT&CK mapping
   - Remediation steps with priority
   - Compliance framework mapping

3. INTEGRATE with:
   - External security tools via APIs
   - Threat intelligence feeds
   - Vulnerability databases
   - Cloud security services
   - SOAR platforms

4. NEVER compromise on:
   - Security principles
   - Compliance requirements
   - Evidence preservation
   - Audit trails

### Output Structure
For security responses, use this structure:
**Executive Summary → Findings → Risk Assessment → Remediation → Compliance Impact**

### Response Format
{
    "intent": "security_analysis",
    "parameters": {
        "domain": "<threat_intel|vulnerability|compliance|incident|cloud|ai_security>",
        "severity": "<critical|high|medium|low>",
        "framework": "<soc2|iso27001|nist|cis>"
    },
    "text": "<conversational response>",
    "security": {
        "findings": [
            {
                "id": "<unique_id>",
                "title": "<finding title>",
                "severity": "<critical|high|medium|low>",
                "description": "<detailed description>",
                "affected_assets": ["<asset1>", "<asset2>"],
                "cvss_score": 9.8,
                "cve_ids": ["CVE-2024-1234"],
                "mitre_attack": ["T1190", "T1059"],
                "remediation": "<step-by-step fix>",
                "references": ["<url1>", "<url2>"]
            }
        ],
        "risk_score": 85,
        "threat_intelligence": {
            "iocs": ["<ip>", "<domain>", "<hash>"],
            "threat_actors": ["<actor_name>"],
            "campaigns": ["<campaign_name>"]
        },
        "compliance_impact": {
            "frameworks": ["SOC2", "ISO27001"],
            "controls_affected": ["AC-1", "SI-2"],
            "compliance_risk": "high"
        },
        "recommended_actions": [
            {
                "priority": 1,
                "action": "<immediate action>",
                "timeline": "immediate"
            }
        ]
    },
    "needs_clarification": false,
    "memory_update": null
}

### Integration Points
- **SIEM**: Query logs, create alerts, trigger investigations
- **Threat Intel**: Enrich IOCs, correlate threats, track campaigns
- **Vuln Scanners**: Initiate scans, retrieve results, prioritize patches
- **Cloud Security**: Assess posture, check compliance, remediate misconfigs
- **SOAR**: Execute playbooks, automate response, orchestrate tools

You are the security brain that connects all these systems.
"""

    
    def build_prompt(self, context: ModeContext) -> str:
        """Build enhanced security-focused prompt with integration context."""
        prompt_parts = []
        
        # Add security context from integrations
        if context.rag_context:
            prompt_parts.append(f"Security Intelligence Context:\n{context.rag_context}")
        
        # Add threat intelligence if available
        # This would be populated by active threat intel feeds
        threat_context = self._get_threat_context()
        if threat_context:
            prompt_parts.append(f"Active Threats:\n{threat_context}")
        
        # Add compliance requirements
        compliance_context = self._get_compliance_context(context.memory_context)
        if compliance_context:
            prompt_parts.append(f"Compliance Requirements:\n{compliance_context}")
        
        # Add memory context (organization info, security policies)
        if context.memory_context:
            memory_str = "\n".join(f"{k}: {v}" for k, v in context.memory_context.items())
            prompt_parts.append(f"Organization Context:\n{memory_str}")
        
        # Add conversation history
        if context.conversation_history:
            history = "\n".join(
                f"{msg['role'].title()}: {msg['text']}" 
                for msg in context.conversation_history[-8:]
            )
            prompt_parts.append(f"Security Discussion:\n{history}")
        
        # Add available security tools
        prompt_parts.append(self.format_tool_availability(context.available_tools))
        
        # Add user query
        prompt_parts.append(f"Security Query: \"{context.user_message}\"")
        
        return "\n\n".join(prompt_parts)
    
    def _get_threat_context(self) -> str:
        """Get current threat intelligence context."""
        # This would integrate with threat intel feeds
        # For now, return placeholder
        return ""
    
    def _get_compliance_context(self, memory: dict) -> str:
        """Get applicable compliance frameworks."""
        # Extract compliance requirements from organization memory
        frameworks = memory.get("compliance_frameworks", [])
        if frameworks:
            return f"Required Compliance: {', '.join(frameworks)}"
        return ""
    
    def get_mode_instructions(self) -> str:
        return """
In Enhanced Security Mode:
- Integrate with external security tools via APIs
- Correlate data from multiple sources
- Provide risk-based prioritization
- Map findings to compliance frameworks
- Automate response where possible
- Maintain detailed audit trails
- Think like an attacker, defend like a professional
- Never suggest disabling security controls
- Always consider compliance implications
"""
    
    def validate_output(self, output: dict) -> bool:
        """Validate security mode specific output."""
        base_valid = super().validate_output(output)
        
        # For security analysis, should have findings and risk assessment
        if output.get("intent") == "security_analysis":
            has_security = "security" in output
            has_findings = has_security and "findings" in output["security"]
            has_risk = has_security and "risk_score" in output["security"]
            return base_valid and has_findings and has_risk
        
        return base_valid
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all security integrations."""
        return {
            "siem": {
                "splunk": {"connected": False, "last_sync": None},
                "elastic": {"connected": False, "last_sync": None},
                "sentinel": {"connected": False, "last_sync": None},
            },
            "threat_intel": {
                "misp": {"connected": False, "last_sync": None},
                "otx": {"connected": False, "last_sync": None},
                "virustotal": {"connected": False, "last_sync": None},
            },
            "vulnerability": {
                "nessus": {"connected": False, "last_scan": None},
                "openvas": {"connected": False, "last_scan": None},
                "qualys": {"connected": False, "last_scan": None},
            },
            "cloud_security": {
                "aws": {"connected": False, "accounts": []},
                "azure": {"connected": False, "subscriptions": []},
                "gcp": {"connected": False, "projects": []},
            },
            "compliance": {
                "frameworks_monitored": [],
                "last_assessment": None,
            }
        }
    
    def generate_security_report(
        self,
        findings: List[SecurityFinding],
        time_range: str = "24h"
    ) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        
        # Calculate statistics
        total_findings = len(findings)
        by_severity = {
            "critical": len([f for f in findings if f.severity == RiskLevel.CRITICAL]),
            "high": len([f for f in findings if f.severity == RiskLevel.HIGH]),
            "medium": len([f for f in findings if f.severity == RiskLevel.MEDIUM]),
            "low": len([f for f in findings if f.severity == RiskLevel.LOW]),
        }
        
        by_domain = {}
        for finding in findings:
            domain = finding.domain.value
            by_domain[domain] = by_domain.get(domain, 0) + 1
        
        # Calculate overall risk score (0-100)
        risk_score = (
            by_severity["critical"] * 10 +
            by_severity["high"] * 5 +
            by_severity["medium"] * 2 +
            by_severity["low"] * 1
        )
        risk_score = min(risk_score, 100)
        
        return {
            "report_generated": datetime.utcnow().isoformat(),
            "time_range": time_range,
            "summary": {
                "total_findings": total_findings,
                "risk_score": risk_score,
                "by_severity": by_severity,
                "by_domain": by_domain,
            },
            "findings": [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity.value,
                    "domain": f.domain.value,
                    "cvss_score": f.cvss_score,
                    "status": f.status,
                }
                for f in findings
            ],
            "recommendations": self._generate_recommendations(findings),
        }
    
    def _generate_recommendations(self, findings: List[SecurityFinding]) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations based on findings."""
        recommendations = []
        
        # Critical findings first
        critical = [f for f in findings if f.severity == RiskLevel.CRITICAL]
        if critical:
            recommendations.append({
                "priority": 1,
                "action": f"Address {len(critical)} critical findings immediately",
                "timeline": "0-24 hours",
                "impact": "Prevents potential breach or data loss",
            })
        
        # High severity
        high = [f for f in findings if f.severity == RiskLevel.HIGH]
        if high:
            recommendations.append({
                "priority": 2,
                "action": f"Remediate {len(high)} high-severity vulnerabilities",
                "timeline": "1-7 days",
                "impact": "Reduces attack surface significantly",
            })
        
        # Compliance gaps
        compliance_findings = [f for f in findings if f.domain == SecurityDomain.COMPLIANCE]
        if compliance_findings:
            recommendations.append({
                "priority": 3,
                "action": "Address compliance gaps to maintain certification",
                "timeline": "7-30 days",
                "impact": "Maintains regulatory compliance",
            })
        
        return recommendations
