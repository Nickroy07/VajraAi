from __future__ import annotations
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    connected = "connected"
    disconnected = "disconnected"
    unknown = "unknown"


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    status: AgentStatus
    registered_at: str

    model_config = {"from_attributes": True}


class AgentList(BaseModel):
    agents: list[AgentResponse]
    count: int