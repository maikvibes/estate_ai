import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.services.kafka_service import KafkaService
from app.models.payloads import EventRequest, EventResponse, AgentRun, AgentRunUpdate
from app.core.database import get_db

router = APIRouter()
kafka_service = KafkaService()


@router.post("/requests", response_model=EventResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_request(body: EventRequest) -> EventResponse:
    settings = get_settings()
    # Assume the client passes the eventId, but if we need to we can ensure it's there
    payload = body.model_dump()

    try:
        await kafka_service.send(topic=settings.kafka_requests_topic, payload=payload)
    except Exception as exc:  # pragma: no cover - network failure path
        raise HTTPException(status_code=500, detail="Failed to enqueue request") from exc

    return EventResponse(eventId=body.eventId)


@router.get("/agent-runs", response_model=List[AgentRun])
async def list_agent_runs(db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db["agent_runs"].find().sort("created_at", -1)
    runs = await cursor.to_list(length=100)
    return runs


@router.get("/agent-runs/{eventId}", response_model=AgentRun)
async def get_agent_run(eventId: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    run = await db["agent_runs"].find_one({"eventId": eventId})
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.patch("/agent-runs/{eventId}", response_model=AgentRun)
async def update_agent_run(eventId: str, body: AgentRunUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    result = await db["agent_runs"].find_one_and_update(
        {"eventId": eventId},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return result


@router.delete("/agent-runs/{eventId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_run(eventId: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db["agent_runs"].delete_one({"eventId": eventId})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return None
