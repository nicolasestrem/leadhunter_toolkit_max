"""Utilities for building and querying a lightweight local content index.

The :class:`SiteIndexer` keeps the implementation intentionally lightweight so
that it can run in resource constrained environments (e.g. a CLI session or a
small Streamlit deployment) without external vector database dependencies. Key
design notes that are relevant when integrating the indexer are summarised
below:

* **Embedding dimensionality (384)** – the hashing-based bag-of-words approach
  distributes terms across a 384 dimension vector. This size strikes a balance
  between minimising hash collisions for medium sized vocabularies while
  keeping both the stored footprint (float32 vectors on disk) and cosine
  similarity calculations fast. Empirically, higher dimensionalities offered
  diminishing improvements for short marketing pages while increasing storage
  costs.
* **Chunking** – text is tokenised by whitespace and grouped into chunks of
  ``chunk_size`` tokens with an overlap of ``chunk_overlap``. For typical web
  pages we have found a chunk size in the 300-500 word range with ~10% overlap
  (the defaults are 400 / 40) provides a good trade-off between context and
  retrieval granularity. Smaller chunks may improve recall for dense pages at
  the cost of larger indices.
* **Performance characteristics** – indexing is CPU bound and scales linearly
  with the number of chunks. Embedding generation is a simple hashing loop,
  making it suitable for bulk ingestion of hundreds of documents per minute on
  commodity hardware. Querying runs a vector dot product in-memory and filters
  on metadata, which keeps median query latency well below a second for tens of
  thousands of chunks.
"""
from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, date, time, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import numpy as np


@dataclass
class IndexQueryResult:
    """Container for semantic search results."""

    url: str
    score: float
    text: str
    timestamp: Optional[str]
    domain: Optional[str]
    chunk_index: int
    metadata: Dict[str, Any]


class SiteIndexer:
    """Create and query a simple on-disk vector index for crawled content."""

    def __init__(
        self,
        index_path: Union[str, Path],
        *,
        chunk_size: int = 400,
        chunk_overlap: int = 40,
        embedding_dim: int = 384,
    ) -> None:
        """Initialise a new index or load an existing one.

        Args:
            index_path: Directory where ``embeddings.npy`` and
                ``metadata.json`` should be stored.
            chunk_size: Maximum number of whitespace-delimited tokens per
                chunk. Values between 300 and 500 work well for general web
                copy; prefer the lower end for very dense content or the upper
                end for narrative-heavy articles.
            chunk_overlap: Number of tokens to repeat between neighbouring
                chunks. A 5-15% overlap is usually sufficient to avoid losing
                connective context between sections.
            embedding_dim: Size of the hashed embedding vector. The default of
                384 keeps similarity calculations fast while mitigating hash
                collisions for marketing and sales content. Larger values may
                be useful when indexing sizeable corpora with more varied
                vocabularies.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.index_dir = Path(index_path)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_path = self.index_dir / "embeddings.npy"
        self.metadata_path = self.index_dir / "metadata.json"

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_dim = embedding_dim

        self.embeddings: np.ndarray = np.empty((0, embedding_dim), dtype=np.float32)
        self.metadata: List[Dict[str, Any]] = []
        self._dirty = False

        self._load_index()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_index(self) -> None:
        """Load embeddings and metadata from disk if they exist."""
        if self.embeddings_path.exists():
            try:
                arr = np.load(self.embeddings_path)
                if arr.ndim == 1:
                    arr = arr.reshape(-1, self.embedding_dim)
                self.embeddings = arr.astype(np.float32)
            except Exception:
                self.embeddings = np.empty((0, self.embedding_dim), dtype=np.float32)
        if self.metadata_path.exists():
            try:
                self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            except Exception:
                self.metadata = []

    def _save_index(self) -> None:
        """Persist embeddings and metadata to disk."""
        np.save(self.embeddings_path, self.embeddings)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        self._dirty = False

    # ------------------------------------------------------------------
    # Text preparation
    # ------------------------------------------------------------------
    def chunk_content(self, content: str) -> List[str]:
        """Split text into overlapping chunks sized by words."""
        tokens = content.split()
        if not tokens:
            return []

        step = self.chunk_size - self.chunk_overlap
        chunks: List[str] = []
        for start in range(0, len(tokens), step):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            if not chunk_tokens:
                continue
            chunks.append(" ".join(chunk_tokens))
            if end == len(tokens):
                break
        return chunks

    # ------------------------------------------------------------------
    # Embedding utilities
    # ------------------------------------------------------------------
    def _embed_text(self, text: str) -> np.ndarray:
        """Create a deterministic hashing-based embedding vector."""
        vector = np.zeros(self.embedding_dim, dtype=np.float32)
        tokens = re.findall(r"[\w-]+", text.lower())
        if not tokens:
            return vector

        for token in tokens:
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.embedding_dim
            vector[idx] += 1.0

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector

    # ------------------------------------------------------------------
    # Index population
    # ------------------------------------------------------------------
    def index_page(
        self,
        url: str,
        content: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Chunk, embed, and store a document associated with a URL."""
        if not content.strip():
            return []

        chunks = self.chunk_content(content)
        if not chunks:
            return []

        domain = urlparse(url).netloc or None
        ts = timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_iso = ts.isoformat()

        new_embeddings: List[np.ndarray] = []
        new_metadata: List[Dict[str, Any]] = []

        for chunk_index, chunk in enumerate(chunks):
            embedding = self._embed_text(chunk)
            new_embeddings.append(embedding)

            entry: Dict[str, Any] = {
                "url": url,
                "domain": domain,
                "timestamp": ts_iso,
                "chunk_index": chunk_index,
                "text": chunk,
            }
            if metadata:
                entry.update(metadata)
            new_metadata.append(entry)

        if new_embeddings:
            stacked = np.vstack(new_embeddings)
            if self.embeddings.size == 0:
                self.embeddings = stacked
            else:
                self.embeddings = np.vstack([self.embeddings, stacked])
            self.metadata.extend(new_metadata)
            self._dirty = True
            self._save_index()

        return new_metadata

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------
    def query(
        self,
        query_text: str,
        *,
        top_k: int = 5,
        domain: Optional[str] = None,
        start_date: Optional[Union[str, datetime, date]] = None,
        end_date: Optional[Union[str, datetime, date]] = None,
    ) -> List[IndexQueryResult]:
        """Perform semantic search with optional domain and date filters."""
        query_text = query_text.strip()
        if not query_text or not self.metadata:
            return []

        query_vec = self._embed_text(query_text)
        if not np.any(query_vec):
            return []

        scores = self.embeddings @ query_vec
        domain_filter = domain.lower() if domain else None
        start_dt = self._coerce_datetime(start_date)
        end_dt = self._coerce_datetime(end_date)

        scored_items: List[Tuple[int, float]] = []
        for idx, meta in enumerate(self.metadata):
            if domain_filter and meta.get("domain"):
                if domain_filter not in meta["domain"].lower():
                    continue
            elif domain_filter and not meta.get("domain"):
                continue

            ts = self._parse_timestamp(meta.get("timestamp"))
            if start_dt and (ts is None or ts < start_dt):
                continue
            if end_dt and (ts is None or ts > end_dt):
                continue

            scored_items.append((idx, float(scores[idx])))

        if not scored_items:
            return []

        scored_items.sort(key=lambda item: item[1], reverse=True)
        limited = scored_items[: max(1, top_k)]

        results: List[IndexQueryResult] = []
        for idx, score in limited:
            meta = self.metadata[idx]
            meta_copy = dict(meta)
            text = meta_copy.pop("text", "")
            result = IndexQueryResult(
                url=meta_copy.get("url", ""),
                score=score,
                text=text,
                timestamp=meta_copy.get("timestamp"),
                domain=meta_copy.get("domain"),
                chunk_index=int(meta_copy.get("chunk_index", 0)),
                metadata={k: v for k, v in meta_copy.items() if k not in {"url", "timestamp", "domain", "chunk_index"}},
            )
            results.append(result)

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _coerce_datetime(self, value: Optional[Union[str, datetime, date]]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        if isinstance(value, date):
            return datetime.combine(value, time.min, tzinfo=timezone.utc)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(value)
            except ValueError:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        return None

    def _parse_timestamp(self, timestamp: Optional[str]) -> Optional[datetime]:
        if not timestamp:
            return None
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def flush(self) -> None:
        """Persist pending updates if there are unsaved changes."""
        if self._dirty:
            self._save_index()

