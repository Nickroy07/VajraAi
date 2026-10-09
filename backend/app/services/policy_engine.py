"""Policy evaluation engine — default-deny, task-scoped, server-side only."""

from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any

from app.tools.registry import is_known_tool


@dataclass
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str


def evaluate(
    task_scope: dict[str, Any],
    policy_rules: list[dict[str, Any]],
    tool_name: str,
    arguments: dict[str, Any],
    resource: str,
    destination: str,
) -> PolicyDecision:
    """Evaluate a tool action against task scope and policy rules.

    Order of checks (first failure wins, default-deny):
    1. Unknown tool → deny
    2. Task scope: tool in allowed_tools?
    3. Task scope: resource in resources? (if task has resources defined)
    4. Task scope: external destination blocked?
    5. Policy rules: explicit allow/deny/require_approval per tool
    6. Default: deny
    """

    # 1. Unknown tool
    if not is_known_tool(tool_name):
        return PolicyDecision(
            allowed=False,
            requires_approval=False,
            reason=f"Unknown tool '{tool_name}' is not in the allowlisted registry",
        )

    allowed_tools: list[str] = task_scope.get("allowed_tools", [])
    resources: list[str] = task_scope.get("resources", [])
    destination_allowlist: list[str] = task_scope.get("destination_allowlist", [])
    block_external: bool = task_scope.get("block_external_destinations", False)

    # 2. Tool not in task scope
    if allowed_tools and tool_name not in allowed_tools:
        return PolicyDecision(
            allowed=False,
            requires_approval=False,
            reason=f"Tool '{tool_name}' is not in the task's allowed_tools scope",
        )

    # 3. Resource check
    if resources and resource and resource not in resources:
        return PolicyDecision(
            allowed=False,
            requires_approval=False,
            reason=f"Resource '{resource}' is not in the task's allowed resources",
        )

    # 4. External destination check
    if block_external and destination:
        is_external = True
        for allowed_dest in destination_allowlist:
            if destination == allowed_dest or destination.endswith("@" + allowed_dest.split("@")[-1] if "@" in allowed_dest else False):
                is_external = False
                break
        if is_external and destination_allowlist:
            return PolicyDecision(
                allowed=False,
                requires_approval=False,
                reason=f"External destination '{destination}' is not permitted for this task",
            )

    # 5. Check policy rules for this tool
    for rule in policy_rules:
        if rule.get("tool") == tool_name:
            action = rule.get("action", "deny")
            desc = rule.get("description", "")
            if action == "deny":
                return PolicyDecision(
                    allowed=False,
                    requires_approval=False,
                    reason=desc or f"Tool '{tool_name}' is denied by policy",
                )
            elif action == "require_approval":
                return PolicyDecision(
                    allowed=False,
                    requires_approval=True,
                    reason=desc or f"Tool '{tool_name}' requires explicit approval",
                )
            elif action == "allow":
                return PolicyDecision(
                    allowed=True,
                    requires_approval=False,
                    reason=desc or f"Tool '{tool_name}' is allowed by policy",
                )

    # 6. Default deny
    return PolicyDecision(
        allowed=False,
        requires_approval=False,
        reason=f"No matching policy rule for tool '{tool_name}' — default deny",
    )


def canonical_json(obj: dict[str, Any]) -> str:
    """Produce deterministic sorted JSON for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)