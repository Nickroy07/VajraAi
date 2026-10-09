"""Approval routes — list, inspect and decide. Approvals are created only by the gateway."""

import json

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.database.init_db import get_connection
from app.schemas.approval import ApprovalDecision, ApprovalList, ApprovalResponse
from app.schemas.attack_lab import ScenarioResult
from app.services.demo_agent import run_proposal
from app.services.gateway import get_gateway

router = APIRouter(prefix="/api/v1", tags=["approvals"])


def _to_response(r) -> ApprovalResponse:
    r = dict(r)
    args_raw = r.get("arguments")
    args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
    return ApprovalResponse(
        approval_id=r["approval_id"],
        task_id=r["task_id"],
        agent_id=r.get("agent_id"),
        tool_name=r["tool_name"],
        arguments=args if isinstance(args, dict) else {},
        arguments_hash=r["arguments_hash"],
        resource=r.get("resource") or "",
        destination=r.get("destination") or "",
        reason=r.get("reason") or "",
        status=r["status"],
        expires_at=r["expires_at"],
        consumed_at=r.get("consumed_at"),
        created_at=r["created_at"],
        decided_at=r.get("decided_at"),
        decided_by=r.get("decided_by") or "system",
    )


@router.get("/approvals", response_model=ApprovalList)
def list_approvals(
    status: str = Query("pending", pattern="^(pending|approved|denied|expired|consumed|all)$"),
) -> ApprovalList:
    settings = get_settings()
    gateway = get_gateway(settings.sqlite_path)
    conn = get_connection(settings.sqlite_path)
    try:
        gateway.expire_stale_approvals(conn)
        if status == "all":
            rows = conn.execute("SELECT * FROM approvals ORDER BY created_at DESC LIMIT 200").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM approvals WHERE status = ? ORDER BY created_at DESC LIMIT 200", (status,)
            ).fetchall()
        approvals = [_to_response(r) for r in rows]
        return ApprovalList(approvals=approvals, count=len(approvals))
    finally:
        conn.close()


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
def get_approval(approval_id: str) -> ApprovalResponse:
    settings = get_settings()
    gateway = get_gateway(settings.sqlite_path)
    conn = get_connection(settings.sqlite_path)
    try:
        gateway.expire_stale_approvals(conn)
        row = conn.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Approval not found")
        return _to_response(row)
    finally:
        conn.close()


@router.post("/approvals/{approval_id}/decision", response_model=ApprovalResponse)
def decide_approval(approval_id: str, body: ApprovalDecision) -> ApprovalResponse:
    settings = get_settings()
    gateway = get_gateway(settings.sqlite_path)

    result = gateway.decide_approval(approval_id, body.decision)
    if result is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    if result["status"] not in ("approved", "denied") or (
        result["status"] != ("approved" if body.decision == "approve" else "denied")
    ):
        raise HTTPException(status_code=409, detail=f"Approval is already '{result['status']}' and cannot be changed")
    return _to_response(result)


@router.post("/approvals/{approval_id}/execute", response_model=ScenarioResult)
def execute_approved_action(approval_id: str) -> ScenarioResult:
    """Run the exact approved action through the gateway (single use).

    The action payload comes only from server-side approval state; the gateway
    re-checks status, expiry, argument hash and policy before the mock executor runs.
    """
    settings = get_settings()
    gateway = get_gateway(settings.sqlite_path)
    request = gateway.approved_action_request(approval_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return ScenarioResult(**run_proposal(
        gateway, "approved_action", "Approved action", request,
        f"Executing the action a human approved (approval {approval_id[:8]}).", source="approval",
    ))
