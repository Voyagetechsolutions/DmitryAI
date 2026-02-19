# reliability/verifier.py
"""
Code Verifier - Validates code through execution and testing.

Provides confidence scoring for algorithm implementations.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from tools.code.sandbox import CodeSandbox, ExecutionResult


class ConfidenceLevel(Enum):
    """Confidence levels for code verification."""
    UNVERIFIED = "unverified"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


@dataclass
class TestCase:
    """A test case for verification."""
    name: str
    input_data: str
    expected_output: str
    actual_output: Optional[str] = None
    passed: Optional[bool] = None


@dataclass
class VerificationResult:
    """Result of code verification."""
    confidence: ConfidenceLevel
    confidence_score: float  # 0.0 to 1.0
    executed: bool
    tests_run: int
    tests_passed: int
    test_cases: List[TestCase] = field(default_factory=list)
    execution_output: str = ""
    error: Optional[str] = None
    
    @property
    def all_tests_passed(self) -> bool:
        return self.tests_run > 0 and self.tests_passed == self.tests_run
    
    def to_dict(self) -> dict:
        return {
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "executed": self.executed,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "all_tests_passed": self.all_tests_passed,
            "error": self.error,
        }


class CodeVerifier:
    """
    Verifies code correctness through execution and testing.
    """
    
    def __init__(self):
        self._sandbox = CodeSandbox()
    
    def _calculate_confidence(
        self,
        executed: bool,
        tests_run: int,
        tests_passed: int,
        has_edge_cases: bool,
    ) -> tuple[ConfidenceLevel, float]:
        """Calculate confidence level and score."""
        if not executed:
            return ConfidenceLevel.UNVERIFIED, 0.0
        
        if tests_run == 0:
            # Code ran but no tests
            return ConfidenceLevel.LOW, 0.3
        
        pass_rate = tests_passed / tests_run if tests_run > 0 else 0
        
        if pass_rate < 0.5:
            return ConfidenceLevel.LOW, 0.2 + (pass_rate * 0.2)
        elif pass_rate < 1.0:
            return ConfidenceLevel.MEDIUM, 0.4 + (pass_rate * 0.3)
        else:
            # All tests passed
            if tests_run >= 5 and has_edge_cases:
                return ConfidenceLevel.VERIFIED, 0.95
            elif tests_run >= 3:
                return ConfidenceLevel.HIGH, 0.85
            else:
                return ConfidenceLevel.MEDIUM, 0.7
    
    def verify_with_tests(
        self,
        code: str,
        tests: str,
        timeout: int = 60,
    ) -> VerificationResult:
        """
        Verify code by running tests.
        
        Args:
            code: The code to verify
            tests: Test code (pytest or unittest format)
            timeout: Maximum execution time
            
        Returns:
            VerificationResult
        """
        # Combine code and tests
        full_code = f"{code}\n\n{tests}\n"
        
        # Add pytest runner if not present
        if "if __name__" not in full_code:
            if "pytest" in tests or "@pytest" in tests:
                full_code += """
if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
"""
            elif "unittest" in tests or "TestCase" in tests:
                full_code += """
if __name__ == "__main__":
    import unittest
    unittest.main(verbosity=2)
"""
        
        # Execute
        result = self._sandbox.execute_python(full_code, timeout=timeout)
        
        if result.error:
            return VerificationResult(
                confidence=ConfidenceLevel.UNVERIFIED,
                confidence_score=0.0,
                executed=False,
                tests_run=0,
                tests_passed=0,
                error=result.error,
            )
        
        # Parse test results from output
        output = result.stdout + "\n" + result.stderr
        
        import re
        
        # Count passed/failed tests
        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        error_match = re.search(r"(\d+) error", output)
        
        tests_passed = int(passed_match.group(1)) if passed_match else 0
        tests_failed = int(failed_match.group(1)) if failed_match else 0
        tests_error = int(error_match.group(1)) if error_match else 0
        tests_run = tests_passed + tests_failed + tests_error
        
        # If no pytest output, check return code
        if tests_run == 0:
            if result.success:
                tests_run = 1
                tests_passed = 1
            elif "AssertionError" in output:
                tests_run = 1
                tests_passed = 0
        
        # Check for edge case tests
        has_edge_cases = any(
            kw in tests.lower() 
            for kw in ["edge", "boundary", "empty", "zero", "negative", "overflow"]
        )
        
        confidence, score = self._calculate_confidence(
            executed=True,
            tests_run=tests_run,
            tests_passed=tests_passed,
            has_edge_cases=has_edge_cases,
        )
        
        return VerificationResult(
            confidence=confidence,
            confidence_score=score,
            executed=True,
            tests_run=tests_run,
            tests_passed=tests_passed,
            execution_output=output,
            error=None if result.success else output,
        )
    
    def verify_with_examples(
        self,
        code: str,
        test_cases: List[TestCase],
        function_name: str,
        timeout: int = 30,
    ) -> VerificationResult:
        """
        Verify code by running specific test cases.
        
        Args:
            code: The code to verify
            test_cases: List of test cases
            function_name: Name of the function to test
            timeout: Maximum execution time
            
        Returns:
            VerificationResult
        """
        if not test_cases:
            return VerificationResult(
                confidence=ConfidenceLevel.UNVERIFIED,
                confidence_score=0.0,
                executed=False,
                tests_run=0,
                tests_passed=0,
                error="No test cases provided",
            )
        
        # Build test runner code
        test_code = f"{code}\n\n"
        test_code += "# Test cases\n"
        test_code += "import json\n"
        test_code += "results = []\n\n"
        
        for i, tc in enumerate(test_cases):
            test_code += f"""
# Test case {i+1}: {tc.name}
try:
    result = {function_name}({tc.input_data})
    expected = {tc.expected_output}
    passed = result == expected
    results.append({{"name": "{tc.name}", "passed": passed, "actual": str(result), "expected": str(expected)}})
except Exception as e:
    results.append({{"name": "{tc.name}", "passed": False, "error": str(e)}})
"""
        
        test_code += "\nprint(json.dumps(results))\n"
        
        # Execute
        result = self._sandbox.execute_python(test_code, timeout=timeout)
        
        if result.error:
            return VerificationResult(
                confidence=ConfidenceLevel.UNVERIFIED,
                confidence_score=0.0,
                executed=False,
                tests_run=0,
                tests_passed=0,
                error=result.error,
            )
        
        # Parse results
        import json
        try:
            test_results = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return VerificationResult(
                confidence=ConfidenceLevel.LOW,
                confidence_score=0.2,
                executed=True,
                tests_run=len(test_cases),
                tests_passed=0,
                execution_output=result.stdout,
                error="Could not parse test results",
            )
        
        tests_passed = sum(1 for r in test_results if r.get("passed"))
        
        # Update test cases with results
        for tc, res in zip(test_cases, test_results):
            tc.passed = res.get("passed", False)
            tc.actual_output = res.get("actual")
        
        has_edge_cases = any(
            "edge" in tc.name.lower() or "empty" in tc.name.lower()
            for tc in test_cases
        )
        
        confidence, score = self._calculate_confidence(
            executed=True,
            tests_run=len(test_cases),
            tests_passed=tests_passed,
            has_edge_cases=has_edge_cases,
        )
        
        return VerificationResult(
            confidence=confidence,
            confidence_score=score,
            executed=True,
            tests_run=len(test_cases),
            tests_passed=tests_passed,
            test_cases=test_cases,
            execution_output=result.stdout,
        )
    
    def quick_verify(self, code: str, timeout: int = 10) -> VerificationResult:
        """
        Quick verification - just check if code runs without errors.
        
        Args:
            code: The code to verify
            timeout: Maximum execution time
            
        Returns:
            VerificationResult
        """
        result = self._sandbox.execute_python(code, timeout=timeout)
        
        if result.error:
            return VerificationResult(
                confidence=ConfidenceLevel.UNVERIFIED,
                confidence_score=0.0,
                executed=False,
                tests_run=0,
                tests_passed=0,
                error=result.error,
            )
        
        if result.success:
            return VerificationResult(
                confidence=ConfidenceLevel.LOW,
                confidence_score=0.3,
                executed=True,
                tests_run=0,
                tests_passed=0,
                execution_output=result.stdout,
            )
        else:
            return VerificationResult(
                confidence=ConfidenceLevel.UNVERIFIED,
                confidence_score=0.1,
                executed=True,
                tests_run=0,
                tests_passed=0,
                execution_output=result.stdout + result.stderr,
                error=f"Code exited with code {result.return_code}",
            )
