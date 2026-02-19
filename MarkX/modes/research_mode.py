# modes/research_mode.py
"""
Research Mode - Technology and Tool Evaluation.

Purpose: Objective comparison of tools, long-term viability analysis.
Behavior Focus:
- Objective comparison of tools
- Long-term viability and ecosystem strength
- Hidden risks and lock-in concerns

Output Structure: Options → Strengths → Weaknesses → Risks → Verdict
"""

from .base_mode import BaseMode, ModeContext, SubMode


class ResearchMode(BaseMode):
    """Technology research and comparison mode."""
    
    def __init__(self):
        super().__init__()
        self._name = "research"
        self._description = "Technology & tool evaluation"
        self._icon = "🔍"
        self._allowed_tools = [
            "web_search",
            "fetch_docs",
            "summarize",
            "project_docs",
            "design_history",
        ]
        self._output_format = {
            "options": True,
            "strengths": True,
            "weaknesses": True,
            "risks": True,
            "verdict": True,
        }
        
        # Sub-modes
        self._sub_modes = {
            "cto_strategy": SubMode(
                name="CTO Strategy",
                description="Evaluates technology through business survival lens",
                trigger_phrases=["strategic", "long term", "company direction", "hiring", "team skills"],
                prompt_injection="""
You are now in CTO Strategy sub-mode within Research mode.
Evaluate technology choices through the lens of business survival and growth.
Consider:
- Team hiring and skill availability in market
- Vendor lock-in and exit strategies
- Total cost of ownership (not just licensing)
- Community health and long-term viability
- Integration with existing investments
- Competitive advantage vs commodity
""",
                output_structure="Options → Tech Debt Risk → Business Impact → Decision"
            ),
        }
    
    def get_mode_prompt(self) -> str:
        return """
## Current Mode: 🔍 RESEARCH MODE

### Purpose
Technology and tool evaluation. You provide objective, well-sourced comparisons with a focus on long-term viability and hidden risks.

### Behavior Focus
- OBJECTIVE comparison—no favoritism
- Long-term viability and ecosystem strength
- Hidden risks and vendor lock-in concerns
- Community health and maintenance trajectory

### Key Principles
1. ALWAYS use web search for current information
2. CITE sources for all factual claims
3. Provide BALANCED comparisons:
   - Pros and cons for each option
   - Use cases where each excels
   - Community and ecosystem factors
4. FLAG uncertainty:
   - Distinguish between facts and opinions
   - Note when information may be outdated
   - Indicate confidence level
5. CONSIDER hidden costs:
   - Lock-in risks
   - Migration complexity
   - Skill availability

### Output Structure
For research responses, structure as:
**Options → Strengths → Weaknesses → Risks → Verdict**

### Response Format
{
    "intent": "research",
    "parameters": {
        "topic": "<research topic>",
        "research_type": "<comparison|evaluation|trend|howto>"
    },
    "text": "<conversational summary>",
    "research": {
        "options": ["<option1>", "<option2>"],
        "analysis": [
            {
                "option": "<name>",
                "strengths": ["<strength1>", "<strength2>"],
                "weaknesses": ["<weakness1>", "<weakness2>"],
                "risks": ["<risk1>", "<risk2>"],
                "best_for": "<use case>"
            }
        ],
        "verdict": "<final recommendation with reasoning>",
        "confidence": "<high|medium|low>",
        "sources": ["<url1>", "<url2>"]
    },
    "needs_clarification": false,
    "memory_update": null
}
"""

    def build_prompt(self, context: ModeContext) -> str:
        prompt_parts = []
        
        # Add any prior research context
        if context.rag_context:
            prompt_parts.append(f"Previous research on related topics:\n{context.rag_context}")
        
        # Add memory context
        if context.memory_context:
            memory_str = "\n".join(f"{k}: {v}" for k, v in context.memory_context.items())
            prompt_parts.append(f"User preferences and context:\n{memory_str}")
        
        # Add conversation history
        if context.conversation_history:
            history = "\n".join(
                f"{msg['role'].title()}: {msg['text']}" 
                for msg in context.conversation_history[-6:]
            )
            prompt_parts.append(f"Research discussion:\n{history}")
        
        # Add available tools
        prompt_parts.append(self.format_tool_availability(context.available_tools))
        
        # Add user message
        prompt_parts.append(f"Research request: \"{context.user_message}\"")
        
        return "\n\n".join(prompt_parts)
    
    def get_mode_instructions(self) -> str:
        return """
In Research Mode:
- Prioritize accuracy over speed
- Always cite sources
- Be explicit about uncertainty
- Expose hidden risks (lock-in, migration costs)
- Provide actionable verdicts, not wishy-washy conclusions
"""

    def validate_output(self, output: dict) -> bool:
        """Validate research mode specific output."""
        base_valid = super().validate_output(output)
        
        # For research, should have findings with sources
        if output.get("intent") == "research":
            has_research = "research" in output
            return base_valid and has_research
        
        return base_valid
