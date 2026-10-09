"""Gateway execute route — the ONE entry point for protected tool execution."""

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.gateway import GatewayExecuteRequest, GatewayExecuteResponse
from app.services.gateway import get_gateway

router = APIRouter(prefix="/api/v1", tags=["gateway"])


@router.post("/gateway/execute", response_model=GatewayExecuteResponse)
def gateway_execute(body: GatewayExecuteRequest) -> GatewayExecuteResponse:
    """Authorize and execute a tool action through the security gateway.

    All execution goes through this single endpoint — agents/UI must not
    call executors directly. Re-validates policy and approval server-side.
    """
    settings = get_settings()
    gateway = get_gateway(settings.sqlite_path)

    if body.arguments is None:
        raise HTTPException(status_code=400, detail="arguments must not be null")

    result = gateway.execute(
        task_id=body.task_id,
        agent_id=body.agent_id,
        tool_name=body.tool_name,
        arguments=body.arguments,
        resource=body.resource,
        destination=body.destination,
        approval_id=body.approval_id,
    )

    return GatewayExecuteResponse(**result)