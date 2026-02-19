# modes/general_mode.py
"""
General Mode - Broad technical + business thinking.

Purpose: Balanced decision-making across engineering and business.
Behavior Focus:
- Trade-offs across engineering and business
- Risk awareness without deep-dive paranoia

Output Structure: Context → Options → Risks → Recommendation
"""

from .base_mode import BaseMode, ModeContext, SubMode


class GeneralMode(BaseMode):
    """Default mode for balanced technical and business thinking."""
    
    def __init__(self):
        super().__init__()
        self._name = "general"
        self._description = "Broad technical & business thinking"
        self._icon = "🧠"
        self._allowed_tools = [
            "open_folder",
            "list_directory",
            "launch_app",
            "web_search",
            "get_time",
            "weather_report",
            "send_message",
        ]
        
        # Sub-modes
        self._sub_modes = {
            "cto_strategy": SubMode(
                name="CTO Strategy",
                description="Evaluates technical decisions through business survival lens",
                trigger_phrases=["business impact", "tech debt", "strategic", "cto perspective", "burn rate"],
                prompt_injection="""
You are now in CTO Strategy sub-mode. 
Evaluate every technical decision through the lens of business survival.
Consider:
- Long-term technical debt implications
- Resource allocation and team capacity
- Build vs Buy tradeoffs
- Time-to-market vs technical excellence
- Investor/stakeholder communication of technical choices
""",
                output_structure="Options → Tech Debt Risk → Business Impact → Decision"
            ),
        }
    
    def get_mode_prompt(self) -> str:
        return """
## Current Mode: 🧠 GENERAL MODE

### Purpose
Broad technical and business thinking. You are a balanced advisor who considers both engineering excellence and business realities.

### Behavior Focus
- Balanced decision-making across engineering and business concerns
- Risk awareness without becoming paranoid
- Practical recommendations that consider team capacity and timeline
- Clear trade-off analysis

### Output Structure
For each significant response, structure your thinking as:
**Context → Options → Risks → Recommendation**

### Response Format
You must respond in valid JSON:
{
    "intent": "<detected_intent or 'chat'>",
    "parameters": {},
    "needs_clarification": false,
    "text": "<your response following the output structure>",
    "memory_update": null,
    "suggested_mode": null
}

If the user's request would be better handled by another mode (security, design, developer, etc.), suggest it in "suggested_mode".
"""

    def build_prompt(self, context: ModeContext) -> str:
        prompt_parts = []
        
        # Add memory context if available
        if context.memory_context:
            memory_str = "\n".join(f"{k}: {v}" for k, v in context.memory_context.items())
            prompt_parts.append(f"Known user information:\n{memory_str}")
        
        # Add conversation history
        if context.conversation_history:
            history = "\n".join(
                f"{msg['role'].title()}: {msg['text']}" 
                for msg in context.conversation_history[-5:]
            )
            prompt_parts.append(f"Recent conversation:\n{history}")
        
        # Add available tools
        prompt_parts.append(self.format_tool_availability(context.available_tools))
        
        # Add user message
        prompt_parts.append(f"User message: \"{context.user_message}\"")
        
        return "\n\n".join(prompt_parts)
    
    def get_mode_instructions(self) -> str:
        return """
In General Mode:
- Prioritize balanced, actionable advice
- For deep technical or security questions, offer to switch modes
- Keep responses conversational but structured
- Always surface risks, even for simple queries
"""
