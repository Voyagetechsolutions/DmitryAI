# knowledge/ingestion.py
"""
Document Ingestion - Ingest documents into the knowledge base.

Supports:
- Codebase files
- Markdown documentation
- Design documents
- Text files
"""

import os
from typing import List, Optional
from datetime import datetime

from .vector_store import VectorStore, Document


class DocumentIngester:
    """
    Ingests documents into the vector store.
    """
    
    # Supported file extensions
    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".go", ".rs", ".rb", ".php",
        ".c", ".cpp", ".h", ".hpp", ".cs",
    }
    
    DOC_EXTENSIONS = {
        ".md", ".txt", ".rst", ".asciidoc",
    }
    
    CONFIG_EXTENSIONS = {
        ".json", ".yaml", ".yml", ".toml", ".ini",
        ".env", ".cfg", ".conf",
    }
    
    # Maximum file size (500 KB)
    MAX_FILE_SIZE = 500 * 1024
    
    # Chunk size for large files (characters)
    CHUNK_SIZE = 2000
    CHUNK_OVERLAP = 200
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize the ingester.
        
        Args:
            vector_store: The vector store to ingest into
        """
        self._store = vector_store
    
    def _get_file_type(self, path: str) -> Optional[str]:
        """Determine the file type from extension."""
        ext = os.path.splitext(path)[1].lower()
        
        if ext in self.CODE_EXTENSIONS:
            return "code"
        elif ext in self.DOC_EXTENSIONS:
            return "documentation"
        elif ext in self.CONFIG_EXTENSIONS:
            return "configuration"
        
        return None
    
    def _chunk_content(self, content: str) -> List[str]:
        """Split content into overlapping chunks."""
        if len(content) <= self.CHUNK_SIZE:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.CHUNK_SIZE
            
            # Try to break at a newline
            if end < len(content):
                newline_pos = content.rfind("\n", start, end)
                if newline_pos > start:
                    end = newline_pos + 1
            
            chunks.append(content[start:end])
            start = end - self.CHUNK_OVERLAP
        
        return chunks
    
    def _read_file(self, path: str) -> Optional[str]:
        """Read a file with size limit."""
        try:
            size = os.path.getsize(path)
            if size > self.MAX_FILE_SIZE:
                return None
            
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return None
    
    def ingest_file(
        self,
        path: str,
        metadata: dict = None,
    ) -> List[Document]:
        """
        Ingest a single file.
        
        Args:
            path: Path to the file
            metadata: Additional metadata
            
        Returns:
            List of created Documents (may be multiple if chunked)
        """
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            return []
        
        file_type = self._get_file_type(path)
        if not file_type:
            return []
        
        content = self._read_file(path)
        if not content:
            return []
        
        # Build metadata
        base_metadata = {
            "source": "file",
            "file_path": path,
            "file_name": os.path.basename(path),
            "file_type": file_type,
            "ingested_at": datetime.utcnow().isoformat() + "Z",
        }
        if metadata:
            base_metadata.update(metadata)
        
        # Chunk content if needed
        chunks = self._chunk_content(content)
        
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = base_metadata.copy()
            if len(chunks) > 1:
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(chunks)
            
            doc = self._store.add_document(chunk, chunk_metadata)
            documents.append(doc)
        
        return documents
    
    def ingest_directory(
        self,
        directory: str,
        recursive: bool = True,
        include_hidden: bool = False,
        file_types: List[str] = None,
    ) -> int:
        """
        Ingest all supported files in a directory.
        
        Args:
            directory: Directory to ingest
            recursive: Whether to recurse into subdirectories
            include_hidden: Whether to include hidden files/directories
            file_types: Filter by file types ("code", "documentation", "configuration")
            
        Returns:
            Number of files ingested
        """
        directory = os.path.abspath(directory)
        
        if not os.path.isdir(directory):
            return 0
        
        count = 0
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                
                # Skip common non-code directories
                dirs[:] = [d for d in dirs if d not in {
                    "node_modules", ".git", "__pycache__", ".venv", "venv",
                    "build", "dist", ".next", ".cache",
                }]
                
                for filename in files:
                    if not include_hidden and filename.startswith("."):
                        continue
                    
                    path = os.path.join(root, filename)
                    file_type = self._get_file_type(path)
                    
                    if file_type:
                        if file_types and file_type not in file_types:
                            continue
                        
                        docs = self.ingest_file(path, {"project_dir": directory})
                        if docs:
                            count += 1
        else:
            for entry in os.listdir(directory):
                if not include_hidden and entry.startswith("."):
                    continue
                
                path = os.path.join(directory, entry)
                if os.path.isfile(path):
                    docs = self.ingest_file(path, {"project_dir": directory})
                    if docs:
                        count += 1
        
        return count
    
    def ingest_codebase(self, path: str) -> int:
        """
        Ingest a codebase (code files only).
        
        Args:
            path: Path to the codebase root
            
        Returns:
            Number of files ingested
        """
        return self.ingest_directory(
            path,
            recursive=True,
            include_hidden=False,
            file_types=["code"],
        )
    
    def ingest_docs(self, path: str) -> int:
        """
        Ingest documentation files.
        
        Args:
            path: Path to the docs directory
            
        Returns:
            Number of files ingested
        """
        return self.ingest_directory(
            path,
            recursive=True,
            include_hidden=False,
            file_types=["documentation"],
        )
    
    def ingest_text(
        self,
        content: str,
        source_type: str,
        title: str = None,
        metadata: dict = None,
    ) -> Document:
        """
        Ingest raw text content.
        
        Args:
            content: Text content
            source_type: Type of content (e.g., "design", "policy", "note")
            title: Optional title
            metadata: Additional metadata
            
        Returns:
            Created Document
        """
        base_metadata = {
            "source": "text",
            "source_type": source_type,
            "ingested_at": datetime.utcnow().isoformat() + "Z",
        }
        if title:
            base_metadata["title"] = title
        if metadata:
            base_metadata.update(metadata)
        
        return self._store.add_document(content, base_metadata)
