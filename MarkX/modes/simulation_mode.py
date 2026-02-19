# modes/simulation_mode.py
"""
Simulation Mode - Predictive Consequence Modeling.

Purpose: "What happens if" thinking. Chain reactions and cascading failures.
Behavior Focus:
- Future scaling or breach outcomes
- Never executes—only analyzes

Output Structure: Scenario → Chain Reaction → Impact → Preventive Action
"""

from .base_mode import BaseMode, ModeContext, SubMode


class SimulationMode(BaseMode):
    """Predictive consequence modeling mode."""
    
    def __init__(self):
        super().__init__()
        self._name = "simulation"
        self._description = "Predictive consequence modeling"
        self._icon = "🎯"
        self._allowed_tools = [
            # Read-only tools only
            "file_read",
            "codebase_search",
            "design_history",
            "project_docs",
            "policy_lookup",
            # NO execution or write tools
        ]
        self._output_format = {
            "scenario": True,
            "chain_reaction": True,
            "impact": True,
            "preventive_action": True,
        }
        
        # Sub-modes
        self._sub_modes = {
            "incident_response": SubMode(
                name="Incident Response",
                description="Simulate breach scenarios and response plans",
                trigger_phrases=["if we get hacked", "breach scenario", "attack simulation", "tabletop exercise"],
                prompt_injection="""
You are now in Incident Response sub-mode within Simulation mode.
Model breach scenarios and their cascading effects.
Focus on:
- Attack vectors and initial compromise
- Lateral movement possibilities
- Data exfiltration paths
- Detection gaps
- Response time estimates
- Business impact timeline
- Recovery complexity
This is simulation only—for preparation, not a live incident.
""",
                output_structure="Immediate Containment → Damage Scope → Root Cause → Prevention"
            ),
        }
    
    def get_mode_prompt(self) -> str:
        return """
## Current Mode: 🎯 SIMULATION MODE

### Purpose
Predictive consequence modeling. You answer "what happens if" questions by modeling chain reactions and cascading effects.

### Behavior Focus
- Model CHAIN REACTIONS from proposed changes
- Predict CASCADING FAILURES before they happen
- Analyze future scaling and breach outcomes
- NEVER execute anything—only analyze and predict

### Key Principles
1. NEVER execute changes - only analyze and predict
2. Model the BLAST RADIUS of proposed changes:
   - What systems would be affected?
   - What could break?
   - Who would be impacted?
3. Identify RISK FACTORS:
   - Dependencies that could fail
   - Edge cases that might cause issues
   - Rollback complexity
4. Provide CONFIDENCE levels:
   - How certain are the predictions?
   - What assumptions are being made?
5. Suggest SAFE TESTING approaches:
   - Canary/staged rollout strategies
   - Monitoring to watch

### Output Structure
For simulation responses, structure as:
**Scenario → Chain Reaction → Impact → Preventive Action**

### Response Format
{
    "intent": "simulation",
    "parameters": {
        "change_type": "<code|infrastructure|policy|configuration|scaling>",
        "scope": "<description of proposed change>"
    },
    "text": "<conversational summary>",
    "simulation": {
        "scenario": "<clear description of what's being analyzed>",
        "chain_reaction": [
            {
                "step": 1,
                "event": "<what happens>",
                "affected_systems": ["<system1>", "<system2>"],
                "time_to_impact": "<estimate>"
            }
        ],
        "impact": {
            "users_affected": "<none|some|many|all>",
            "data_risk": "<none|possible|likely>",
            "revenue_impact": "<estimate>",
            "reputation_risk": "<low|medium|high>"
        },
        "preventive_actions": [
            {
                "action": "<what to do>",
                "priority": "<p1|p2|p3>",
                "effort": "<low|medium|high>"
            }
        ],
        "confidence": "<high|medium|low>",
        "assumptions": ["<assumption1>", "<assumption2>"]
    },
    "execute": false,
    "needs_clarification": false,
    "memory_update": null
}

IMPORTANT: The "execute" field must ALWAYS be false.
"""

    def build_prompt(self, context: ModeContext) -> str:
        prompt_parts = []
        
        # Add relevant context
        if context.rag_context:
            prompt_parts.append(f"System context for simulation:\n{context.rag_context}")
        
        # Add memory context
        if context.memory_context:
            memory_str = "\n".join(f"{k}: {v}" for k, v in context.memory_context.items())
            prompt_parts.append(f"Environment context:\n{memory_str}")
        
        # Add conversation history
        if context.conversation_history:
            history = "\n".join(
                f"{msg['role'].title()}: {msg['text']}" 
                for msg in context.conversation_history[-6:]
            )
            prompt_parts.append(f"Simulation discussion:\n{history}")
        
        # Add available tools (read-only)
        prompt_parts.append(self.format_tool_availability(context.available_tools))
        prompt_parts.append("⚠️ NOTE: This is simulation mode. No changes will be executed.")
        
        # Add user message
        prompt_parts.append(f"Simulation request: \"{context.user_message}\"")
        
        return "\n\n".join(prompt_parts)
    
    def get_mode_instructions(self) -> str:
        return """
In Simulation Mode:
- Analyze but NEVER execute
- Model chain reactions and cascading failures
- Consider all downstream effects
- Be explicit about uncertainty and assumptions
- Suggest safe validation approaches
- Help make informed decisions without risk
"""

    def validate_output(self, output: dict) -> bool:
        """Validate simulation mode specific output - ensure no execution."""
        base_valid = super().validate_output(output)
        
        # CRITICAL: execute must be false
        if output.get("execute", False):
            return False
        
        # For simulation, should have simulation block
        if output.get("intent") == "simulation":
            has_simulation = "simulation" in output
            return base_valid and has_simulation
        
        return base_valid
