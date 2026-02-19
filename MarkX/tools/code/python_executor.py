# tools/code/python_executor.py
"""
Python Executor Tool - Executes Python code in a sandbox.
"""

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel
from .sandbox import CodeSandbox


class PythonExecutorTool(BaseTool):
    """Tool to execute Python code in a sandbox."""
    
    def __init__(self):
        super().__init__()
        self._name = "python_executor"
        self._description = "Execute Python code in a safe sandbox (requires confirmation)"
        self._permission_level = PermissionLevel.EXECUTE
        self._needs_confirmation = True
        self._sandbox = CodeSandbox()
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds",
                    "default": 30,
                },
            },
            "required": ["code"],
        }
    
    def _execute(
        self,
        code: str,
        timeout: int = 30,
        **kwargs,
    ) -> ToolResult:
        """Execute the Python code."""
        if not code or not code.strip():
            return ToolResult(
                status=ToolStatus.FAILED,
                error="No code provided",
            )
        
        # Limit timeout
        timeout = min(timeout, 60)
        
        # Execute in sandbox
        result = self._sandbox.execute_python(code, timeout=timeout)
        
        if result.error:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=result.error,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": result.execution_time,
                },
            )
        
        if result.success:
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Code executed successfully in {result.execution_time:.2f}s",
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.return_code,
                    "execution_time": result.execution_time,
                },
            )
        else:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Code exited with return code {result.return_code}",
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.return_code,
                    "execution_time": result.execution_time,
                },
            )
    
    def get_confirmation_message(self, params: dict) -> str:
        code = params.get("code", "")
        lines = code.count("\n") + 1
        return f"Execute Python code ({lines} lines)?"
