from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    blocked = "blocked"
    completed = "completed"
    failed = "failed"


class TaskScope(BaseModel):
    allowed_tools: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    destination_allowlist: list[str] = Field(default_factory=list)
    block_external_destinations: bool = False


class TaskBase(BaseModel):
    description: str = Field(..., min_length=1)
    status: TaskStatus = TaskStatus.pending
    scope: TaskScope = Field(default_factory=TaskScope)


class TaskCreate(TaskBase):
    task_id: str = Field(default_factory=lambda: str(uuid4()))


class TaskResponse(TaskBase):
    task_id: str
    created_at: str
    updated_at: str
    scope: TaskScope

    model_config = {"from_attributes": True}


class TaskList(BaseModel):
    tasks: list[TaskResponse]
    count: int