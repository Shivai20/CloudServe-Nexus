"""Semantic Passage Retrieval Module (A4).

Splits the 29 authoritative documentation articles (data/documentation.json)
into granular, semantic section chunks and provides high-precision retrieval
with real doc IDs and chunk IDs.
"""

from typing import Any, Dict, List, Optional
import json
import logging
import os
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from src.models import RetrievedChunk

logger = logging.getLogger(__name__)

DEFAULT_DOCS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documentation.json")

class DocumentRetriever:
    """Retrieves authoritative documentation chunks using hybrid semantic search."""

    def __init__(self, docs_path: str = DEFAULT_DOCS_PATH, min_score: float = 0.15):
        self.docs_path = docs_path
        self.min_score = min_score
        self.chunks: List[Dict[str, Any]] = []
        self.model = None
        self.chunk_embeddings = None
        self._load_and_chunk()

    def _load_and_chunk(self):
        """Loads documentation.json and breaks each document into section chunks."""
        if not os.path.exists(self.docs_path):
            logger.warning(f"Docs path not found at {self.docs_path}")
            return

        with open(self.docs_path, "r", encoding="utf-8") as f:
            raw_docs = json.load(f)

        self.chunks = []
        for doc in raw_docs:
            doc_id = doc.get("doc_id", "UNKNOWN-DOC")
            title = doc.get("title", "")
            category = doc.get("category", "")
            content = doc.get("content", "")

            # Split into sections using markdown headers
            sections = re.split(r"\n(?=##\s+)", content)
            for idx, sec in enumerate(sections):
                sec_text = sec.strip()
                if not sec_text:
                    continue
                first_line = sec_text.split("\n")[0].replace("#", "").strip()
                chunk_id = f"{doc_id}#sec-{idx}"
                full_chunk_text = f"{title} | {first_line}\n{sec_text}"

                self.chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "title": title,
                    "category": category,
                    "section": first_line,
                    "content": full_chunk_text,
                })

        # Embed using all-MiniLM-L6-v2 (Requirement #4)
        corpus = [c["content"] for c in self.chunks]
        if corpus:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.chunk_embeddings = self.model.encode(corpus)
                logger.info(f"Indexed {len(self.chunks)} documentation chunks using all-MiniLM-L6-v2.")
            except ImportError:
                logger.error("sentence-transformers is not installed. Run pip install sentence-transformers")

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Retrieve the top-k most relevant documentation chunks for a given query."""
        if not query or not query.strip() or not self.chunks or self.chunk_embeddings is None:
            return []

        clean_query = query.strip()
        q_vec = self.model.encode([clean_query])
        sims = cosine_similarity(q_vec, self.chunk_embeddings)[0]

        # Rank indices by descending similarity
        ranked_indices = sims.argsort()[::-1]

        results: List[RetrievedChunk] = []
        for idx in ranked_indices[:top_k]:
            score = float(sims[idx])
            if score < self.min_score:
                continue

            chunk_meta = self.chunks[idx]
            results.append(
                RetrievedChunk(
                    chunk_id=chunk_meta["chunk_id"],
                    doc_id=chunk_meta["doc_id"],
                    title=chunk_meta["title"],
                    content=chunk_meta["content"],
                    category=chunk_meta.get("category"),
                    score=round(score, 4),
                )
            )

        return results


# Global singleton instance
_retriever_instance: Optional[DocumentRetriever] = None


def get_retriever(docs_path: str = DEFAULT_DOCS_PATH) -> DocumentRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = DocumentRetriever(docs_path=docs_path)
    return _retriever_instance


def retrieve_passages(query: str, top_k: int = 5) -> List[RetrievedChunk]:
    return get_retriever().retrieve(query, top_k=top_k)
