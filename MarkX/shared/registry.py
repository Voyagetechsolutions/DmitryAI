# shared/registry.py
"""Service registration and heartbeat with Platform."""

import asyncio
import logging
import time
from datetime import datetime
import requests
from typing import List, Optional

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registers service with Platform and sends heartbeats."""
    
    def __init__(
        self,
        platform_url: str,
        service_name: str,
        service_type: str,
        service_url: str,
        version: str,
        capabilities: List[str],
        heartbeat_interval: int = 10,
    ):
        self.platform_url = platform_url
        self.service_name = service_name
        self.service_type = service_type
        self.service_url = service_url
        self.version = version
        self.capabilities = capabilities
        self.heartbeat_interval = heartbeat_interval
        self._registered = False
        self._heartbeat_running = False
    
    def register(self) -> bool:
        """Register with Platform (synchronous)."""
        try:
            response = requests.post(
                f"{self.platform_url}/api/v1/services/register",
                json={
                    "service_name": self.service_name,
                    "service_type": self.service_type,
                    "base_url": self.service_url,
                    "version": self.version,
                    "capabilities": self.capabilities,
                    "health_endpoint": "/health",
                },
                timeout=10.0,
            )
            if response.status_code == 200:
                self._registered = True
                logger.info(f"✓ Registered {self.service_name} with Platform")
                return True
            logger.error(f"Failed to register: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def send_heartbeat(self) -> bool:
        """Send single heartbeat (synchronous)."""
        if not self._registered:
            return False
        
        try:
            response = requests.post(
                f"{self.platform_url}/api/v1/services/heartbeat",
                json={
                    "service_name": self.service_name,
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            return False
    
    def deregister(self) -> None:
        """Deregister from Platform (synchronous)."""
        if not self._registered:
            return
        
        try:
            requests.post(
                f"{self.platform_url}/api/v1/services/deregister",
                json={"service_name": self.service_name},
                timeout=5.0,
            )
            logger.info(f"✓ Deregistered {self.service_name}")
        except Exception as e:
            logger.warning(f"Deregistration failed: {e}")
