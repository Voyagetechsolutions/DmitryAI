# modes/design_mode.py
"""
Design Mode - System Architecture and Structure.

Purpose: Components, boundaries, data flow, scalability, maintainability.
Behavior Focus:
- Avoids messy quick solutions
- Production-grade architecture with failure tolerance

Output Structure: System Components → Data Flow → Failure Points → Best-Practice Design
"""

from .base_mode import BaseMode, ModeContext, SubMode


class DesignMode(BaseMode):
    """System and product design specialist mode."""
    
    def __init__(self):
        super().__init__()
        self._name = "design"
        self._description = "System architecture & structure"
        self._icon = "🏗"
        self._allowed_tools = [
            "design_history",
            "project_docs",
            "codebase_search",
            "web_search",
            "fetch_docs",
            "file_read",
            "file_write",
        ]
        self._output_format = {
            "sections": [
                "system_components",
                "data_flow", 
                "failure_points",
                "best_practice_design",
            ]
        }
        
        # Sub-modes
        self._sub_modes = {
            "architecture_deep_dive": SubMode(
                name="Architecture Deep Dive",
                description="Production-grade architecture with failure tolerance",
                trigger_phrases=["deep dive", "production ready", "fault tolerant", "high availability", "disaster recovery"],
                prompt_injection="""
You are now in Architecture Deep Dive sub-mode.
Design systems that are production-ready from day one.
Focus on:
- Horizontal and vertical scaling strategies
- Failure modes and recovery procedures
- Observability: logging, metrics, tracing
- Data consistency and partition tolerance
- Deployment strategies (blue/green, canary, rolling)
- Cost optimization at scale
""",
                output_structure="Components → Scaling Plan → Failure Handling → Observability"
            ),
        }
    
    def get_mode_prompt(self) -> str:
        return """
## Current Mode: 🏗 DESIGN MODE

### Purpose
System architecture and structure. You design systems that are scalable, maintainable, and secure by default.

### Behavior Focus
- Components, boundaries, and data flow
- Scalability and maintainability first
- NEVER suggest messy quick solutions—always production-quality designs
- Consider failure modes upfront

### Key Questions to Ask
Before designing, clarify:
- Scale (users, requests/sec, data volume)
- Latency requirements
- Budget constraints
- Team size and expertise
- Existing infrastructure

### Output Structure
For design responses, structure as:
**System Components → Data Flow → Failure Points → Best-Practice Design**

### Response Format
{
    "intent": "architecture_design",
    "parameters": {
        "design_type": "<api|database|system|component>",
        "name": "<design name>"
    },
    "text": "<conversational explanation>",
    "structured_output": {
        "summary": "<brief summary>",
        "diagram": "<mermaid diagram code>",
        "components": [{"name": "", "responsibility": "", "interfaces": []}],
        "data_flow": "<description of how data moves through the system>",
        "failure_points": [{"point": "", "mitigation": ""}],
        "tradeoffs": [{"option": "", "pros": [], "cons": []}],
        "recommendations": []
    },
    "needs_clarification": false,
    "clarification_questions": [],
    "memory_update": null
}

If you need more information, set needs_clarification to true.
"""

    def build_prompt(self, context: ModeContext) -> str:
        prompt_parts = []
        
        # Add RAG context (past designs, project docs)
        if context.rag_context:
            prompt_parts.append(f"Relevant context from knowledge base:\n{context.rag_context}")
        
        # Add memory context
        if context.memory_context:
            memory_str = "\n".join(f"{k}: {v}" for k, v in context.memory_context.items())
            prompt_parts.append(f"User context:\n{memory_str}")
        
        # Add conversation history
        if context.conversation_history:
            history = "\n".join(
                f"{msg['role'].title()}: {msg['text']}" 
                for msg in context.conversation_history[-10:]
            )
            prompt_parts.append(f"Design discussion so far:\n{history}")
        
        # Add available tools
        prompt_parts.append(self.format_tool_availability(context.available_tools))
        
        # Add user message
        prompt_parts.append(f"User request: \"{context.user_message}\"")
        
        return "\n\n".join(prompt_parts)
    
    def get_mode_instructions(self) -> str:
        return """
In Design Mode:
- Think systematically about components and their interactions
- Always consider scale, reliability, and maintainability
- Use diagrams (Mermaid) to communicate complex ideas
- Reference past designs when relevant
- Be explicit about tradeoffs
- Design for failure—not just success
"""

    def validate_output(self, output: dict) -> bool:
        """Validate design mode specific output."""
        base_valid = super().validate_output(output)
        
        # For design outputs, structured_output should be present
        if output.get("intent") == "architecture_design":
            return base_valid and "structured_output" in output
        
        return base_valid
