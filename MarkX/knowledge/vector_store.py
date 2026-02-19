# knowledge/vector_store.py
"""
Vector Store - ChromaDB-powered knowledge base.

Production-ready vector store with:
- Persistent storage
- Metadata filtering
- Collection management
- Semantic search
"""

import os
import hashlib
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Try to import ChromaDB, fallback to simple implementation
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not installed. Using fallback vector store.")
    print("   Install with: pip install chromadb")


@dataclass
class Document:
    """A document in the knowledge base."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        return cls(**data)


@dataclass
class SearchResult:
    """A search result with relevance score."""
    document: Document
    score: float
    
    def to_dict(self) -> dict:
        return {
            "document": self.document.to_dict(),
            "score": self.score,
        }


class VectorStore:
    """
    ChromaDB-backed vector store.
    
    Features:
    - Automatic embedding generation
    - Metadata filtering
    - Persistent storage
    - Collection management
    """
    
    DEFAULT_COLLECTION = "dmitry_knowledge"
    
    def __init__(
        self,
        persist_dir: str = "knowledge_base",
        collection_name: str = None,
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_dir: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
        """
        self._persist_dir = os.path.abspath(persist_dir)
        self._collection_name = collection_name or self.DEFAULT_COLLECTION
        
        os.makedirs(self._persist_dir, exist_ok=True)
        
        if CHROMADB_AVAILABLE:
            self._init_chromadb()
        else:
            self._init_fallback()
    
    def _init_chromadb(self) -> None:
        """Initialize ChromaDB client and collection."""
        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        
        print(f"ChromaDB initialized: {self._collection.count()} documents")
    
    def _init_fallback(self) -> None:
        """Initialize fallback in-memory store."""
        self._documents: Dict[str, Document] = {}
        self._word_index: Dict[str, set] = {}
        self._load_fallback()
    
    def _load_fallback(self) -> None:
        """Load fallback store from disk."""
        import json
        db_path = os.path.join(self._persist_dir, "documents.json")
        
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for doc_data in data:
                        doc = Document.from_dict(doc_data)
                        self._documents[doc.id] = doc
                        self._index_document(doc)
            except Exception as e:
                print(f"Warning: Failed to load documents: {e}")
    
    def _save_fallback(self) -> None:
        """Save fallback store to disk."""
        import json
        db_path = os.path.join(self._persist_dir, "documents.json")
        
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump([doc.to_dict() for doc in self._documents.values()], f, indent=2)
    
    def _index_document(self, doc: Document) -> None:
        """Index document for fallback search."""
        import re
        words = set(re.findall(r"\b\w+\b", doc.content.lower()))
        words = {w for w in words if len(w) > 2 and not w.isdigit()}
        
        for word in words:
            if word not in self._word_index:
                self._word_index[word] = set()
            self._word_index[word].add(doc.id)
    
    def _generate_id(self, content: str) -> str:
        """Generate a document ID from content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def add_document(
        self,
        content: str,
        metadata: Dict[str, Any] = None,
        doc_id: str = None,
    ) -> Document:
        """
        Add a document to the store.
        
        Args:
            content: Document content
            metadata: Optional metadata (repo, file_path, type, etc.)
            doc_id: Optional custom document ID
            
        Returns:
            The created Document
        """
        doc_id = doc_id or self._generate_id(content)
        metadata = metadata or {}
        metadata["added_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Ensure metadata values are valid types for ChromaDB
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_metadata[k] = v
            elif v is None:
                continue
            else:
                clean_metadata[k] = str(v)
        
        if CHROMADB_AVAILABLE:
            # Check if document already exists
            existing = self._collection.get(ids=[doc_id])
            if existing["ids"]:
                return Document(id=doc_id, content=content, metadata=clean_metadata)
            
            self._collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[clean_metadata],
            )
        else:
            doc = Document(id=doc_id, content=content, metadata=clean_metadata)
            self._documents[doc_id] = doc
            self._index_document(doc)
            self._save_fallback()
        
        return Document(id=doc_id, content=content, metadata=clean_metadata)
    
    def add_documents(
        self,
        documents: List[tuple[str, Dict[str, Any]]],
    ) -> List[Document]:
        """
        Add multiple documents.
        
        Args:
            documents: List of (content, metadata) tuples
            
        Returns:
            List of created Documents
        """
        results = []
        for content, metadata in documents:
            results.append(self.add_document(content, metadata))
        return results
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        if CHROMADB_AVAILABLE:
            result = self._collection.get(ids=[doc_id])
            if result["ids"]:
                return Document(
                    id=result["ids"][0],
                    content=result["documents"][0],
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                )
            return None
        else:
            return self._documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if CHROMADB_AVAILABLE:
            try:
                self._collection.delete(ids=[doc_id])
                return True
            except Exception:
                return False
        else:
            if doc_id in self._documents:
                del self._documents[doc_id]
                self._save_fallback()
                return True
            return False
    
    def search(
        self,
        query: str,
        k: int = 5,
        where: Dict[str, Any] = None,
    ) -> List[SearchResult]:
        """
        Search for documents matching the query.
        
        Args:
            query: Search query
            k: Number of results to return
            where: Optional metadata filter (ChromaDB where clause)
            
        Returns:
            List of SearchResults sorted by relevance
        """
        if CHROMADB_AVAILABLE:
            return self._search_chromadb(query, k, where)
        else:
            return self._search_fallback(query, k)
    
    def _search_chromadb(
        self,
        query: str,
        k: int,
        where: Dict[str, Any] = None,
    ) -> List[SearchResult]:
        """Search using ChromaDB."""
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=k,
                where=where,
            )
            
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    doc = Document(
                        id=doc_id,
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                    # ChromaDB returns distances, convert to similarity score
                    distance = results["distances"][0][i] if results["distances"] else 0
                    score = 1 / (1 + distance)  # Convert distance to similarity
                    search_results.append(SearchResult(document=doc, score=score))
            
            return search_results
            
        except Exception as e:
            print(f"Warning: ChromaDB search error: {e}")
            return []
    
    def _search_fallback(self, query: str, k: int) -> List[SearchResult]:
        """Fallback TF-IDF-like search."""
        import re
        query_words = set(re.findall(r"\b\w+\b", query.lower()))
        query_words = {w for w in query_words if len(w) > 2}
        
        if not query_words:
            return []
        
        doc_scores: Dict[str, float] = {}
        
        for word in query_words:
            if word in self._word_index:
                matching_docs = self._word_index[word]
                word_weight = 1 / len(matching_docs)
                
                for doc_id in matching_docs:
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = 0
                    doc_scores[doc_id] += word_weight
        
        for doc_id in doc_scores:
            doc_scores[doc_id] /= len(query_words)
        
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in sorted_docs[:k]:
            doc = self._documents[doc_id]
            results.append(SearchResult(document=doc, score=score))
        
        return results
    
    def search_by_metadata(
        self,
        filters: Dict[str, Any],
        k: int = 10,
    ) -> List[Document]:
        """
        Search documents by metadata.
        
        Args:
            filters: Metadata key-value filters
            k: Maximum results
            
        Returns:
            List of matching Documents
        """
        if CHROMADB_AVAILABLE:
            try:
                # Build ChromaDB where clause
                if len(filters) == 1:
                    key, value = list(filters.items())[0]
                    where = {key: value}
                else:
                    where = {"$and": [{k: v} for k, v in filters.items()]}
                
                results = self._collection.get(
                    where=where,
                    limit=k,
                )
                
                docs = []
                for i, doc_id in enumerate(results["ids"]):
                    docs.append(Document(
                        id=doc_id,
                        content=results["documents"][i],
                        metadata=results["metadatas"][i] if results["metadatas"] else {},
                    ))
                return docs
                
            except Exception as e:
                print(f"Warning: Metadata search error: {e}")
                return []
        else:
            results = []
            for doc in self._documents.values():
                if all(doc.metadata.get(k) == v for k, v in filters.items()):
                    results.append(doc)
                    if len(results) >= k:
                        break
            return results
    
    def count(self) -> int:
        """Get total document count."""
        if CHROMADB_AVAILABLE:
            return self._collection.count()
        else:
            return len(self._documents)
    
    def clear(self) -> None:
        """Clear all documents."""
        if CHROMADB_AVAILABLE:
            self._client.delete_collection(self._collection_name)
            self._collection = self._client.create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            self._documents.clear()
            self._word_index.clear()
            self._save_fallback()
    
    def list_collections(self) -> List[str]:
        """List all collections (ChromaDB only)."""
        if CHROMADB_AVAILABLE:
            return [c.name for c in self._client.list_collections()]
        else:
            return [self._collection_name]
    
    def get_statistics(self) -> dict:
        """Get store statistics."""
        stats = {
            "document_count": self.count(),
            "persist_dir": self._persist_dir,
            "collection_name": self._collection_name,
            "backend": "chromadb" if CHROMADB_AVAILABLE else "fallback",
        }
        
        if CHROMADB_AVAILABLE:
            stats["collections"] = self.list_collections()
        
        return stats
