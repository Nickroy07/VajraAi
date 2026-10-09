from __future__ import annotations
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AuthorizationResult(str, Enum):
    pending = "pending"
    allowed = "allowed"
    denied = "denied"


class ExecutionStatus(str, Enum):
    not_attempted = "not_attempted"
    succeeded = "succeeded"
    failed = "failed"


class EventResponse(BaseModel):
    event_id: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    event_type: str
    authorization: AuthorizationResult
    authorization_reason: str = ""
    execution_status: ExecutionStatus
    execution_result: Optional[str] = None
    arguments: dict = Field(default_factory=dict)
    resource: str = ""
    destination: str = ""
    timestamp: str
    details: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class EventList(BaseModel):
    events: list[EventResponse]
    count: int