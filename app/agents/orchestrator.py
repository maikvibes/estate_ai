import logging
import time
import asyncio
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agents.tools import ToolRegistry
from app.core.config import get_settings
from app.services.vector_store import VectorStore
from app.models.payloads import AgentRun

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates task handling via pattern matching + tools."""

    def __init__(self, db: AsyncIOMotorDatabase, vector_store: VectorStore) -> None:
        self.settings = get_settings()
        self.db = db
        self.vector_store = vector_store
        self.tools = ToolRegistry(vector_store=vector_store)

    async def process_task(self, payload: Dict[str, Any]) -> None:
        """Main entrypoint invoked per Kafka message."""

        eventId = str(payload.get("eventId", ""))
        title = payload.get("title", "")
        description = payload.get("description", "")
        user_input = f"{title}\n{description}".strip()
        metadata = {
            "listingId": payload.get("listingId"),
            "userId": payload.get("userId"),
            "category": payload.get("category"),
            "price": payload.get("price"),
            "analysisType": payload.get("analysisType")
        }

        logger.info("Processing task eventId=%s", eventId)

        # Kick off agent run. We await because we want the result before acknowledging work.
        try:
            response = await self._run_agent(user_input=user_input, metadata=metadata)
        except Exception:
            logger.exception("Agent failed for eventId=%s", eventId)
            await self._persist_failure(eventId=eventId, user_input=user_input, metadata=metadata)
            return

        await self._persist_success(eventId=eventId, user_input=user_input, response=response, metadata=metadata)

    async def _run_agent(self, user_input: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent conversation using pattern matching.
        """

        # Provide vector context as a starting hint.
        context = await self.tools.lookup_vector_store(query=user_input)

        # Introduce a delay to simulate agent thought process
        await asyncio.sleep(2.0)

        lower_input = user_input.lower()
        words = set(lower_input.replace(".", " ").replace(",", " ").split())
        
        # Use Python structural pattern matching (simulated with if/elif since match on sets is less elegant, but we can match on the string)
        match lower_input:
            case _ if any(w in words for w in ["price", "cost", "expensive", "cheap"]):
                text_response = "The price is competitive and aligns with current market rates for this area."
            case _ if any(w in words for w in ["location", "address", "area", "neighborhood"]):
                text_response = "This property is located in a highly desirable and convenient neighborhood."
            case _ if any(w in words for w in ["scam", "fraud", "suspicious", "fake"]):
                text_response = "This listing has been flagged for review due to potentially suspicious keywords. We take your safety seriously."
            case _ if "contact" in words or "viewing" in words:
                text_response = "You can contact the agent directly to schedule a viewing. Let me know if you need their details!"
            case _:
                text_response = "I have received your inquiry. I can help you with questions about this listing's price, location, or schedule a viewing."

        return {
            "text": text_response,
            "context": context,
        }

    async def _persist_success(self, eventId: str, user_input: str, response: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        record = AgentRun(
            eventId=eventId,
            input=user_input,
            response=response,
            metadata=metadata,
            status="completed",
            created_at=time.time(),
        ).model_dump()
        await self.db["agent_runs"].insert_one(record)

    async def _persist_failure(self, eventId: str, user_input: str, metadata: Dict[str, Any]) -> None:
        record = AgentRun(
            eventId=eventId,
            input=user_input,
            response=None,
            metadata=metadata,
            status="failed",
            created_at=time.time(),
        ).model_dump()
        await self.db["agent_runs"].insert_one(record)
