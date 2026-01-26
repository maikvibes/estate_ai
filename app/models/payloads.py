from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    input: str = Field(..., description="User input to process")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Optional metadata")


class TaskResponse(BaseModel):
    request_id: str
    status: str = "accepted"


class AgentRun(BaseModel):
    request_id: str
    input: str
    response: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="pending")
    created_at: float | None = None
