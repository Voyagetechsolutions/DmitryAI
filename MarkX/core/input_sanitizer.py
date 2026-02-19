# core/input_sanitizer.py
"""
Input Sanitizer - Treat all text as untrusted.

Strips secrets, redacts PII, validates schema, prevents injection.
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class SanitizationResult:
    """Result of input sanitization."""
    
    sanitized_data: Dict[str, Any]
    redacted_fields: List[str]
    validation_errors: List[str]
    is_safe: bool


class InputSanitizer:
    """
    Sanitizes all user input before processing.
    
    Treats all text as untrusted:
    - Strips secrets
    - Redacts PII
    - Validates schema
    - Prevents injection
    """
    
    # Patterns for sensitive data
    SECRET_PATTERNS = {
        "api_key": r"(?i)(api[_-]?key|apikey)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_\-]{20,})",
        "password": r"(?i)(password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?([^\s\"']{8,})",
        "token": r"(?i)(token|bearer)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_\-\.]{20,})",
        "secret": r"(?i)(secret|private[_-]?key)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_\-]{20,})",
    }
    
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    }
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(?i)(union\s+select|drop\s+table|delete\s+from|insert\s+into)",
        r"(?i)(exec\s*\(|execute\s*\(|script\s*>)",
        r"['\";].*(-{2}|\/\*|\*\/)",
    ]
    
    @staticmethod
    def sanitize_context(context: Dict[str, Any]) -> SanitizationResult:
        """
        Sanitize user context before processing.
        
        Args:
            context: User-provided context
            
        Returns:
            SanitizationResult with sanitized data
        """
        sanitized = {}
        redacted_fields = []
        validation_errors = []
        
        for key, value in context.items():
            # Check for secrets in key names
            if InputSanitizer._is_secret_key(key):
                sanitized[key] = "***REDACTED***"
                redacted_fields.append(key)
                continue
            
            # Sanitize value
            if isinstance(value, str):
                sanitized_value, was_redacted = InputSanitizer._sanitize_string(value)
                sanitized[key] = sanitized_value
                if was_redacted:
                    redacted_fields.append(key)
            elif isinstance(value, dict):
                nested_result = InputSanitizer.sanitize_context(value)
                sanitized[key] = nested_result.sanitized_data
                redacted_fields.extend([f"{key}.{f}" for f in nested_result.redacted_fields])
                validation_errors.extend(nested_result.validation_errors)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputSanitizer._sanitize_string(item)[0] if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        # Validate schema
        schema_errors = InputSanitizer._validate_context_schema(sanitized)
        validation_errors.extend(schema_errors)
        
        is_safe = len(validation_errors) == 0
        
        return SanitizationResult(
            sanitized_data=sanitized,
            redacted_fields=redacted_fields,
            validation_errors=validation_errors,
            is_safe=is_safe,
        )
    
    @staticmethod
    def sanitize_message(message: str) -> tuple[str, bool]:
        """
        Sanitize user message.
        
        Args:
            message: User message
            
        Returns:
            (sanitized_message, was_modified)
        """
        original = message
        
        # Strip secrets
        for pattern_name, pattern in InputSanitizer.SECRET_PATTERNS.items():
            message = re.sub(pattern, f"\\1=***REDACTED***", message)
        
        # Redact PII
        for pattern_name, pattern in InputSanitizer.PII_PATTERNS.items():
            message = re.sub(pattern, f"[{pattern_name.upper()}_REDACTED]", message)
        
        # Check for SQL injection
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, message):
                # Don't modify, but flag it
                message = "[POTENTIALLY_UNSAFE_INPUT] " + message
                break
        
        was_modified = message != original
        return message, was_modified
    
    @staticmethod
    def _is_secret_key(key: str) -> bool:
        """Check if key name indicates secret data."""
        key_lower = key.lower()
        secret_indicators = [
            "password", "passwd", "pwd",
            "secret", "api_key", "apikey",
            "token", "bearer",
            "private_key", "privatekey",
            "credential", "auth",
        ]
        return any(indicator in key_lower for indicator in secret_indicators)
    
    @staticmethod
    def _sanitize_string(value: str) -> tuple[str, bool]:
        """
        Sanitize a string value.
        
        Returns:
            (sanitized_value, was_redacted)
        """
        original = value
        
        # Strip secrets
        for pattern_name, pattern in InputSanitizer.SECRET_PATTERNS.items():
            value = re.sub(pattern, f"\\1=***REDACTED***", value)
        
        # Redact PII
        for pattern_name, pattern in InputSanitizer.PII_PATTERNS.items():
            value = re.sub(pattern, f"[{pattern_name.upper()}_REDACTED]", value)
        
        was_redacted = value != original
        return value, was_redacted
    
    @staticmethod
    def _validate_context_schema(context: Dict[str, Any]) -> List[str]:
        """
        Validate context against expected schema.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for required fields (if any)
        # This is flexible - context can have any fields
        
        # Check for suspicious patterns
        for key, value in context.items():
            if isinstance(value, str):
                # Check for SQL injection
                for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
                    if re.search(pattern, value):
                        errors.append(f"Potentially unsafe input in field '{key}'")
                
                # Check for excessive length
                if len(value) > 10000:
                    errors.append(f"Field '{key}' exceeds maximum length (10000 chars)")
        
        return errors


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    import json
    
    # Example 1: Clean context
    context1 = {
        "entity_id": "customer-db",
        "risk_score": 85,
        "threat_type": "data_exposure"
    }
    
    result1 = InputSanitizer.sanitize_context(context1)
    print("Example 1: Clean context")
    print(f"Is safe: {result1.is_safe}")
    print(f"Sanitized: {json.dumps(result1.sanitized_data, indent=2)}")
    
    # Example 2: Context with secrets
    context2 = {
        "entity_id": "customer-db",
        "api_key": "sk_live_abc123def456",
        "password": "MySecretPassword123"
    }
    
    result2 = InputSanitizer.sanitize_context(context2)
    print("\nExample 2: Context with secrets")
    print(f"Is safe: {result2.is_safe}")
    print(f"Redacted fields: {result2.redacted_fields}")
    print(f"Sanitized: {json.dumps(result2.sanitized_data, indent=2)}")
    
    # Example 3: Context with PII
    context3 = {
        "entity_id": "customer-db",
        "user_email": "john.doe@example.com",
        "ssn": "123-45-6789"
    }
    
    result3 = InputSanitizer.sanitize_context(context3)
    print("\nExample 3: Context with PII")
    print(f"Is safe: {result3.is_safe}")
    print(f"Redacted fields: {result3.redacted_fields}")
    print(f"Sanitized: {json.dumps(result3.sanitized_data, indent=2)}")
    
    # Example 4: Message with secrets
    message = "Check api_key=sk_live_abc123 and password=secret123"
    sanitized_msg, was_modified = InputSanitizer.sanitize_message(message)
    print("\nExample 4: Message with secrets")
    print(f"Original: {message}")
    print(f"Sanitized: {sanitized_msg}")
    print(f"Was modified: {was_modified}")
    
    # Example 5: SQL injection attempt
    context5 = {
        "entity_id": "customer-db'; DROP TABLE users; --"
    }
    
    result5 = InputSanitizer.sanitize_context(context5)
    print("\nExample 5: SQL injection attempt")
    print(f"Is safe: {result5.is_safe}")
    print(f"Errors: {result5.validation_errors}")
