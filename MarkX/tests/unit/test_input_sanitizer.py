# test_input_sanitizer.py - Unit tests for input sanitizer

import pytest
import sys
from pathlib import Path

# Add MarkX to path
markx_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(markx_path))

from core.input_sanitizer import InputSanitizer


class TestInputSanitizer:
    """Test InputSanitizer class."""
    
    def test_sanitize_secrets(self):
        """Test that secrets are stripped from messages."""
        message = "My API key is sk-1234567890 and password is secret123"
        sanitized, modified = InputSanitizer.sanitize_message(message)
        
        assert modified is True
        assert "sk-1234567890" not in sanitized
        assert "secret123" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_sanitize_pii_email(self):
        """Test that email addresses are redacted."""
        message = "Contact me at john.doe@example.com for details"
        sanitized, modified = InputSanitizer.sanitize_message(message)
        
        assert modified is True
        assert "john.doe@example.com" not in sanitized
        assert "[EMAIL]" in sanitized
    
    def test_sanitize_pii_ssn(self):
        """Test that SSNs are redacted."""
        message = "SSN: 123-45-6789"
        sanitized, modified = InputSanitizer.sanitize_message(message)
        
        assert modified is True
        assert "123-45-6789" not in sanitized
        assert "[SSN]" in sanitized
    
    def test_sanitize_pii_credit_card(self):
        """Test that credit card numbers are redacted."""
        message = "Card: 4532-1234-5678-9010"
        sanitized, modified = InputSanitizer.sanitize_message(message)
        
        assert modified is True
        assert "4532-1234-5678-9010" not in sanitized
        assert "[CREDIT_CARD]" in sanitized
    
    def test_sanitize_sql_injection(self):
        """Test that SQL injection attempts are blocked."""
        context = {
            "entity_id": "db-1' OR '1'='1",
            "query": "SELECT * FROM users WHERE id = '1' OR '1'='1'"
        }
        
        result = InputSanitizer.sanitize_context(context)
        
        assert result.is_safe is False
        assert len(result.validation_errors) > 0
        assert "SQL injection" in result.validation_errors[0]
    
    def test_sanitize_clean_message(self):
        """Test that clean messages pass through unchanged."""
        message = "This is a clean message with no secrets or PII"
        sanitized, modified = InputSanitizer.sanitize_message(message)
        
        assert modified is False
        assert sanitized == message
    
    def test_sanitize_context_valid(self):
        """Test sanitizing valid context."""
        context = {
            "entity_id": "customer-db",
            "risk_score": 85,
            "severity": "high"
        }
        
        result = InputSanitizer.sanitize_context(context)
        
        assert result.is_safe is True
        assert result.sanitized_data == context
        assert len(result.validation_errors) == 0
    
    def test_sanitize_context_with_secrets(self):
        """Test sanitizing context with secrets."""
        context = {
            "entity_id": "customer-db",
            "api_key": "sk-1234567890",
            "password": "secret123"
        }
        
        result = InputSanitizer.sanitize_context(context)
        
        assert result.is_safe is True
        assert result.sanitized_data["api_key"] == "[REDACTED]"
        assert result.sanitized_data["password"] == "[REDACTED]"
        assert result.sanitized_data["entity_id"] == "customer-db"
    
    def test_sanitize_context_with_pii(self):
        """Test sanitizing context with PII."""
        context = {
            "entity_id": "customer-db",
            "email": "john.doe@example.com",
            "ssn": "123-45-6789"
        }
        
        result = InputSanitizer.sanitize_context(context)
        
        assert result.is_safe is True
        assert "[EMAIL]" in str(result.sanitized_data["email"])
        assert "[SSN]" in str(result.sanitized_data["ssn"])
    
    def test_sanitize_nested_context(self):
        """Test sanitizing nested context structures."""
        context = {
            "entity": {
                "id": "customer-db",
                "credentials": {
                    "api_key": "sk-1234567890",
                    "password": "secret123"
                }
            }
        }
        
        result = InputSanitizer.sanitize_context(context)
        
        assert result.is_safe is True
        assert result.sanitized_data["entity"]["credentials"]["api_key"] == "[REDACTED]"
        assert result.sanitized_data["entity"]["credentials"]["password"] == "[REDACTED]"
    
    def test_multiple_secrets_in_message(self):
        """Test handling multiple secrets in one message."""
        message = "API key: sk-123 and token: tok-456 and password: pass123"
        sanitized, modified = InputSanitizer.sanitize_message(message)
        
        assert modified is True
        assert "sk-123" not in sanitized
        assert "tok-456" not in sanitized
        assert "pass123" not in sanitized
        assert sanitized.count("[REDACTED]") >= 3
    
    def test_empty_message(self):
        """Test handling empty message."""
        message = ""
        sanitized, modified = InputSanitizer.sanitize_message(message)
        
        assert modified is False
        assert sanitized == ""
    
    def test_empty_context(self):
        """Test handling empty context."""
        context = {}
        result = InputSanitizer.sanitize_context(context)
        
        assert result.is_safe is True
        assert result.sanitized_data == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
