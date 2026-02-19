# reliability/__init__.py
"""
Dmitry v1.2 Algorithm Reliability System

When solving complex algorithms:
1. Decompose problem
2. Define constraints and edge cases
3. Generate code
4. Generate tests
5. Execute code
6. Validate results

No verification → low confidence output.
"""

from .verifier import CodeVerifier, VerificationResult

__all__ = [
    "CodeVerifier",
    "VerificationResult",
]
