# tools/security/ai_security_audit.py
"""
AI Security Audit Tool

Comprehensive security assessment for AI/ML systems:
- Model security analysis
- Training data security
- Inference security
- AI supply chain security
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AISecurityFinding:
    """An AI security finding."""
    finding_id: str
    category: str  # model, data, inference, supply_chain
    severity: str  # critical, high, medium, low
    title: str
    description: str
    impact: str
    remediation: str
    owasp_llm_mapping: Optional[str] = None


class AISecurityAudit:
    """
    AI/ML security auditing tool.
    
    Assesses AI systems for security vulnerabilities specific to
    machine learning and large language models.
    """
    
    # OWASP Top 10 for LLM Applications
    OWASP_LLM_TOP10 = {
        "LLM01": "Prompt Injection",
        "LLM02": "Insecure Output Handling",
        "LLM03": "Training Data Poisoning",
        "LLM04": "Model Denial of Service",
        "LLM05": "Supply Chain Vulnerabilities",
        "LLM06": "Sensitive Information Disclosure",
        "LLM07": "Insecure Plugin Design",
        "LLM08": "Excessive Agency",
        "LLM09": "Overreliance",
        "LLM10": "Model Theft",
    }
    
    def __init__(self):
        """Initialize AI security audit tool."""
        pass
    
    def audit_model(
        self,
        model_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Audit an AI model for security issues.
        
        Args:
            model_info: Model metadata (name, version, source, etc.)
            
        Returns:
            Security audit results
        """
        findings = []
        
        # Check model provenance
        findings.extend(self._check_model_provenance(model_info))
        
        # Check for known vulnerabilities
        findings.extend(self._check_model_vulnerabilities(model_info))
        
        # Check training data security
        findings.extend(self._check_training_data(model_info))
        
        # Check inference security
        findings.extend(self._check_inference_security(model_info))
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(findings)
        
        return {
            "model": model_info.get("name", "unknown"),
            "audited_at": datetime.utcnow().isoformat(),
            "risk_score": risk_score,
            "findings": findings,
            "owasp_llm_coverage": self._map_to_owasp(findings),
            "recommendations": self._generate_recommendations(findings),
        }
    
    def _check_model_provenance(
        self,
        model_info: Dict[str, Any],
    ) -> List[AISecurityFinding]:
        """Check model provenance and supply chain."""
        findings = []
        
        # Check if model source is known
        if not model_info.get("source"):
            findings.append(AISecurityFinding(
                finding_id="PROV-001",
                category="supply_chain",
                severity="high",
                title="Unknown Model Source",
                description="Model source/provenance is not documented",
                impact="Cannot verify model integrity or detect tampering",
                remediation="Document model source, training process, and chain of custody",
                owasp_llm_mapping="LLM05",
            ))
        
        # Check for model signing/verification
        if not model_info.get("signature"):
            findings.append(AISecurityFinding(
                finding_id="PROV-002",
                category="supply_chain",
                severity="medium",
                title="Model Not Cryptographically Signed",
                description="Model lacks cryptographic signature for integrity verification",
                impact="Cannot detect model tampering or substitution",
                remediation="Implement model signing and verification process",
                owasp_llm_mapping="LLM05",
            ))
        
        return findings
    
    def _check_model_vulnerabilities(
        self,
        model_info: Dict[str, Any],
    ) -> List[AISecurityFinding]:
        """Check for known model vulnerabilities."""
        findings = []
        
        # Check for prompt injection vulnerabilities
        findings.append(AISecurityFinding(
            finding_id="VULN-001",
            category="model",
            severity="high",
            title="Prompt Injection Risk",
            description="Model may be vulnerable to prompt injection attacks",
            impact="Attackers could manipulate model behavior or extract sensitive data",
            remediation="Implement prompt injection detection and input validation",
            owasp_llm_mapping="LLM01",
        ))
        
        return findings
    
    def _check_training_data(
        self,
        model_info: Dict[str, Any],
    ) -> List[AISecurityFinding]:
        """Check training data security."""
        findings = []
        
        # Check for data poisoning risks
        if not model_info.get("data_validation"):
            findings.append(AISecurityFinding(
                finding_id="DATA-001",
                category="data",
                severity="high",
                title="No Training Data Validation",
                description="Training data lacks validation and sanitization",
                impact="Model could be poisoned with malicious training data",
                remediation="Implement training data validation and anomaly detection",
                owasp_llm_mapping="LLM03",
            ))
        
        return findings
    
    def _check_inference_security(
        self,
        model_info: Dict[str, Any],
    ) -> List[AISecurityFinding]:
        """Check inference-time security."""
        findings = []
        
        # Check for output validation
        if not model_info.get("output_validation"):
            findings.append(AISecurityFinding(
                finding_id="INF-001",
                category="inference",
                severity="medium",
                title="No Output Validation",
                description="Model outputs are not validated or sanitized",
                impact="Could lead to injection attacks or sensitive data leakage",
                remediation="Implement output validation and sanitization",
                owasp_llm_mapping="LLM02",
            ))
        
        return findings
    
    def _calculate_risk_score(self, findings: List[AISecurityFinding]) -> int:
        """Calculate overall risk score (0-100)."""
        severity_weights = {
            "critical": 25,
            "high": 15,
            "medium": 8,
            "low": 3,
        }
        
        score = sum(severity_weights.get(f.severity, 0) for f in findings)
        return min(score, 100)
    
    def _map_to_owasp(self, findings: List[AISecurityFinding]) -> Dict[str, int]:
        """Map findings to OWASP LLM Top 10."""
        mapping = {}
        for finding in findings:
            if finding.owasp_llm_mapping:
                mapping[finding.owasp_llm_mapping] = mapping.get(finding.owasp_llm_mapping, 0) + 1
        return mapping
    
    def _generate_recommendations(
        self,
        findings: List[AISecurityFinding],
    ) -> List[str]:
        """Generate prioritized recommendations."""
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 4))
        
        return [f.remediation for f in sorted_findings[:5]]  # Top 5
    
    def get_owasp_llm_top10(self) -> Dict[str, str]:
        """Get OWASP LLM Top 10 list."""
        return self.OWASP_LLM_TOP10.copy()


# Global instance
ai_security_audit = AISecurityAudit()
