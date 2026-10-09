"""Approval routes — list pending and decide."""

import json

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.database.init_db import get_connection
from app.schemas.approval import ApprovalDecision, ApprovalList, ApprovalResponse
from app.services.gateway import get_gateway

router = APIRouter(prefix="/api/v1", tags=["approvals"])


@router.get("/approvals", response_model=ApprovalList)
def list_approvals(status: str = "pending") -> ApprovalList:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    try:
        if status == "all":
            rows = conn.execute(
                "SELECT * FROM approvals ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM approvals WHERE status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
        approvals = []
        for r in rows:
            args_raw = r["arguments"]
            args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            approvals.append(ApprovalResponse(
                approval_id=r["approval_id"],
                task_id=r["task_id"],
                agent_id=r["agent_id"],
                tool_name=r["tool_name"],
                arguments=args if isinstance(args, dict) else {},
                arguments_hash=r["arguments_hash"],
                resource=r["resource"] or "",
                destination=r["destination"] or "",
                reason=r["reason"] or "",
                status=r["status"],
                expires_at=r["expires_at"],
                consumed_at=r["consumed_at"],
                created_at=r["created_at"],
                decided_at=r["decided_at"],
                decided_by=r["decided_by"] or "system",
            ))
        return ApprovalList(approvals=approvals, count=len(approvals))
    finally:
        conn.close()


@router.post("/approvals/{approval_id}/decision", response_model=ApprovalResponse)
def decide_approval(approval_id: str, body: ApprovalDecision) -> ApprovalResponse:
    settings = get_settings()
    gateway = get_gateway(settings.sqlite_path)

    result = gateway.decide_approval(approval_id, body.decision)
    if result is None:
        raise HTTPException(status_code=404, detail="Approval not found")

    return ApprovalResponse(
        approval_id=result["approval_id"],
        task_id=result["task_id"],
        agent_id=result.get("agent_id"),
        tool_name=result["tool_name"],
        arguments=json.loads(result["arguments"]) if isinstance(result["arguments"], str) else (result["arguments"] if isinstance(result["arguments"], dict) else {}),
        arguments_hash=result["arguments_hash"],
        resource=result.get("resource", ""),
        destination=result.get("destination", ""),
        reason=result.get("reason", ""),
        status=result["status"],
        expires_at=result["expires_at"],
        consumed_at=result.get("consumed_at"),
        created_at=result["created_at"],
        decided_at=result.get("decided_at"),
        decided_by=result.get("decided_by", "system"),
    )