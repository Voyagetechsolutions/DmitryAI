# tools/code/test_runner.py
"""
Test Runner Tool - Runs tests and captures results.
"""

import os
import re
from typing import Optional

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel
from .sandbox import CodeSandbox


class TestRunnerTool(BaseTool):
    """Tool to run tests (pytest/unittest) on code."""
    
    def __init__(self):
        super().__init__()
        self._name = "test_runner"
        self._description = "Run Python tests on code (requires confirmation)"
        self._permission_level = PermissionLevel.EXECUTE
        self._needs_confirmation = True
        self._sandbox = CodeSandbox()
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Main code to test",
                },
                "tests": {
                    "type": "string",
                    "description": "Test code (pytest or unittest format)",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds",
                    "default": 60,
                },
            },
            "required": ["tests"],
        }
    
    def _parse_test_output(self, output: str) -> dict:
        """Parse pytest output to extract test results."""
        results = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "total": 0,
            "failures": [],
        }
        
        # Look for pytest summary line
        # e.g., "1 passed", "2 failed, 1 passed", etc.
        summary_match = re.search(
            r"=+ ([\d\w, ]+) =+",
            output
        )
        
        if summary_match:
            summary = summary_match.group(1)
            
            passed_match = re.search(r"(\d+) passed", summary)
            if passed_match:
                results["passed"] = int(passed_match.group(1))
            
            failed_match = re.search(r"(\d+) failed", summary)
            if failed_match:
                results["failed"] = int(failed_match.group(1))
            
            error_match = re.search(r"(\d+) error", summary)
            if error_match:
                results["errors"] = int(error_match.group(1))
            
            skipped_match = re.search(r"(\d+) skipped", summary)
            if skipped_match:
                results["skipped"] = int(skipped_match.group(1))
        
        results["total"] = (
            results["passed"] + 
            results["failed"] + 
            results["errors"] + 
            results["skipped"]
        )
        
        # Extract failure details
        failure_sections = re.findall(
            r"FAILED ([\w:]+).*?\n(.*?)(?=FAILED|=====|$)",
            output,
            re.DOTALL
        )
        
        for test_name, details in failure_sections:
            results["failures"].append({
                "test": test_name.strip(),
                "details": details.strip()[:500],  # Limit size
            })
        
        return results
    
    def _execute(
        self,
        tests: str,
        code: Optional[str] = None,
        timeout: int = 60,
        **kwargs,
    ) -> ToolResult:
        """Run the tests."""
        if not tests or not tests.strip():
            return ToolResult(
                status=ToolStatus.FAILED,
                error="No test code provided",
            )
        
        # Limit timeout
        timeout = min(timeout, 120)
        
        # Build combined code
        full_code = ""
        
        if code:
            full_code += code + "\n\n"
        
        # Add test code
        full_code += tests + "\n\n"
        
        # Check if using pytest or unittest
        uses_pytest = "pytest" in tests or "@pytest" in tests
        uses_unittest = "unittest" in tests or "TestCase" in tests
        
        if uses_pytest:
            # Add pytest runner
            full_code += """
if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
"""
        elif uses_unittest:
            # Add unittest runner
            full_code += """
if __name__ == "__main__":
    import unittest
    unittest.main(verbosity=2)
"""
        else:
            # Simple assertions - just run the code
            pass
        
        # Execute in sandbox
        result = self._sandbox.execute_python(full_code, timeout=timeout)
        
        if result.error:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=result.error,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )
        
        # Parse results
        output = result.stdout + "\n" + result.stderr
        test_results = self._parse_test_output(output)
        
        # Determine overall status
        all_passed = test_results["failed"] == 0 and test_results["errors"] == 0
        
        if all_passed and test_results["total"] > 0:
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"All {test_results['passed']} tests passed",
                data={
                    "test_results": test_results,
                    "output": output,
                    "execution_time": result.execution_time,
                },
            )
        elif test_results["total"] == 0:
            # No tests found - might be simple assertions
            if result.success:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    message="Code executed without errors",
                    data={
                        "output": output,
                        "execution_time": result.execution_time,
                    },
                )
            else:
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error="Assertions failed or code error",
                    data={
                        "output": output,
                        "execution_time": result.execution_time,
                    },
                )
        else:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"{test_results['failed']} tests failed, {test_results['errors']} errors",
                data={
                    "test_results": test_results,
                    "output": output,
                    "execution_time": result.execution_time,
                },
            )
    
    def get_confirmation_message(self, params: dict) -> str:
        tests = params.get("tests", "")
        lines = tests.count("\n") + 1
        return f"Run tests ({lines} lines of test code)?"
