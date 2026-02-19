# core/resilience.py
"""
Error Recovery & Resilience System
"""

import time
import asyncio
from typing import Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise e


def retry_with_backoff(config: RetryConfig = None):
    if config is None:
        config = RetryConfig()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = min(
                            config.base_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )
                        time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


class ResilientLLM:
    def __init__(self, llm_instance):
        self.llm = llm_instance
        self.circuit_breaker = CircuitBreaker()
        
    @retry_with_backoff(RetryConfig(max_attempts=3, base_delay=2.0))
    def get_response(self, *args, **kwargs):
        return self.circuit_breaker.call(self.llm.get_response, *args, **kwargs)


def graceful_tool_execution(tool_func, fallback_message="Tool execution failed"):
    def wrapper(*args, **kwargs):
        try:
            return tool_func(*args, **kwargs)
        except Exception as e:
            print(f"Tool failed gracefully: {e}")
            return {"status": "failed", "message": fallback_message, "error": str(e)}
    return wrapper