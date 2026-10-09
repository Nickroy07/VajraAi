from __future__ import annotations
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class GatewayExecuteRequest(BaseModel):
    task_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    arguments: dict = Field(default_factory=dict)
    resource: str = ""
    destination: str = ""
    approval_id: Optional[str] = None


class GatewayExecuteResponse(BaseModel):
    event_id: str
    task_id: str
    tool_name: str
    authorization: str  # allowed | denied
    authorization_reason: str
    execution_status: str  # not_attempted | succeeded | failed
    execution_result: Optional[str] = None
    executor_call_count: int
    timestamp: str