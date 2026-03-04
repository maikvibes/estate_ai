from __future__ import annotations

from typing import Any, Optional, List

from pydantic import BaseModel, Field


class EventRequest(BaseModel):
    eventId: str
    eventType: str
    eventTimestamp: List[int]
    listingId: str
    userId: str
    title: str
    description: str
    category: str
    images: Optional[List[str]] = None
    price: Optional[float] = None
    documentType: Optional[List[str]] = None
    fileUrl: Optional[List[str]] = None
    analysisType: str
    priority: int


class EventResponse(BaseModel):
    eventId: str
    status: str = "accepted"


class AgentRun(BaseModel):
    eventId: str
    input: str
    response: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="pending")
    created_at: float | None = None
