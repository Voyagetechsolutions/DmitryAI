# llm.py - Dmitry v1.2
"""
LLM Integration with Mode-aware prompts and RAG context.
Includes prompt injection detection and security features.
"""

import os
import json
import requests
import time
import random
from typing import Optional
from dotenv import load_dotenv

# Import new core systems
from core.resilience import ResilientLLM, retry_with_backoff, RetryConfig
from core.cache import llm_cache
from core.context_awareness import context_manager

# Import prompt injection detector
try:
    from modes.security_mode.ai_security.prompt_injection_detector import prompt_injection_detector
    PROMPT_INJECTION_DETECTION_AVAILABLE = True
except ImportError:
    PROMPT_INJECTION_DETECTION_AVAILABLE = False
    print("⚠ Prompt injection detection not available")

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Default model - can be configured
MODEL = os.getenv("DMITRY_MODEL", "arcee-ai/trinity-large-preview:free")


def safe_json_parse(text: str) -> dict | None:
    """Parse JSON from LLM response, handling various formats."""
    if not text:
        return None

    text = text.strip()

    # Handle markdown code blocks
    if "```json" in text:
        try:
            start = text.index("```json") + 7
            end = text.index("```", start)
            text = text[start:end].strip()
        except:
            pass
    elif "```" in text:
        try:
            start = text.index("```") + 3
            end = text.index("```", start)
            text = text[start:end].strip()
        except:
            pass

    # Extract JSON object
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"The error text: {text[:200]}")
        return None


class DmitryLLM:
    """
    LLM integration for Dmitry with mode support.
    """
    
    def __init__(self, mode_manager=None, knowledge_retriever=None):
        """
        Initialize LLM integration.
        
        Args:
            mode_manager: Optional ModeManager instance
            knowledge_retriever: Optional KnowledgeRetriever for RAG
        """
        self._mode_manager = mode_manager
        self._retriever = knowledge_retriever
    
    def set_mode_manager(self, mode_manager):
        """Set the mode manager."""
        self._mode_manager = mode_manager
    
    def set_retriever(self, retriever):
        """Set the knowledge retriever."""
        self._retriever = retriever
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt from the current mode."""
        if self._mode_manager:
            return self._mode_manager.get_system_prompt()
        
        # Fallback default prompt
        return """You are Dmitry, a helpful AI assistant.
Respond in valid JSON with this format:
{
    "intent": "<detected_intent or 'chat'>",
    "parameters": {},
    "needs_clarification": false,
    "text": "<your response>",
    "memory_update": null,
    "suggested_mode": null
}
"""
    
    def _build_user_prompt(
        self,
        user_text: str,
        memory_context: dict,
        rag_context: str,
        conversation_history: list,
    ) -> str:
        """Build the user prompt with context."""
        if self._mode_manager:
            from modes import ModeContext
            
            context = ModeContext(
                user_message=user_text,
                memory_context=memory_context,
                rag_context=rag_context,
                conversation_history=conversation_history,
                available_tools=self._mode_manager.current_mode.allowed_tools,
            )
            
            return self._mode_manager.build_user_prompt(context)
        
        # Fallback: simple prompt construction
        parts = []
        
        if memory_context:
            memory_str = "\n".join(f"{k}: {v}" for k, v in memory_context.items())
            parts.append(f"Known user information:\n{memory_str}")
        
        if rag_context:
            parts.append(f"Relevant context:\n{rag_context}")
        
        parts.append(f"User message: \"{user_text}\"")
        
        return "\n\n".join(parts)
    
    def _retrieve_context(self, user_text: str) -> str:
        """Retrieve RAG context if available."""
        if self._retriever and self._mode_manager:
            try:
                return self._retriever.retrieve_context(
                    user_text,
                    mode=self._mode_manager.current_mode_name,
                )
            except Exception as e:
                print(f"⚠️ RAG retrieval error: {e}")
        return ""
    
    def get_response(
        self,
        user_text: str,
        memory_context: dict = None,
        conversation_history: list = None,
        image_data: str = None,  # Base64 image
    ) -> dict:
        """
        Get LLM response for user input, optionally with vision.
        Now with caching, context awareness, resilience, and prompt injection detection.
        """
        if not user_text and not image_data:
             return {
                "intent": "chat",
                "text": "Sir, I didn't catch that.", 
                "needs_clarification": False
            }

        # SECURITY: Check for prompt injection attacks
        if PROMPT_INJECTION_DETECTION_AVAILABLE and user_text:
            detection = prompt_injection_detector.detect(user_text)
            if detection.is_malicious and detection.risk_score > 70:
                print(f"🛡️ Prompt injection detected! Risk: {detection.risk_score}/100")
                return {
                    "intent": "security_alert",
                    "text": f"⚠️ Security Alert: Potential prompt injection detected. {detection.explanation}",
                    "security_alert": True,
                    "detection": {
                        "risk_score": detection.risk_score,
                        "injection_type": detection.injection_type.value,
                        "matched_patterns": detection.matched_patterns,
                        "recommended_action": detection.recommended_action,
                    },
                    "needs_clarification": False
                }
            elif detection.is_malicious and detection.risk_score > 30:
                print(f"⚠️ Suspicious input detected. Risk: {detection.risk_score}/100")
                # Log but allow with warning

        # Check cache first (skip for image requests)
        if not image_data:
            cache_context = {
                "memory": memory_context,
                "mode": self._mode_manager.current_mode_name if self._mode_manager else "general"
            }
            cached_response = llm_cache.get(user_text, cache_context)
            if cached_response:
                print("📋 Using cached response")
                return cached_response

        if not OPENROUTER_API_KEY:
            print("❌ OPENROUTER_API_KEY not found!")
            return {
                "intent": "chat", 
                "text": "API key is missing, Sir.",
                "needs_clarification": False
            }

        # Get system context
        system_context = context_manager.get_current_context()
        context_info = context_manager.format_context_for_llm(system_context)

        # Get RAG context (text only)
        rag_context = self._retrieve_context(user_text) if user_text else ""
        
        # Build prompts with context
        system_prompt = self._get_system_prompt()
        if image_data:
            system_prompt += "\n\nVISION MODE: You are analyzing a screenshot. Describe what you see and answer the user's question about it."
        
        # Add context to system prompt
        if context_info:
            system_prompt += f"\n\nCURRENT CONTEXT:\n{context_info}"
            
        user_prompt = self._build_user_prompt(
            user_text or "Describe this image",
            memory_context or {},
            rag_context,
            conversation_history or [],
        )

        # Construct message payload (Multimodal)
        user_content = [{"type": "text", "text": user_prompt}]
        
        if image_data:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_data}"
                }
            })

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "max_tokens": 1000,
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Dmitry-Assistant",
        }

        # Use resilient request with retry
        @retry_with_backoff(RetryConfig(max_attempts=3, base_delay=2.0))
        def make_request():
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=45,
            )
            
            if response.status_code == 429:
                raise Exception("Rate limited")
            elif response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
            
            return response

        try:
            response = make_request()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON response
            parsed = safe_json_parse(content)

            if parsed:
                result = {
                    "intent": parsed.get("intent", "chat"),
                    "parameters": parsed.get("parameters", {}),
                    "needs_clarification": parsed.get("needs_clarification", False),
                    "text": parsed.get("text"),
                    "memory_update": parsed.get("memory_update"),
                    "suggested_mode": parsed.get("suggested_mode"),
                    "structured_output": parsed.get("structured_output"),
                    "code": parsed.get("code"),
                    "security": parsed.get("security"),
                    "research": parsed.get("research"),
                    "simulation": parsed.get("simulation"),
                }
            else:
                # Fallback: return raw content
                result = {
                    "intent": "chat",
                    "parameters": {},
                    "needs_clarification": False,
                    "text": content,
                    "memory_update": None,
                }

            # Cache successful responses (non-image)
            if not image_data and result.get("text"):
                llm_cache.set(user_text, result, cache_context)

            return result

        except requests.exceptions.Timeout:
            print("❌ API timeout!")
            return {
                "intent": "chat",
                "text": "Sir, the connection timed out.",
                "parameters": {},
                "needs_clarification": False,
                "memory_update": None,
            }
        
        except Exception as e:
            print(f"❌ LLM ERROR: {e}")
            return {
                "intent": "chat",
                "text": "Sir, I encountered a system error.",
                "parameters": {},
                "needs_clarification": False,
                "memory_update": None,
            }


# Legacy function for backward compatibility
def get_llm_output(user_text: str, memory_block: dict = None) -> dict:
    """
    Legacy function - creates a simple DmitryLLM instance.
    Use DmitryLLM class directly for full features.
    """
    llm = DmitryLLM()
    return llm.get_response(user_text, memory_context=memory_block)