# tools/code/sandbox.py
"""
Code Sandbox - Docker-based safe execution environment.

Features:
- Docker isolation (primary)
- Process-level fallback for trusted code
- CPU/memory limits
- Network isolation
- Read-only filesystem support
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
import time
from typing import Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    sandbox_type: str = "process"  # "docker" or "process"
    error: Optional[str] = None


class DockerSandbox:
    """
    Docker-based code execution sandbox.
    
    Provides strong isolation with:
    - Network disabled by default
    - CPU/memory limits
    - Read-only filesystem option
    - Timeout enforcement
    """
    
    # Docker image for Python execution
    PYTHON_IMAGE = "python:3.11-slim"
    NODE_IMAGE = "node:20-slim"
    
    # Resource limits
    DEFAULT_MEMORY_LIMIT = "256m"
    DEFAULT_CPU_LIMIT = "0.5"
    
    def __init__(self):
        self._docker_available = self._check_docker()
        self._sandbox_dir = os.path.join(tempfile.gettempdir(), "dmitry_sandbox")
        os.makedirs(self._sandbox_dir, exist_ok=True)
    
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @property
    def is_docker_available(self) -> bool:
        return self._docker_available
    
    def _create_temp_file(self, content: str, extension: str) -> str:
        """Create a temporary file with content."""
        import uuid
        filename = f"code_{uuid.uuid4().hex[:8]}{extension}"
        filepath = os.path.join(self._sandbox_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath
    
    def _truncate_output(self, output: str, max_size: int = 100 * 1024) -> str:
        """Truncate output if too long."""
        if len(output) > max_size:
            return output[:max_size] + "\n...[output truncated]"
        return output
    
    def execute_in_docker(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30,
        memory_limit: str = None,
        cpu_limit: str = None,
        network_enabled: bool = False,
        read_only: bool = True,
    ) -> ExecutionResult:
        """
        Execute code in Docker container.
        
        Args:
            code: Code to execute
            language: "python" or "node"
            timeout: Maximum execution time
            memory_limit: Memory limit (e.g., "256m")
            cpu_limit: CPU limit (e.g., "0.5")
            network_enabled: Allow network access
            read_only: Mount filesystem as read-only
            
        Returns:
            ExecutionResult
        """
        if not self._docker_available:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                execution_time=0,
                error="Docker is not available",
            )
        
        # Select image and extension
        if language == "python":
            image = self.PYTHON_IMAGE
            extension = ".py"
            cmd = ["python", "/workspace/code" + extension]
        elif language == "node":
            image = self.NODE_IMAGE
            extension = ".js"
            cmd = ["node", "/workspace/code" + extension]
        else:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                execution_time=0,
                error=f"Unsupported language: {language}",
            )
        
        # Create temp file
        filepath = self._create_temp_file(code, extension)
        
        try:
            # Build docker command
            docker_cmd = [
                "docker", "run",
                "--rm",  # Remove container after execution
                "--name", f"dmitry_sandbox_{os.getpid()}_{int(time.time())}",
            ]
            
            # Resource limits
            docker_cmd.extend([
                "--memory", memory_limit or self.DEFAULT_MEMORY_LIMIT,
                "--cpus", cpu_limit or self.DEFAULT_CPU_LIMIT,
            ])
            
            # Network isolation
            if not network_enabled:
                docker_cmd.extend(["--network", "none"])
            
            # Mount code file
            mount_mode = "ro" if read_only else "rw"
            docker_cmd.extend([
                "-v", f"{filepath}:/workspace/code{extension}:{mount_mode}",
            ])
            
            # Image and command
            docker_cmd.append(image)
            docker_cmd.extend(cmd)
            
            # Execute
            start_time = time.time()
            
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=self._truncate_output(result.stdout),
                stderr=self._truncate_output(result.stderr),
                return_code=result.returncode,
                execution_time=execution_time,
                sandbox_type="docker",
            )
            
        except subprocess.TimeoutExpired:
            # Kill the container
            try:
                subprocess.run(
                    ["docker", "kill", f"dmitry_sandbox_{os.getpid()}_{int(time.time())}"],
                    capture_output=True,
                    timeout=5,
                )
            except Exception:
                pass
            
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                execution_time=timeout,
                sandbox_type="docker",
                error=f"Execution timed out after {timeout} seconds",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time=0,
                sandbox_type="docker",
                error=str(e),
            )
        finally:
            # Cleanup
            try:
                os.unlink(filepath)
            except Exception:
                pass


class ProcessSandbox:
    """
    Process-level sandbox for trusted code.
    
    Faster than Docker but less isolated.
    Use for trusted internal utilities only.
    """
    
    DEFAULT_TIMEOUT = 30
    MAX_OUTPUT_SIZE = 100 * 1024
    
    def __init__(self):
        self._sandbox_dir = os.path.join(tempfile.gettempdir(), "dmitry_sandbox")
        os.makedirs(self._sandbox_dir, exist_ok=True)
    
    def _create_temp_file(self, content: str, extension: str) -> str:
        """Create temporary file."""
        import uuid
        filename = f"code_{uuid.uuid4().hex[:8]}{extension}"
        filepath = os.path.join(self._sandbox_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath
    
    def _truncate_output(self, output: str) -> str:
        """Truncate output if too long."""
        if len(output) > self.MAX_OUTPUT_SIZE:
            return output[:self.MAX_OUTPUT_SIZE] + "\n...[output truncated]"
        return output
    
    def execute_python(
        self,
        code: str,
        timeout: int = None,
    ) -> ExecutionResult:
        """Execute Python code in subprocess."""
        timeout = timeout or self.DEFAULT_TIMEOUT
        filepath = self._create_temp_file(code, ".py")
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                [sys.executable, filepath],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._sandbox_dir,
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONUNBUFFERED": "1",
                },
            )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=self._truncate_output(result.stdout),
                stderr=self._truncate_output(result.stderr),
                return_code=result.returncode,
                execution_time=execution_time,
                sandbox_type="process",
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                execution_time=timeout,
                sandbox_type="process",
                error=f"Execution timed out after {timeout} seconds",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time=0,
                sandbox_type="process",
                error=str(e),
            )
        finally:
            try:
                os.unlink(filepath)
            except Exception:
                pass
    
    def execute_node(
        self,
        code: str,
        timeout: int = None,
    ) -> ExecutionResult:
        """Execute Node.js code in subprocess."""
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Check if Node is available
        try:
            subprocess.run(["node", "--version"], capture_output=True, timeout=5)
        except Exception:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                execution_time=0,
                sandbox_type="process",
                error="Node.js is not installed or not in PATH",
            )
        
        filepath = self._create_temp_file(code, ".js")
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                ["node", filepath],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._sandbox_dir,
            )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=self._truncate_output(result.stdout),
                stderr=self._truncate_output(result.stderr),
                return_code=result.returncode,
                execution_time=execution_time,
                sandbox_type="process",
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                execution_time=timeout,
                sandbox_type="process",
                error=f"Execution timed out after {timeout} seconds",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time=0,
                sandbox_type="process",
                error=str(e),
            )
        finally:
            try:
                os.unlink(filepath)
            except Exception:
                pass


class CodeSandbox:
    """
    Unified code sandbox interface.
    
    Uses Docker by default for untrusted code,
    falls back to process-level for trusted utilities.
    """
    
    def __init__(self, prefer_docker: bool = True):
        """
        Initialize sandbox.
        
        Args:
            prefer_docker: Use Docker when available
        """
        self._docker = DockerSandbox()
        self._process = ProcessSandbox()
        self._prefer_docker = prefer_docker
    
    @property
    def docker_available(self) -> bool:
        return self._docker.is_docker_available
    
    def execute_python(
        self,
        code: str,
        timeout: int = 30,
        trusted: bool = False,
        network_enabled: bool = False,
    ) -> ExecutionResult:
        """
        Execute Python code.
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time
            trusted: If True, use process sandbox (faster)
            network_enabled: Allow network access (Docker only)
            
        Returns:
            ExecutionResult
        """
        # Use Docker for untrusted code
        if self._prefer_docker and self._docker.is_docker_available and not trusted:
            return self._docker.execute_in_docker(
                code,
                language="python",
                timeout=timeout,
                network_enabled=network_enabled,
            )
        
        # Fallback to process sandbox
        return self._process.execute_python(code, timeout)
    
    def execute_node(
        self,
        code: str,
        timeout: int = 30,
        trusted: bool = False,
        network_enabled: bool = False,
    ) -> ExecutionResult:
        """
        Execute Node.js code.
        
        Args:
            code: JavaScript code to execute
            timeout: Maximum execution time
            trusted: If True, use process sandbox
            network_enabled: Allow network access
            
        Returns:
            ExecutionResult
        """
        if self._prefer_docker and self._docker.is_docker_available and not trusted:
            return self._docker.execute_in_docker(
                code,
                language="node",
                timeout=timeout,
                network_enabled=network_enabled,
            )
        
        return self._process.execute_node(code, timeout)
    
    def cleanup(self) -> None:
        """Clean up sandbox directories."""
        sandbox_dir = os.path.join(tempfile.gettempdir(), "dmitry_sandbox")
        try:
            for item in os.listdir(sandbox_dir):
                item_path = os.path.join(sandbox_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                except Exception:
                    pass
        except Exception:
            pass
    
    def get_info(self) -> dict:
        """Get sandbox info."""
        return {
            "docker_available": self._docker.is_docker_available,
            "prefer_docker": self._prefer_docker,
            "sandbox_dir": os.path.join(tempfile.gettempdir(), "dmitry_sandbox"),
        }
