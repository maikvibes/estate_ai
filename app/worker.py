import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from app.agents.orchestrator import AgentOrchestrator
from app.core.database import close_db, get_db, init_db
from app.services.kafka_service import KafkaService
from app.core.config import get_settings
from app.services.vector_store import ChromaVectorStore, InMemoryVectorStore

logger = logging.getLogger(__name__)

kafka = KafkaService()
settings = get_settings()
# Default to Chroma (real vector DB, local/no auth). Fall back to in-memory if creation fails.
try:
    vector_store = ChromaVectorStore(persist_directory=settings.chroma_persist_dir)
except Exception:  # pragma: no cover - env-specific failure
    logging.exception("Failed to init Chroma; using in-memory vector store")
    vector_store = InMemoryVectorStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload vector store with a couple items for demo.
    vector_store.bulk_load([
        ("doc-1", "Quarterly revenue report shows strong growth."),
        ("doc-2", "Security incident postmortem and remediation plan."),
    ])

    db = await init_db()
    orchestrator = AgentOrchestrator(db=db, vector_store=vector_store)

    await kafka.start()
    await kafka.consume_forever(handler=orchestrator.process_task)
    try:
        yield
    finally:
        await kafka.stop()
        await close_db()


def create_app() -> FastAPI:
    return FastAPI(lifespan=lifespan)


app = create_app()


async def main() -> None:
    # Worker entry point when launched as a script.
    # We keep the loop running until cancelled (CTRL+C or orchestrated shutdown).
    api = create_app()
    # Running the FastAPI lifespan manually to start consumer without serving HTTP.
    async with lifespan(api):
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
