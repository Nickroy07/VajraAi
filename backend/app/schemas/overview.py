from __future__ import annotations
from pydantic import BaseModel


class OverviewMetric(BaseModel):
    label: str
    value: int


class OverviewResponse(BaseModel):
    mode: str
    gateway_connected: bool
    metrics: list[OverviewMetric]
    recent_events: list[dict]
    attention_items: list[str]