# tools/web/__init__.py
"""
Web Research Tools

Tools for web search, documentation fetching, and content summarization.
"""

from .web_search import WebSearchTool
from .fetch_docs import FetchDocsTool

__all__ = [
    "WebSearchTool",
    "FetchDocsTool",
]
