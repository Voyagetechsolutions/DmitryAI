# modes/developer_mode.py
"""
Developer Mode - Implementation and Coding Support.

Purpose: Practical step-by-step guidance with secure defaults.
Behavior Focus:
- Secure defaults in implementation
- Warns about dev pitfalls
- Production-ready code

Output Structure: Steps → Code Pattern → Security Note → Optimization Tip
"""

from .base_mode import BaseMode, ModeContext, SubMode


class DeveloperMode(BaseMode):
    """Implementation and coding support mode."""
    
    def __init__(self):
        super().__init__()
        self._name = "developer"
        self._description = "Implementation & coding support"
        self._icon = "💻"
        self._allowed_tools = [
            "file_read",
            "file_write",
            "codebase_search",
            "python_executor",
            "node_executor",
            "test_runner",
            "web_search",
            "fetch_docs",
        ]
        self._output_format = {
            "code_block": True,
            "tests": True,
            "security_notes": True,
            "optimization_tips": True,
        }
        
        # Sub-modes
        self._sub_modes = {
            "build_execution": SubMode(
                name="Build Execution",
                description="Production-ready implementation guidance",
                trigger_phrases=["build this", "implement", "create the", "write the code", "production ready"],
                prompt_injection="""
You are now in Build Execution sub-mode.
Deliver production-ready code, not prototypes.
Focus on:
- Complete error handling
- Input validation
- Logging and observability
- Configuration management
- Dependency injection where appropriate
- Unit and integration test scaffolding
""",
                output_structure="Implementation Steps → Secure Pattern → Common Mistakes → Optimization"
            ),
            "security_review": SubMode(
                name="Security Review",
                description="Deep code & architecture vulnerability hunting",
                trigger_phrases=["review this code", "is this secure", "vulnerability", "security review", "audit this"],
                prompt_injection="""
You are now in Security Review sub-mode within Developer mode.
Hunt for vulnerabilities with a penetration tester's mindset.
Focus on:
- Injection vulnerabilities (SQL, command, XSS)
- Authentication and authorization flaws
- Secrets and credential exposure
- Insecure deserialization
- Dependency vulnerabilities
- OWASP Top 10 mapping
""",
                output_structure="Vulnerability → Exploit Path → Severity → Fix"
            ),
        }
    
    def get_mode_prompt(self) -> str:
        return """
## Current Mode: 💻 DEVELOPER MODE

### Purpose
Implementation and coding support. You write production-quality code with security as a default, not an afterthought.

### Behavior Focus
- Practical step-by-step guidance
- Secure defaults in EVERY implementation
- Proactively warn about common dev pitfalls
- Test-driven thinking

### Key Principles
1. DECOMPOSE problems into clear steps before coding
2. Write PRODUCTION-QUALITY code:
   - Clear variable names
   - Proper error handling
   - Type hints (Python) / Types (TypeScript)
   - Docstrings and comments where needed
3. ALWAYS include:
   - Time/space complexity analysis (Big O)
   - Edge case handling
   - Unit test examples
4. SECURITY by default:
   - Validate all inputs
   - Sanitize outputs
   - Use parameterized queries
   - Never hardcode secrets

### Output Structure
For code responses, structure as:
**Steps → Code Pattern → Security Note → Optimization Tip**

### Response Format
{
    "intent": "code_task",
    "parameters": {
        "task_type": "<write|debug|refactor|optimize|explain>",
        "language": "<python|javascript|typescript|etc>"
    },
    "text": "<explanation of approach with security considerations>",
    "code": {
        "main": "<the main code>",
        "tests": "<test code>",
        "complexity": {
            "time": "<O notation>",
            "space": "<O notation>",
            "explanation": "<why>"
        }
    },
    "security_notes": ["<security consideration 1>", "<security consideration 2>"],
    "needs_clarification": false,
    "memory_update": null
}
"""

    def build_prompt(self, context: ModeContext) -> str:
        prompt_parts = []
        
        # Add RAG context (codebase info)
        if context.rag_context:
            prompt_parts.append(f"Relevant codebase context:\n{context.rag_context}")
        
        # Add memory context
        if context.memory_context:
            memory_str = "\n".join(f"{k}: {v}" for k, v in context.memory_context.items())
            prompt_parts.append(f"Project context:\n{memory_str}")
        
        # Add conversation history
        if context.conversation_history:
            history = "\n".join(
                f"{msg['role'].title()}: {msg['text']}" 
                for msg in context.conversation_history[-8:]
            )
            prompt_parts.append(f"Coding session so far:\n{history}")
        
        # Add available tools
        prompt_parts.append(self.format_tool_availability(context.available_tools))
        
        # Add user message
        prompt_parts.append(f"User request: \"{context.user_message}\"")
        
        return "\n\n".join(prompt_parts)
    
    def get_mode_instructions(self) -> str:
        return """
In Developer Mode:
- Think step-by-step about the problem
- Write clean, tested, documented, SECURE code
- Explain complexity and tradeoffs
- Verify code works via execution when possible
- Suggest improvements proactively
- Always mention security implications
"""

    def validate_output(self, output: dict) -> bool:
        """Validate developer mode specific output."""
        base_valid = super().validate_output(output)
        
        # For code tasks, code block should be present
        if output.get("intent") == "code_task":
            has_code = "code" in output and output["code"].get("main")
            return base_valid and has_code
        
        return base_valid
