# knowledge/retriever.py
"""
Knowledge Retriever - Retrieves relevant context for LLM prompts.

Combines results from:
- Vector store (semantic search)
- Memory (user preferences, history)
- Mode-specific filtering
"""

from typing import List, Optional
from dataclasses import dataclass

from .vector_store import VectorStore, SearchResult


@dataclass
class RetrievalResult:
    """A retrieval result with context."""
    content: str
    source: str
    source_type: str
    relevance: float
    metadata: dict


class KnowledgeRetriever:
    """
    Retrieves relevant knowledge for LLM context.
    """
    
    # Maximum context length
    MAX_CONTEXT_LENGTH = 4000
    
    # Source type priorities by mode
    MODE_PRIORITIES = {
        "general": ["documentation", "note"],
        "architect": ["design", "documentation", "code"],
        "developer": ["code", "documentation", "design"],
        "research": ["documentation", "web", "note"],
        "security": ["policy", "security", "documentation"],
        "simulation": ["design", "code", "documentation"],
    }
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize the retriever.
        
        Args:
            vector_store: The vector store to retrieve from
        """
        self._store = vector_store
    
    def _format_result(self, result: SearchResult) -> RetrievalResult:
        """Format a search result for output."""
        metadata = result.document.metadata or {}
        
        # Determine source type
        source_type = metadata.get("source_type") or metadata.get("file_type") or "unknown"
        
        # Determine source name
        source = metadata.get("title") or metadata.get("file_name") or result.document.id[:8]
        
        return RetrievalResult(
            content=result.document.content,
            source=source,
            source_type=source_type,
            relevance=result.score,
            metadata=metadata,
        )
    
    def _prioritize_results(
        self,
        results: List[RetrievalResult],
        mode: str,
    ) -> List[RetrievalResult]:
        """Prioritize results based on mode."""
        priorities = self.MODE_PRIORITIES.get(mode, [])
        
        def priority_score(result: RetrievalResult) -> float:
            # Combine relevance with source type priority
            base_score = result.relevance
            
            if result.source_type in priorities:
                type_priority = 1.0 - (priorities.index(result.source_type) * 0.1)
            else:
                type_priority = 0.5
            
            return base_score * type_priority
        
        return sorted(results, key=priority_score, reverse=True)
    
    def retrieve(
        self,
        query: str,
        mode: str = "general",
        k: int = 5,
        source_types: List[str] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant knowledge for a query.
        
        Args:
            query: The search query
            mode: Current cognitive mode (affects prioritization)
            k: Maximum number of results
            source_types: Filter by source types
            
        Returns:
            List of RetrievalResults
        """
        # Search the vector store
        search_results = self._store.search(query, k=k * 2)  # Get more for filtering
        
        # Format results
        results = [self._format_result(r) for r in search_results]
        
        # Filter by source type if specified
        if source_types:
            results = [r for r in results if r.source_type in source_types]
        
        # Prioritize by mode
        results = self._prioritize_results(results, mode)
        
        # Return top k
        return results[:k]
    
    def retrieve_context(
        self,
        query: str,
        mode: str = "general",
        max_length: int = None,
    ) -> str:
        """
        Retrieve and format context as a string for LLM injection.
        
        Args:
            query: The search query
            mode: Current cognitive mode
            max_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        max_length = max_length or self.MAX_CONTEXT_LENGTH
        
        results = self.retrieve(query, mode=mode, k=10)
        
        if not results:
            return ""
        
        # Format results into context
        context_parts = []
        total_length = 0
        
        for result in results:
            # Format this result
            formatted = f"[{result.source_type.upper()}] {result.source}:\n{result.content}\n"
            
            # Check if we have room
            if total_length + len(formatted) > max_length:
                # Truncate if needed
                remaining = max_length - total_length - 50  # Buffer for ellipsis
                if remaining > 100:
                    formatted = formatted[:remaining] + "...\n"
                    context_parts.append(formatted)
                break
            
            context_parts.append(formatted)
            total_length += len(formatted)
        
        return "\n".join(context_parts)
    
    def get_similar_designs(self, query: str, k: int = 3) -> List[RetrievalResult]:
        """Retrieve similar design documents."""
        return self.retrieve(query, mode="architect", k=k, source_types=["design"])
    
    def get_relevant_code(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Retrieve relevant code snippets."""
        return self.retrieve(query, mode="developer", k=k, source_types=["code"])
    
    def get_relevant_policies(self, query: str, k: int = 3) -> List[RetrievalResult]:
        """Retrieve relevant security policies."""
        return self.retrieve(query, mode="security", k=k, source_types=["policy", "security"])
