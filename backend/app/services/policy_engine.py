"""Policy evaluation engine — default-deny, task-scoped, server-side only."""

from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from app.tools.registry import get_tool

MAX_ARGUMENT_LENGTH = 4000
_EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9\-]+(\.[a-z0-9\-]+)+$")


@dataclass
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    resource: str = ""
    destination: str = ""


def _deny(reason: str, resource: str = "", destination: str = "") -> PolicyDecision:
    return PolicyDecision(False, False, reason, resource, destination)


def normalize_email(value: str) -> str | None:
    """Lower-case and validate an email address. Returns None if not a single, plain address."""
    candidate = value.strip().lower()
    if not _EMAIL_RE.match(candidate) or ".." in candidate:
        return None
    return candidate


def destination_in_allowlist(destination: str, allowlist: list[str]) -> bool:
    """Exact recipient or exact domain match. No suffix/substring matching.

    Entries: "user@example.com" (exact recipient) or "@example.com" / "example.com"
    (exact domain; subdomains and lookalikes such as example.com.evil.io do not match).
    """
    domain = destination.split("@", 1)[1]
    for raw in allowlist:
        entry = str(raw).strip().lower()
        if not entry:
            continue
        if "@" in entry and not entry.startswith("@"):
            if normalize_email(entry) == destination:
                return True
        elif entry.lstrip("@") == domain:
            return True
    return False


def _validate_arguments(spec, arguments: dict[str, Any]) -> str | None:
    if not isinstance(arguments, dict):
        return "Arguments must be an object"
    unknown = set(arguments) - spec.allowed_args
    if unknown:
        return f"Unexpected argument(s) for '{spec.name}': {', '.join(sorted(unknown))}"
    for name in spec.required_args:
        value = arguments.get(name)
        if not isinstance(value, str) or not value.strip():
            return f"Missing or empty required argument '{name}' for '{spec.name}'"
    for name, value in arguments.items():
        if not isinstance(value, str):
            return f"Argument '{name}' must be a string"
        if len(value) > MAX_ARGUMENT_LENGTH:
            return f"Argument '{name}' exceeds {MAX_ARGUMENT_LENGTH} characters"
    return None


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
    2. Arguments must match the tool's schema
    3. Task scope: tool must be in a non-empty allowed_tools list
    4. Resource: derived from the tool argument; must agree with any supplied
       label, and must be in scope when the task defines resources
    5. Destination: derived from the tool argument (e.g. email "to"); a
       conflicting top-level destination is denied; external destinations
       must match the allowlist exactly when blocking is on
    6. Policy rules: first rule for the tool decides; unknown action → deny
    7. Default: deny
    """

    # 1. Unknown tool
    spec = get_tool(tool_name)
    if spec is None:
        return _deny(f"Unknown tool '{tool_name}' is not in the allowlisted registry")

    # 2. Argument schema
    arg_error = _validate_arguments(spec, arguments)
    if arg_error:
        return _deny(arg_error)

    allowed_tools = task_scope.get("allowed_tools") or []
    resources = task_scope.get("resources") or []
    destination_allowlist = task_scope.get("destination_allowlist") or []
    block_external = bool(task_scope.get("block_external_destinations", False))

    # 3. Tool not in task scope (an empty list grants nothing)
    if tool_name not in allowed_tools:
        return _deny(f"Tool '{tool_name}' is not in the task's allowed_tools scope")

    # 4. Resource — the argument the executor will act on is authoritative
    supplied_resource = (resource or "").strip()
    arg_resource = (arguments.get(spec.resource_arg) or "").strip() if spec.resource_arg else ""
    if arg_resource and supplied_resource and arg_resource != supplied_resource:
        return _deny(
            f"Declared resource '{supplied_resource}' conflicts with tool argument "
            f"'{spec.resource_arg}' ('{arg_resource}')"
        )
    effective_resource = arg_resource or supplied_resource
    if resources:
        if not effective_resource:
            return _deny("Task restricts resources but the action names no resource")
        if effective_resource not in resources:
            return _deny(
                f"Resource '{effective_resource}' is not in the task's allowed resources",
                effective_resource,
            )

    # 5. Destination — derived from tool arguments, never trusted from the caller alone
    supplied_destination = (destination or "").strip()
    effective_destination = ""
    if spec.destination_arg:
        normalized = normalize_email(arguments[spec.destination_arg])
        if normalized is None:
            return _deny(f"Recipient '{arguments[spec.destination_arg]}' is not a valid single email address", effective_resource)
        if supplied_destination and normalize_email(supplied_destination) != normalized:
            return _deny(
                f"Declared destination '{supplied_destination}' conflicts with the actual recipient '{normalized}'",
                effective_resource,
                normalized,
            )
        effective_destination = normalized
        if block_external or destination_allowlist:
            if not destination_in_allowlist(normalized, destination_allowlist):
                return _deny(
                    f"External destination '{normalized}' is not on this task's destination allowlist",
                    effective_resource,
                    normalized,
                )
    elif supplied_destination:
        return _deny(f"Tool '{tool_name}' does not send data anywhere; unexpected destination supplied", effective_resource)

    # 6. Policy rules — first rule naming the tool decides
    for rule in policy_rules:
        if rule.get("tool") != tool_name:
            continue
        action = rule.get("action")
        desc = rule.get("description", "")
        if action == "allow":
            return PolicyDecision(True, False, desc or f"Tool '{tool_name}' is allowed by policy", effective_resource, effective_destination)
        if action == "require_approval":
            return PolicyDecision(False, True, desc or f"Tool '{tool_name}' requires explicit approval", effective_resource, effective_destination)
        return _deny(desc or f"Tool '{tool_name}' is denied by policy", effective_resource, effective_destination)

    # 7. Default deny
    return _deny(f"No matching policy rule for tool '{tool_name}' — default deny", effective_resource, effective_destination)


def canonical_json(obj: Any) -> str:
    """Produce deterministic sorted JSON for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def policy_fingerprint(task_scope: dict[str, Any], policy_rules: list[dict[str, Any]]) -> str:
    """Hash of the scope + rules an approval was granted under."""
    return hashlib.sha256(canonical_json({"scope": task_scope, "rules": policy_rules}).encode()).hexdigest()
