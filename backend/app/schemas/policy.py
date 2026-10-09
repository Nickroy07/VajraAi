from __future__ import annotations
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class PolicyAction(str, Enum):
    allow = "allow"
    deny = "deny"
    require_approval = "require_approval"


class PolicyRule(BaseModel):
    tool: str = Field(..., min_length=1)
    action: PolicyAction
    description: str = ""


class PolicyResponse(BaseModel):
    policy_id: str
    task_id: str
    rules: list[PolicyRule]
    updated_at: str

    model_config = {"from_attributes": True}


class PolicyUpdate(BaseModel):
    rules: list[PolicyRule]