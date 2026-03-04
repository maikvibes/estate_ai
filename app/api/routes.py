import uuid
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.services.kafka_service import KafkaService
from app.models.payloads import EventRequest, EventResponse

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
