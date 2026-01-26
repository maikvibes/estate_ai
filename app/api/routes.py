import uuid
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.services.kafka_service import KafkaService
from app.models.payloads import TaskRequest, TaskResponse

router = APIRouter()
kafka_service = KafkaService()


@router.post("/requests", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_request(body: TaskRequest) -> TaskResponse:
    settings = get_settings()
    request_id = str(uuid.uuid4())
    payload = {"request_id": request_id, "input": body.input, "metadata": body.metadata or {}}

    try:
        await kafka_service.send(topic=settings.kafka_requests_topic, payload=payload)
    except Exception as exc:  # pragma: no cover - network failure path
        raise HTTPException(status_code=500, detail="Failed to enqueue request") from exc

    return TaskResponse(request_id=request_id)
