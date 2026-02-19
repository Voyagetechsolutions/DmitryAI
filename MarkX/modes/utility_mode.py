# modes/utility_mode.py
"""
Utility Mode - Everyday Simple Tasks.

Purpose: Handle simple, non-technical, everyday assistance tasks.
Behavior Focus:
- Natural, human-friendly language
- Short and clear responses
- No overanalyzing or risk lectures

Output Structure: User Intent → Clean Response → Optional Tone Adjustment
"""

from .base_mode import BaseMode, ModeContext, SubMode


class UtilityMode(BaseMode):
    """Low-intensity mode for everyday simple tasks."""
    
    def __init__(self):
        super().__init__()
        self._name = "utility"
        self._description = "Everyday simple tasks"
        self._icon = "🗂️"
        self._allowed_tools = [
            "web_search",
            "get_time",
            "weather_report",
            "send_message",
        ]
        self._output_format = {
            "clean_response": True,
            "tone_options": False,
        }
        
        # No sub-modes - this is the simple layer
        self._sub_modes = {}
    
    def get_mode_prompt(self) -> str:
        return """
## Current Mode: 🗂️ UTILITY MODE

### Purpose
Handle simple, non-technical, everyday assistance tasks. You are Dmitry in casual mode—efficient, helpful, human.

### This Mode is For
- Replying to messages
- Writing captions
- Drafting short posts
- Polishing text
- Rewording things
- Basic communication help
- Quick answers to simple questions

### Behavioral Rules
1. DROP the heavy technical tone
2. STOP defaulting to risk analysis
3. Use NATURAL, human-friendly language
4. Keep responses SHORT and CLEAR
5. Match the user's energy and tone

### What to AVOID
- Overanalyzing simple requests
- Bringing up security unless directly relevant
- Turning everything into strategy talk
- Long-winded explanations
- Technical jargon

### Response Style
**User Intent → Clean, natural response → Optional tone adjustment**

Examples:
- "Reply to this message politely" → Direct rewritten reply, no lecture
- "Caption for this post" → Short, natural caption options
- "Reword this" → Clean rewrite, done

### Response Format
{
    "intent": "utility",
    "parameters": {
        "task_type": "<reply|caption|rewrite|draft|polish>"
    },
    "text": "<your clean, natural response>",
    "alternatives": ["<optional alternative if relevant>"],
    "needs_clarification": false,
    "memory_update": null
}

Be helpful. Be efficient. Be human.
"""

    def build_prompt(self, context: ModeContext) -> str:
        prompt_parts = []
        
        # Add memory context if available (keep it light)
        if context.memory_context:
            if "user_name" in context.memory_context:
                prompt_parts.append(f"User: {context.memory_context['user_name']}")
        
        # Add conversation history (shorter for utility mode)
        if context.conversation_history:
            history = "\n".join(
                f"{msg['role'].title()}: {msg['text']}" 
                for msg in context.conversation_history[-3:]
            )
            prompt_parts.append(f"Recent:\n{history}")
        
        # Add user message
        prompt_parts.append(f"Request: \"{context.user_message}\"")
        
        return "\n\n".join(prompt_parts)
    
    def get_mode_instructions(self) -> str:
        return """
In Utility Mode:
- Be quick and helpful
- No technical lectures
- Match the user's tone
- Just get the task done
"""

    def validate_output(self, output: dict) -> bool:
        """Validate utility mode output - keep it simple."""
        return "text" in output
