import asyncio
from typing import AsyncIterator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def init_db() -> AsyncIOMotorDatabase:
    """Initialize a shared Mongo client.

    A single global client is safe because Motor is thread-safe and keeps
    an internal connection pool. The caller should await this during app startup.
    """

    global _client, _db
    if _db is not None:
        return _db

    settings = get_settings()
    _client = AsyncIOMotorClient(str(settings.mongodb_uri))
    _db = _client[settings.mongodb_db]

    # Ensure a couple of useful indexes; keep this lightweight for startup.
    await _db["agent_runs"].create_index("request_id", unique=True)
    await _db["agent_runs"].create_index("status")
    await _db["agent_runs"].create_index("created_at")

    return _db


async def get_db() -> AsyncIterator[AsyncIOMotorDatabase]:
    """FastAPI dependency to provide a database handle per request."""

    if _db is None:
        await init_db()
    assert _db is not None  # for type checkers
    yield _db


async def close_db() -> None:
    """Close the Mongo client gracefully on shutdown."""

    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def run_sync(coro):
    """Run an async function in sync contexts (e.g., background scripts)."""

    return asyncio.get_event_loop().run_until_complete(coro)
