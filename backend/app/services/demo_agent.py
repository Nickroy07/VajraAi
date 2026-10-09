"""Deterministic DEMO agent runner — sends a proposed action through the real gateway
and returns a step-by-step trace with a verified mock-executor call delta."""

from __future__ import annotations
from typing import Any

from app.services.gateway import GatewayService, safe_arguments

SEEDED_TASK_ID = "00000000-0000-0000-0000-000000000001"
APPROVAL_TASK_ID = "00000000-0000-0000-0000-000000000002"
SEEDED_AGENT_ID = "00000000-0000-0000-0000-000000000100"


def run_proposal(
    gateway: GatewayService,
    scenario_id: str,
    label: str,
    request: dict[str, Any],
    proposal_note: str,
    source: str,
) -> dict[str, Any]:
    tool = request["tool_name"]
    before = gateway.get_executor_count(tool)
    result = gateway.execute(**request, source=source)
    after = gateway.get_executor_count(tool)
    delta = after - before

    auth = result["authorization"]
    args_shown = ", ".join(f"{k}={v!r}" for k, v in safe_arguments(request["arguments"]).items())
    target = result["destination"] or result["resource"] or "—"
    trace = [
        {"stage": "Agent Proposal", "status": "info", "detail": f"{tool}({args_shown}). {proposal_note}"},
        {"stage": "Policy", "status": "info", "detail": f"Checked task scope, tool allowlist, resource and destination ({target})"},
        {"stage": "Decision", "status": auth, "detail": result["authorization_reason"]},
        {
            "stage": "Mock Executor",
            "status": "succeeded" if result["execution_status"] == "succeeded" else "skipped",
            "detail": (result["execution_result"] or "Not invoked") + f" — counter {before} → {after} (Δ {delta})",
        },
        {"stage": "Audit Event", "status": "info", "detail": f"Event {result['event_id']} persisted"},
    ]
    return {
        "scenario_id": scenario_id,
        "scenario_label": label,
        "final_authorization": auth,
        "authorization_reason": result["authorization_reason"],
        "execution_status": result["execution_status"],
        "executor_call_count": delta,
        "executor_calls_before": before,
        "executor_calls_after": after,
        "event_id": result["event_id"],
        "approval_id": result.get("approval_id"),
        "request": request,
        "trace": trace,
    }
