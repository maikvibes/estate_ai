from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol, Tuple

import chromadb
from chromadb.api import ClientAPI
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


@dataclass
class VectorDocument:
    doc_id: str
    text: str
    score: float


class VectorStore(Protocol):
    def add(self, doc_id: str, text: str) -> None:
        ...

    def search(self, query: str, top_k: int = 3) -> List[VectorDocument]:
        ...

    def bulk_load(self, items: Iterable[Tuple[str, str]]) -> None:
        ...


class InMemoryVectorStore:
    """Simple placeholder vector store."""

    def __init__(self) -> None:
        self._docs: list[Tuple[str, str]] = []

    def add(self, doc_id: str, text: str) -> None:
        self._docs.append((doc_id, text))

    def search(self, query: str, top_k: int = 3) -> List[VectorDocument]:
        scored: list[VectorDocument] = []
        for doc_id, text in self._docs:
            score = text.lower().count(query.lower())
            if score > 0:
                scored.append(VectorDocument(doc_id=doc_id, text=text, score=float(score)))
        scored.sort(key=lambda d: d.score, reverse=True)
        return scored[:top_k]

    def bulk_load(self, items: Iterable[Tuple[str, str]]) -> None:
        for doc_id, text in items:
            self.add(doc_id, text)


class ChromaVectorStore:
    """Local Chroma vector DB; no auth required.

    Uses default embedding function for convenience. Suitable for dev/single-node
    use and can be swapped for a hosted vector DB later.
    """

    def __init__(self, persist_directory: str = ".chroma", collection_name: str = "agent_context") -> None:
        self.client: ClientAPI = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=DefaultEmbeddingFunction(),
        )

    def add(self, doc_id: str, text: str) -> None:
        self.collection.add(documents=[text], ids=[doc_id])

    def search(self, query: str, top_k: int = 3) -> List[VectorDocument]:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        docs: list[VectorDocument] = []
        for ids, docs_text, score in zip(
            results.get("ids", [[]])[0],
            results.get("documents", [[]])[0],
            results.get("distances", [[]])[0],
        ):
            docs.append(VectorDocument(doc_id=ids, text=docs_text, score=float(score)))
        # Chroma returns lower distances = closer; sort ascending then reverse to keep existing semantics
        docs.sort(key=lambda d: d.score)
        return docs

    def bulk_load(self, items: Iterable[Tuple[str, str]]) -> None:
        for doc_id, text in items:
            self.add(doc_id, text)
