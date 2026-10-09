"""Document Guard — heuristic scan plus a DEMO agent run through the real gateway.

The document body is processed in memory only; it is never persisted.
"""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.attack_lab import ScenarioResult
from app.schemas.document_guard import DocumentAgentRunResponse, DocumentScanRequest, DocumentScanResponse
from app.services.demo_agent import SEEDED_AGENT_ID, SEEDED_TASK_ID, run_proposal
from app.services.document_guard import extract_agent_proposal, scan_text
from app.services.gateway import get_gateway

router = APIRouter(prefix="/api/v1", tags=["document-guard"])

DISCLAIMER = (
    "Findings are heuristic risk signals from deterministic rules, not a malware verdict. "
    "They never authorize or block anything — only the gateway policy does."
)


def _scan(text: str) -> DocumentScanResponse:
    return DocumentScanResponse(**scan_text(text), disclaimer=DISCLAIMER)


@router.post("/document-guard/scan", response_model=DocumentScanResponse)
def scan_document(body: DocumentScanRequest) -> DocumentScanResponse:
    return _scan(body.text)


@router.post("/document-guard/agent-run", response_model=DocumentAgentRunResponse)
def run_protected_agent(body: DocumentScanRequest) -> DocumentAgentRunResponse:
    settings = get_settings()
    gateway = get_gateway(settings.sqlite_path)
    proposal = extract_agent_proposal(body.text)
    request = {
        "task_id": SEEDED_TASK_ID,
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": proposal["tool_name"],
        "arguments": proposal["arguments"],
        "resource": "invoice-42",
    }
    result = run_proposal(
        gateway, "document_guard", "Document → protected agent", request,
        proposal["rationale"], source="document_guard",
    )
    return DocumentAgentRunResponse(
        scan=_scan(body.text), agent_rationale=proposal["rationale"], result=ScenarioResult(**result)
    )
