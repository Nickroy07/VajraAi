from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ScenarioId(str, Enum):
    authorized_invoice_read = "authorized_invoice_read"
    prompt_injection_email = "prompt_injection_email"
    unauthorized_file_delete = "unauthorized_file_delete"


class AttackLabRequest(BaseModel):
    scenario_ids: list[ScenarioId]


class TraceStage(BaseModel):
    stage: str
    status: str
    detail: Optional[str] = None


class ScenarioResult(BaseModel):
    scenario_id: str
    scenario_label: str
    final_authorization: str
    authorization_reason: str
    execution_status: str
    executor_call_count: int
    event_id: str
    trace: list[TraceStage]


class AttackLabResponse(BaseModel):
    mode: str
    results: list[ScenarioResult]