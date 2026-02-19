# tools/web/web_search.py
"""
Web Search Tool - Performs web searches using SerpAPI or similar.

Enhanced from the original web_search action with source extraction.
"""

import os
import requests
from typing import Optional, List
from urllib.parse import urlparse

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel


class WebSearchTool(BaseTool):
    """Tool to perform web searches."""
    
    def __init__(self, api_key: str = None):
        super().__init__()
        self._name = "web_search"
        self._description = "Search the web for information"
        self._permission_level = PermissionLevel.READ
        self._needs_confirmation = False
        self._api_key = api_key or os.getenv("SERPAPI_KEY")
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        }
    
    def _search_serpapi(self, query: str, num_results: int) -> dict:
        """Search using SerpAPI."""
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self._api_key,
            "num": num_results,
            "engine": "google",
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        
        # Extract organic results
        for item in data.get("organic_results", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": urlparse(item.get("link", "")).netloc,
            })
        
        # Extract answer box if available
        answer_box = None
        if "answer_box" in data:
            ab = data["answer_box"]
            answer_box = {
                "answer": ab.get("answer") or ab.get("snippet") or ab.get("snippet_highlighted_words", [""])[0],
                "source": ab.get("link", ""),
            }
        
        return {
            "results": results,
            "answer_box": answer_box,
        }
    
    def _search_duckduckgo(self, query: str, num_results: int) -> dict:
        """Fallback search using DuckDuckGo Instant Answer API."""
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        
        # Extract related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "title": topic.get("Text", "")[:100],
                    "url": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                    "source": urlparse(topic.get("FirstURL", "")).netloc,
                })
        
        # Extract abstract if available
        answer_box = None
        if data.get("Abstract"):
            answer_box = {
                "answer": data["Abstract"],
                "source": data.get("AbstractURL", ""),
            }
        
        return {
            "results": results,
            "answer_box": answer_box,
        }
    
    def _execute(
        self,
        query: str,
        num_results: int = 5,
        **kwargs,
    ) -> ToolResult:
        """Perform the web search."""
        if not query or not query.strip():
            return ToolResult(
                status=ToolStatus.FAILED,
                error="Search query is required",
            )
        
        num_results = min(num_results, 10)  # Limit results
        
        try:
            # Try SerpAPI if key is available
            if self._api_key:
                try:
                    search_data = self._search_serpapi(query, num_results)
                except Exception as e:
                    # Fall back to DuckDuckGo
                    search_data = self._search_duckduckgo(query, num_results)
            else:
                # Use DuckDuckGo if no API key
                search_data = self._search_duckduckgo(query, num_results)
            
            results = search_data.get("results", [])
            answer_box = search_data.get("answer_box")
            
            # Format a summary
            summary_parts = []
            
            if answer_box and answer_box.get("answer"):
                summary_parts.append(f"Direct answer: {answer_box['answer']}")
            
            for i, result in enumerate(results, 1):
                summary_parts.append(
                    f"{i}. {result['title']}\n   {result['snippet'][:150]}...\n   Source: {result['source']}"
                )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Found {len(results)} results for '{query}'",
                data={
                    "query": query,
                    "results": results,
                    "answer_box": answer_box,
                    "summary": "\n\n".join(summary_parts),
                    "sources": [r["url"] for r in results],
                },
            )
            
        except requests.exceptions.Timeout:
            return ToolResult(
                status=ToolStatus.FAILED,
                error="Search request timed out",
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Search failed: {e}",
            )
