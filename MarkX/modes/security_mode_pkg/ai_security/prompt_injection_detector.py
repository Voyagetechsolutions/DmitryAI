# modes/security_mode/ai_security/prompt_injection_detector.py
"""
Prompt Injection Detection System

Detects and prevents prompt injection attacks against AI models.
Uses pattern matching, ML classification, and behavioral analysis.
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class InjectionType(Enum):
    """Types of prompt injection attacks."""
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    JAILBREAK = "jailbreak"
    ROLE_PLAY = "role_play"
    CONTEXT_OVERFLOW = "context_overflow"
    DELIMITER_MANIPULATION = "delimiter_manipulation"
    ENCODING_ATTACK = "encoding_attack"


@dataclass
class InjectionDetection:
    """Result of injection detection."""
    is_malicious: bool
    confidence: float  # 0.0 to 1.0
    injection_type: InjectionType
    matched_patterns: List[str]
    risk_score: int  # 0-100
    explanation: str
    recommended_action: str


class PromptInjectionDetector:
    """
    Detects prompt injection attacks using multiple techniques:
    - Pattern-based detection
    - Behavioral analysis
    - Context boundary checking
    - Encoding detection
    """
    
    # Known jailbreak patterns
    JAILBREAK_PATTERNS = [
        r"ignore (previous|all|above) (instructions|prompts|rules)",
        r"disregard (previous|all|above) (instructions|prompts|rules)",
        r"forget (previous|all|above) (instructions|prompts|rules)",
        r"you are now (in|a) (DAN|developer|god) mode",
        r"pretend (you are|to be) (not|no longer) (an AI|constrained)",
        r"act as if you (have no|don't have) (restrictions|limitations|rules)",
        r"from now on.*respond as",
        r"new instructions:.*override",
        r"system prompt.*replace with",
    ]
    
    # Role-play manipulation
    ROLEPLAY_PATTERNS = [
        r"you are now.*character",
        r"roleplay as.*without restrictions",
        r"pretend you are.*evil",
        r"act as.*unethical",
    ]
    
    # Context manipulation
    CONTEXT_PATTERNS = [
        r"---.*END OF CONTEXT.*---",
        r"```.*system.*```",
        r"\[SYSTEM\].*\[/SYSTEM\]",
        r"<system>.*</system>",
    ]
    
    # Encoding attacks
    ENCODING_PATTERNS = [
        r"\\x[0-9a-fA-F]{2}",  # Hex encoding
        r"&#\d+;",  # HTML entities
        r"%[0-9a-fA-F]{2}",  # URL encoding
        r"\\u[0-9a-fA-F]{4}",  # Unicode escape
    ]
    
    def __init__(self):
        """Initialize the detector."""
        self.compiled_patterns = {
            InjectionType.JAILBREAK: [re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS],
            InjectionType.ROLE_PLAY: [re.compile(p, re.IGNORECASE) for p in self.ROLEPLAY_PATTERNS],
            InjectionType.DELIMITER_MANIPULATION: [re.compile(p, re.IGNORECASE) for p in self.CONTEXT_PATTERNS],
            InjectionType.ENCODING_ATTACK: [re.compile(p) for p in self.ENCODING_PATTERNS],
        }
    
    def detect(self, user_input: str) -> InjectionDetection:
        """
        Detect prompt injection in user input.
        
        Args:
            user_input: The user's input to analyze
            
        Returns:
            InjectionDetection result
        """
        matched_patterns = []
        injection_types = []
        risk_score = 0
        
        # Check each pattern category
        for injection_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(user_input):
                    matched_patterns.append(pattern.pattern)
                    injection_types.append(injection_type)
                    risk_score += 20
        
        # Check for context overflow (very long inputs)
        if len(user_input) > 10000:
            injection_types.append(InjectionType.CONTEXT_OVERFLOW)
            risk_score += 15
        
        # Check for suspicious instruction keywords
        instruction_keywords = [
            "ignore", "disregard", "forget", "override", "bypass",
            "jailbreak", "unrestricted", "uncensored", "unfiltered"
        ]
        keyword_count = sum(1 for kw in instruction_keywords if kw in user_input.lower())
        if keyword_count >= 2:
            risk_score += keyword_count * 10
        
        # Determine if malicious
        is_malicious = risk_score > 30
        confidence = min(risk_score / 100.0, 1.0)
        
        # Generate explanation
        if is_malicious:
            explanation = f"Detected {len(matched_patterns)} suspicious patterns. "
            explanation += f"Input contains {keyword_count} instruction manipulation keywords. "
            if injection_types:
                types_str = ", ".join(set(t.value for t in injection_types))
                explanation += f"Attack types: {types_str}."
        else:
            explanation = "No significant injection patterns detected."
        
        # Recommended action
        if risk_score > 70:
            action = "BLOCK - High confidence prompt injection attack"
        elif risk_score > 30:
            action = "WARN - Suspicious input, requires review"
        else:
            action = "ALLOW - Input appears safe"
        
        return InjectionDetection(
            is_malicious=is_malicious,
            confidence=confidence,
            injection_type=injection_types[0] if injection_types else InjectionType.DIRECT_INJECTION,
            matched_patterns=matched_patterns,
            risk_score=min(risk_score, 100),
            explanation=explanation,
            recommended_action=action,
        )
    
    def sanitize(self, user_input: str) -> str:
        """
        Sanitize input by removing potential injection patterns.
        
        Args:
            user_input: The input to sanitize
            
        Returns:
            Sanitized input
        """
        sanitized = user_input
        
        # Remove common delimiter manipulations
        sanitized = re.sub(r'---.*?---', '', sanitized, flags=re.DOTALL)
        sanitized = re.sub(r'```.*?```', '', sanitized, flags=re.DOTALL)
        sanitized = re.sub(r'\[SYSTEM\].*?\[/SYSTEM\]', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        return sanitized.strip()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics."""
        return {
            "total_patterns": sum(len(patterns) for patterns in self.compiled_patterns.values()),
            "pattern_categories": len(self.compiled_patterns),
            "supported_attack_types": [t.value for t in InjectionType],
        }


# Global instance
prompt_injection_detector = PromptInjectionDetector()
