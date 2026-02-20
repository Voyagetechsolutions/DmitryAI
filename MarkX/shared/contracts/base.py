# shared/contracts/base.py
"""Base contracts shared across all services."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional, List


class ServiceHealth(BaseModel):
    """Health status of a service."""
    service: str
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    uptime_seconds: float
    checks: Dict[str, bool]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ServiceRegistration(BaseModel):
    """Service registration payload."""
    service_name: str
    service_type: str  # "pdri", "aegis", "dmitry"
    base_url: str
    version: str
    capabilities: List[str]
    health_endpoint: str = "/health"


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    code: str
    details: Optional[Dict] = None
    retry_after: Optional[int] = None  # seconds
