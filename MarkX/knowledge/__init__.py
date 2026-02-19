# knowledge/__init__.py
"""
Dmitry v1.2 Knowledge Architecture

RAG-based knowledge retrieval system.
Dmitry does NOT rely on memory alone - knowledge is retrieval-based.

Sources:
1. Base model knowledge
2. RAG over:
   - User docs
   - System designs
   - Codebase
   - Security playbooks
3. Live web research
"""

from .vector_store import VectorStore
from .retriever import KnowledgeRetriever
from .ingestion import DocumentIngester

__all__ = [
    "VectorStore",
    "KnowledgeRetriever",
    "DocumentIngester",
]
