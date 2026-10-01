"""Semantic Passage Retrieval Module (A4).

Splits the 29 authoritative documentation articles (data/documentation.json)
into granular, semantic section chunks and provides high-precision retrieval
with real doc IDs and chunk IDs.
Uses ChromaDB for vector storage as required.
"""

from typing import Any, Dict, List, Optional
import json
import logging
import os
import re
import chromadb
from src.models import RetrievedChunk

logger = logging.getLogger(__name__)

DEFAULT_DOCS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documentation.json")

class DocumentRetriever:
    """Retrieves authoritative documentation chunks using hybrid semantic search with Chroma."""

    def __init__(self, docs_path: str = DEFAULT_DOCS_PATH, min_score: float = 0.15):
        self.docs_path = docs_path
        self.min_score = min_score
        
        # Initialize ChromaDB client (local persistence)
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "chroma_db")
        os.makedirs(db_path, exist_ok=True)
        try:
            self.chroma_client = chromadb.PersistentClient(path=db_path)
        except AttributeError:
            from chromadb.config import Settings
            self.chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=db_path))
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="cloudserve_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.chunks_cache: Dict[str, Dict[str, Any]] = {}
        
        if self.collection.count() == 0:
            self._load_and_chunk()
        else:
            self._load_cache_only()

    def _load_cache_only(self):
        if not os.path.exists(self.docs_path):
            return
        with open(self.docs_path, "r", encoding="utf-8") as f:
            raw_docs = json.load(f)
        for doc in raw_docs:
            doc_id = doc.get("doc_id", "UNKNOWN-DOC")
            title = doc.get("title", "")
            category = doc.get("category", "")
            content = doc.get("content", "")
            sections = re.split(r"\n(?=##\s+)", content)
            for idx, sec in enumerate(sections):
                sec_text = sec.strip()
                if not sec_text:
                    continue
                first_line = sec_text.split("\n")[0].replace("#", "").strip()
                chunk_id = f"{doc_id}#sec-{idx}"
                full_chunk_text = f"{title} | {first_line}\n{sec_text}"
                self.chunks_cache[chunk_id] = {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "title": title,
                    "category": category,
                    "section": first_line,
                    "content": full_chunk_text,
                }
            
    def _load_and_chunk(self):
        """Loads documentation.json and breaks each document into section chunks."""
        self._load_cache_only()
        
        if not self.chunks_cache:
            return
            
        ids = []
        documents = []
        metadatas = []
        
        for chunk_id, data in self.chunks_cache.items():
            ids.append(chunk_id)
            documents.append(data["content"])
            metadatas.append({
                "doc_id": data["doc_id"],
                "title": data["title"],
                "category": data["category"],
                "section": data["section"]
            })
            
        logger.info(f"Indexing {len(documents)} documentation chunks into ChromaDB...")
        # Add to Chroma in a single batch
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("ChromaDB indexing complete.")

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Retrieve the top-k most relevant documentation chunks using ChromaDB."""
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        
        results = self.collection.query(
            query_texts=[clean_query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        retrieved = []
        if not results["ids"] or not results["ids"][0]:
            return []
            
        for i in range(len(results["ids"][0])):
            chunk_id = results["ids"][0][i]
            dist = results["distances"][0][i]
            # Chroma with cosine uses cosine distance (1 - cosine similarity)
            score = 1.0 - dist
            
            if score < self.min_score:
                continue
                
            meta = results["metadatas"][0][i]
            content = results["documents"][0][i]
            
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    doc_id=meta["doc_id"],
                    title=meta["title"],
                    content=content,
                    category=meta.get("category"),
                    score=round(score, 4),
                )
            )
            
        return retrieved

# Global singleton instance
_retriever_instance: Optional[DocumentRetriever] = None

def get_retriever(docs_path: str = DEFAULT_DOCS_PATH) -> DocumentRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = DocumentRetriever(docs_path=docs_path)
    return _retriever_instance

def retrieve_passages(query: str, top_k: int = 5) -> List[RetrievedChunk]:
    return get_retriever().retrieve(query, top_k=top_k)
