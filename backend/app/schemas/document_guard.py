from __future__ import annotations
from pydantic import BaseModel, Field

from app.schemas.attack_lab import ScenarioResult
from app.services.document_guard import MAX_DOCUMENT_CHARS


class DocumentScanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_DOCUMENT_CHARS)


class DocumentFinding(BaseModel):
    type: str
    severity: str  # review | elevated | high
    evidence: str
    explanation: str


class DocumentScanStats(BaseModel):
    characters: int
    lines: int
    sha256_prefix: str


class DocumentScanResponse(BaseModel):
    mode: str = "demo"
    risk_level: str  # no_signals | review | elevated | high
    findings: list[DocumentFinding]
    stats: DocumentScanStats
    disclaimer: str


class DocumentAgentRunResponse(BaseModel):
    mode: str = "demo"
    scan: DocumentScanResponse
    agent_rationale: str
    result: ScenarioResult
