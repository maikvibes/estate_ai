from __future__ import annotations

from typing import Any, List

from app.services.vector_store import VectorDocument, VectorStore


class ToolRegistry:
    """Registry of tools the agent can call.

    This keeps tools organized and makes it easy to swap implementations.
    """

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    async def lookup_vector_store(self, query: str, top_k: int = 3) -> List[dict[str, Any]]:
        """Retrieve contextual snippets for the agent.

        A real implementation would run embedding search; here we just do
        a naive lookup. Returning simple dicts keeps them JSON-serializable.
        """

        results: list[VectorDocument] = self.vector_store.search(query=query, top_k=top_k)
        return [result.__dict__ for result in results]

    def to_functions(self) -> dict[str, Any]:
        """Expose callables in a dictionary so ADK can bind them as tools."""

        return {
            "lookup_vector_store": self.lookup_vector_store,
        }
