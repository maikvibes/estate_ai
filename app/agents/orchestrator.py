import logging
import time
from typing import Any, Dict

from google.adk import Agent
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agents.tools import ToolRegistry
from app.core.config import get_settings
from app.services.vector_store import VectorStore
from app.models.payloads import AgentRun

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates task handling via Google ADK Agent + tools."""

    def __init__(self, db: AsyncIOMotorDatabase, vector_store: VectorStore) -> None:
        self.settings = get_settings()
        self.db = db
        self.vector_store = vector_store
        self.tools = ToolRegistry(vector_store=vector_store)

        self._agent = self._create_agent()

    def _create_agent(self) -> Any:
        """Create an Agent with tools attached.
        """

        return Agent(
            name="background_agent",
            model=self.settings.google_genai_model,
            tools=self.tools.to_functions(),
        )

    async def process_task(self, payload: Dict[str, Any]) -> None:
        """Main entrypoint invoked per Kafka message."""

        request_id = payload.get("request_id")
        user_input = payload.get("input") or ""
        metadata = payload.get("metadata", {})

        logger.info("Processing task request_id=%s", request_id)

        # Kick off agent run. We await because we want the result before acknowledging work.
        try:
            response = await self._run_agent(user_input=user_input, metadata=metadata)
        except Exception:
            logger.exception("Agent failed for request_id=%s", request_id)
            await self._persist_failure(request_id=request_id, user_input=user_input, metadata=metadata)
            return

        await self._persist_success(request_id=request_id, user_input=user_input, response=response, metadata=metadata)

    async def _run_agent(self, user_input: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent conversation.
        """

        # Provide vector context as a starting hint.
        context = await self.tools.lookup_vector_store(query=user_input)

        # In google-adk we use agent.run()
        prompt = f"Context: {context}\nUser Input: {user_input}"
        
        # Make the call using the newer SDK
        result = await self._agent.run(prompt)

        # result can be converted to dict for persistence; minimal schema here.
        return {
            "text": getattr(result, "text", None) or str(result),
            "context": context,
        }

    async def _persist_success(self, request_id: str, user_input: str, response: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        record = AgentRun(
            request_id=request_id,
            input=user_input,
            response=response,
            metadata=metadata,
            status="completed",
            created_at=time.time(),
        ).model_dump()
        await self.db["agent_runs"].insert_one(record)

    async def _persist_failure(self, request_id: str, user_input: str, metadata: Dict[str, Any]) -> None:
        record = AgentRun(
            request_id=request_id,
            input=user_input,
            response=None,
            metadata=metadata,
            status="failed",
            created_at=time.time(),
        ).model_dump()
        await self.db["agent_runs"].insert_one(record)
