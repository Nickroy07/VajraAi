from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel

from app.schemas.gateway import GatewayExecuteRequest


class ScenarioId(str, Enum):
    authorized_invoice_read = "authorized_invoice_read"
    local_summary = "local_summary"
    prompt_injection_email = "prompt_injection_email"
    unauthorized_file_delete = "unauthorized_file_delete"
    approval_vendor_email = "approval_vendor_email"


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
    executor_call_count: int  # verified delta of the tool's persisted mock-executor counter
    executor_calls_before: int
    executor_calls_after: int
    event_id: str
    approval_id: Optional[str] = None
    request: GatewayExecuteRequest
    trace: list[TraceStage]


class AttackLabResponse(BaseModel):
    mode: str
    results: list[ScenarioResult]
