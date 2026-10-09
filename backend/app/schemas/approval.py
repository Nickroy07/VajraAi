from __future__ import annotations
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    expired = "expired"
    consumed = "consumed"


class ApprovalResponse(BaseModel):
    approval_id: str
    task_id: str
    agent_id: Optional[str] = None
    tool_name: str
    arguments: dict = Field(default_factory=dict)
    arguments_hash: str
    resource: str = ""
    destination: str = ""
    reason: str = ""
    status: ApprovalStatus
    expires_at: str
    consumed_at: Optional[str] = None
    created_at: str
    decided_at: Optional[str] = None
    decided_by: str = "system"

    model_config = {"from_attributes": True}


class ApprovalList(BaseModel):
    approvals: list[ApprovalResponse]
    count: int


class ApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approve|deny)$")