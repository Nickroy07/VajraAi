from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, Field


class GatewayExecuteRequest(BaseModel):
    task_id: str = Field(..., min_length=1, max_length=100)
    agent_id: str = Field(..., min_length=1, max_length=100)
    tool_name: str = Field(..., min_length=1, max_length=100)
    arguments: dict = Field(default_factory=dict)
    resource: str = Field("", max_length=300)
    destination: str = Field("", max_length=300)
    approval_id: Optional[str] = Field(None, max_length=100)


class GatewayExecuteResponse(BaseModel):
    event_id: str
    task_id: str
    tool_name: str
    authorization: str  # allowed | denied | pending_approval
    authorization_reason: str
    execution_status: str  # not_attempted | succeeded | failed
    execution_result: Optional[str] = None
    executor_call_count: int  # mock-executor invocations caused by THIS request (0 or 1)
    resource: str = ""
    destination: str = ""
    approval_id: Optional[str] = None
    timestamp: str
