"""
Platform Security Tools for Dmitry

Registers Platform API tools in Dmitry's tool registry.
These tools provide access to risk intelligence, entity search,
and security actions through the unified Platform API.

Dmitry does NOT know about PDRI, Aegis, or Neo4j.
Only the Platform knows about backend services.
"""

from tools.base_tool import BaseTool, ToolResult, ToolStatus, PermissionLevel
from tools.platform.platform_client import get_platform_client
from tools.platform.cache import SimpleCache
from typing import Optional, Dict, Any


class PlatformRiskFindingsTool(BaseTool):
    """Get risk findings from Platform with caching for graceful degradation."""
    
    def __init__(self):
        super().__init__(
            name="platform_get_risk_findings",
            description="Get risk findings from Platform (supports filters: risk_level, entity_type)",
            permission_level=PermissionLevel.LOW,
            needs_confirmation=False
        )
        self.platform = get_platform_client()
        self.cache = SimpleCache(ttl=300)  # 5 minute cache
    
    def execute(self, filters: Dict[str, Any] = None) -> ToolResult:
        """
        Get risk findings with optional filters.
        
        Args:
            filters: Optional filters (risk_level, entity_type, etc.)
            
        Returns:
            ToolResult with findings
        """
        cache_key = f"findings_{hash(str(filters))}"
        
        # Try Platform first
        result = self.platform.get_risk_findings(filters or {})
        
        if result.get("error"):
            # Try cache for graceful degradation
            cached = self.cache.get(cache_key)
            if cached:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    message=f"⚠️ Using cached data (Platform unavailable: {result['error']})\n\n{cached['message']}",
                    data=cached["data"]
                )
            
            # No cache, fail gracefully
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Platform unavailable and no cached data: {result['error']}"
            )
        
        # Format findings
        findings = result.get("findings", [])
        total = result.get("total", 0)
        
        if not findings:
            message = "✅ No risk findings found"
            tool_result = ToolResult(
                status=ToolStatus.SUCCESS,
                message=message,
                data=result
            )
        else:
            output = f"🔍 Risk Findings ({total} total):\n"
            for finding in findings[:10]:  # Top 10
                entity_id = finding.get("entity_id", "Unknown")
                risk_score = finding.get("risk_score", 0)
                risk_level = finding.get("risk_level", "UNKNOWN")
                description = finding.get("description", "")
                
                emoji = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }.get(risk_level, "⚪")
                
                output += f"\n{emoji} {entity_id}: {risk_score}/100 ({risk_level})"
                if description:
                    output += f"\n   {description[:100]}..."
            
            tool_result = ToolResult(
                status=ToolStatus.SUCCESS,
                message=output,
                data=result
            )
        
        # Cache successful result
        self.cache.set(cache_key, {
            "message": tool_result.message,
            "data": tool_result.data
        })
        
        return tool_result


class PlatformFindingDetailsTool(BaseTool):
    """Get detailed information about a specific finding."""
    
    def __init__(self):
        super().__init__(
            name="platform_get_finding_details",
            description="Get detailed information about a specific risk finding",
            permission_level=PermissionLevel.LOW,
            needs_confirmation=False
        )
        self.platform = get_platform_client()
    
    def execute(self, finding_id: str) -> ToolResult:
        """
        Get finding details.
        
        Args:
            finding_id: Finding identifier
            
        Returns:
            ToolResult with detailed finding info
        """
        if not finding_id:
            return ToolResult(
                status=ToolStatus.FAILED,
                error="finding_id is required"
            )
        
        result = self.platform.get_finding_details(finding_id)
        
        if result.get("error"):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=result["error"]
            )
        
        entity_id = result.get("entity_id", "Unknown")
        risk_score = result.get("risk_score", 0)
        risk_level = result.get("risk_level", "UNKNOWN")
        description = result.get("description", "")
        
        output = f"📋 Finding Details: {entity_id}\n\n"
        output += f"Risk Score: {risk_score}/100 ({risk_level})\n"
        output += f"Description: {description}\n"
        
        if result.get("factors"):
            output += "\nRisk Factors:"
            for factor in result["factors"][:5]:
                output += f"\n  • {factor}"
        
        if result.get("recommendations"):
            output += "\n\nRecommendations:"
            for rec in result["recommendations"][:5]:
                output += f"\n  • {rec}"
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            message=output,
            data=result
        )


class PlatformSearchEntitiesTool(BaseTool):
    """Search for entities across the platform."""
    
    def __init__(self):
        super().__init__(
            name="platform_search_entities",
            description="Search for entities (databases, systems, users) across the platform",
            permission_level=PermissionLevel.LOW,
            needs_confirmation=False
        )
        self.platform = get_platform_client()
    
    def execute(self, query: str, filters: Dict[str, Any] = None) -> ToolResult:
        """
        Search for entities.
        
        Args:
            query: Search query
            filters: Optional filters
            
        Returns:
            ToolResult with search results
        """
        if not query:
            return ToolResult(
                status=ToolStatus.FAILED,
                error="query is required"
            )
        
        result = self.platform.search_entities(query, filters or {})
        
        if result.get("error"):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=result["error"]
            )
        
        entities = result.get("entities", [])
        total = result.get("total", 0)
        
        if not entities:
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"No entities found matching '{query}'"
            )
        
        output = f"🔍 Search Results for '{query}' ({total} total):\n"
        for entity in entities[:10]:
            entity_id = entity.get("entity_id", "Unknown")
            entity_type = entity.get("entity_type", "unknown")
            risk_score = entity.get("risk_score", 0)
            risk_level = entity.get("risk_level", "UNKNOWN")
            
            emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }.get(risk_level, "⚪")
            
            output += f"\n{emoji} {entity_id} ({entity_type}): {risk_score}/100"
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            message=output,
            data=result
        )


class PlatformProposeActionsTool(BaseTool):
    """Get recommended actions for a finding."""
    
    def __init__(self):
        super().__init__(
            name="platform_propose_actions",
            description="Get recommended security actions for a risk finding",
            permission_level=PermissionLevel.LOW,
            needs_confirmation=False
        )
        self.platform = get_platform_client()
    
    def execute(self, finding_id: str) -> ToolResult:
        """
        Get action recommendations.
        
        Args:
            finding_id: Finding identifier
            
        Returns:
            ToolResult with action recommendations
        """
        if not finding_id:
            return ToolResult(
                status=ToolStatus.FAILED,
                error="finding_id is required"
            )
        
        result = self.platform.propose_actions(finding_id)
        
        if result.get("error"):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=result["error"]
            )
        
        actions = result.get("actions", [])
        
        if not actions:
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message="No actions recommended for this finding"
            )
        
        output = f"💡 Recommended Actions for {finding_id}:\n"
        for i, action in enumerate(actions, 1):
            action_type = action.get("action_type", "unknown")
            description = action.get("description", "")
            priority = action.get("priority", "UNKNOWN")
            
            emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }.get(priority, "⚪")
            
            output += f"\n{i}. {emoji} {action_type.upper()}"
            output += f"\n   {description}"
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            message=output,
            data=result
        )


class PlatformExecuteActionTool(BaseTool):
    """Execute a security action."""
    
    def __init__(self):
        super().__init__(
            name="platform_execute_action",
            description="Execute a security action (requires confirmation)",
            permission_level=PermissionLevel.HIGH,
            needs_confirmation=True
        )
        self.platform = get_platform_client()
    
    def execute(self, action_id: str, params: Dict[str, Any] = None) -> ToolResult:
        """
        Execute an action.
        
        Args:
            action_id: Action identifier
            params: Optional action parameters
            
        Returns:
            ToolResult with execution result
        """
        if not action_id:
            return ToolResult(
                status=ToolStatus.FAILED,
                error="action_id is required"
            )
        
        result = self.platform.execute_action(action_id, params or {})
        
        if result.get("error"):
            return ToolResult(
                status=ToolStatus.FAILED,
                error=result["error"]
            )
        
        status = result.get("status", "unknown")
        action_result = result.get("result", "")
        
        output = f"✅ Action Executed: {action_id}\n"
        output += f"Status: {status}\n"
        output += f"Result: {action_result}"
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            message=output,
            data=result
        )


# ========== TOOL REGISTRATION ==========

def register_platform_tools(registry):
    """
    Register all Platform tools with the tool registry.
    
    Args:
        registry: ToolRegistry instance
    """
    tools = [
        PlatformRiskFindingsTool(),
        PlatformFindingDetailsTool(),
        PlatformSearchEntitiesTool(),
        PlatformProposeActionsTool(),
        PlatformExecuteActionTool(),
    ]
    
    for tool in tools:
        registry.register(tool)
    
    print(f"✓ Registered {len(tools)} Platform tools")


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    from tools.registry import get_tool_registry
    
    # Register tools
    registry = get_tool_registry()
    register_platform_tools(registry)
    
    # Test a tool
    print("\nTesting Platform risk findings...")
    result = registry.execute("platform_get_risk_findings", {"filters": {"risk_level": "HIGH"}})
    print(f"Status: {result.status.value}")
    print(f"Message: {result.message}")
