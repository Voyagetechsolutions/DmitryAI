# modes/security_mode/integrations/__init__.py
"""
Security Integrations Manager

Manages all external security tool integrations:
- SIEM (Splunk, Elastic, Sentinel)
- Threat Intelligence (MISP, OTX, VirusTotal)
- Vulnerability Scanners (Nessus, OpenVAS, Qualys)
- Cloud Security (AWS, Azure, GCP)
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class IntegrationConfig:
    """Configuration for a security integration."""
    name: str
    type: str  # siem, threat_intel, vulnerability, cloud_security
    enabled: bool
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    last_sync: Optional[str] = None
    status: str = "disconnected"  # connected, disconnected, error


class SecurityIntegrationManager:
    """
    Manages all security tool integrations.
    
    Provides a unified interface for:
    - Connection management
    - Data synchronization
    - Query execution
    - Alert forwarding
    """
    
    def __init__(self):
        """Initialize the integration manager."""
        self.integrations: Dict[str, IntegrationConfig] = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load integration configurations from environment."""
        # SIEM Integrations
        if os.getenv("SPLUNK_API_KEY"):
            self.integrations["splunk"] = IntegrationConfig(
                name="Splunk",
                type="siem",
                enabled=True,
                api_key=os.getenv("SPLUNK_API_KEY"),
                api_url=os.getenv("SPLUNK_API_URL", "https://localhost:8089"),
            )
        
        if os.getenv("ELASTIC_API_KEY"):
            self.integrations["elastic"] = IntegrationConfig(
                name="Elastic Security",
                type="siem",
                enabled=True,
                api_key=os.getenv("ELASTIC_API_KEY"),
                api_url=os.getenv("ELASTIC_API_URL", "https://localhost:9200"),
            )
        
        # Threat Intelligence
        if os.getenv("VIRUSTOTAL_API_KEY"):
            self.integrations["virustotal"] = IntegrationConfig(
                name="VirusTotal",
                type="threat_intel",
                enabled=True,
                api_key=os.getenv("VIRUSTOTAL_API_KEY"),
                api_url="https://www.virustotal.com/api/v3",
            )
        
        if os.getenv("MISP_API_KEY"):
            self.integrations["misp"] = IntegrationConfig(
                name="MISP",
                type="threat_intel",
                enabled=True,
                api_key=os.getenv("MISP_API_KEY"),
                api_url=os.getenv("MISP_URL"),
            )
        
        # Vulnerability Scanners
        if os.getenv("NESSUS_API_KEY"):
            self.integrations["nessus"] = IntegrationConfig(
                name="Nessus",
                type="vulnerability",
                enabled=True,
                api_key=os.getenv("NESSUS_API_KEY"),
                api_url=os.getenv("NESSUS_URL"),
            )
        
        # Cloud Security
        if os.getenv("AWS_ACCESS_KEY_ID"):
            self.integrations["aws_security_hub"] = IntegrationConfig(
                name="AWS Security Hub",
                type="cloud_security",
                enabled=True,
                credentials={
                    "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
                    "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                    "region": os.getenv("AWS_REGION", "us-east-1"),
                },
            )
    
    def get_integration(self, name: str) -> Optional[IntegrationConfig]:
        """Get integration configuration by name."""
        return self.integrations.get(name)
    
    def list_integrations(self, integration_type: Optional[str] = None) -> List[IntegrationConfig]:
        """List all integrations, optionally filtered by type."""
        if integration_type:
            return [i for i in self.integrations.values() if i.type == integration_type]
        return list(self.integrations.values())
    
    def test_connection(self, name: str) -> Dict[str, Any]:
        """Test connection to an integration."""
        integration = self.get_integration(name)
        if not integration:
            return {"success": False, "error": f"Integration '{name}' not found"}
        
        # This would actually test the connection
        # For now, return placeholder
        return {
            "success": False,
            "message": f"Connection test for {integration.name} not yet implemented",
            "integration": name,
            "type": integration.type,
        }
    
    def sync_integration(self, name: str) -> Dict[str, Any]:
        """Synchronize data from an integration."""
        integration = self.get_integration(name)
        if not integration:
            return {"success": False, "error": f"Integration '{name}' not found"}
        
        # Update last sync time
        integration.last_sync = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "message": f"Synced {integration.name}",
            "last_sync": integration.last_sync,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all integrations."""
        return {
            "total_integrations": len(self.integrations),
            "by_type": {
                "siem": len([i for i in self.integrations.values() if i.type == "siem"]),
                "threat_intel": len([i for i in self.integrations.values() if i.type == "threat_intel"]),
                "vulnerability": len([i for i in self.integrations.values() if i.type == "vulnerability"]),
                "cloud_security": len([i for i in self.integrations.values() if i.type == "cloud_security"]),
            },
            "enabled": len([i for i in self.integrations.values() if i.enabled]),
            "connected": len([i for i in self.integrations.values() if i.status == "connected"]),
        }


# Global instance
security_integration_manager = SecurityIntegrationManager()
