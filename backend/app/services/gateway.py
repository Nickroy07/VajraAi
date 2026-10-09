"""The ONE authoritative gateway service — all protected execution goes through here."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.policy_engine import canonical_json, evaluate
from app.tools.registry import get_tool, is_known_tool


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_arguments(arguments: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(arguments).encode()).hexdigest()


class GatewayService:
    """Single entry point for all protected tool execution."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        task_id: str,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        resource: str = "",
        destination: str = "",
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        """Authorize and (if allowed) execute a tool action.

        Returns a dict suitable for GatewayExecuteResponse.
        """
        event_id = str(uuid4())
        timestamp = _utcnow()

        # --- Step 1: Validate task exists ---
        conn = self._get_conn()
        try:
            task_row = conn.execute(
                "SELECT task_id, scope FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if not task_row:
                return self._build_denied_event(
                    conn, event_id, task_id, agent_id, tool_name, arguments,
                    resource, destination, timestamp,
                    reason="Task not found",
                )

            task_scope = json.loads(task_row["scope"])

            # --- Step 2: Load policy ---
            policy_row = conn.execute(
                "SELECT rules FROM policies WHERE task_id = ?", (task_id,)
            ).fetchone()
            if not policy_row:
                return self._build_denied_event(
                    conn, event_id, task_id, agent_id, tool_name, arguments,
                    resource, destination, timestamp,
                    reason="No policy found for this task",
                )
            policy_rules = json.loads(policy_row["rules"])

            # --- Step 3: Validate tool is known ---
            if not is_known_tool(tool_name):
                return self._build_denied_event(
                    conn, event_id, task_id, agent_id, tool_name, arguments,
                    resource, destination, timestamp,
                    reason=f"Unknown tool '{tool_name}' is not in the allowlisted registry",
                )

            # --- Step 4: Policy evaluation ---
            decision = evaluate(task_scope, policy_rules, tool_name, arguments, resource, destination)

            # Handle require_approval: need a valid approval
            if decision.requires_approval:
                if not approval_id:
                    return self._build_denied_event(
                        conn, event_id, task_id, agent_id, tool_name, arguments,
                        resource, destination, timestamp,
                        reason=f"Tool '{tool_name}' requires explicit approval — no approval_id provided",
                    )
                approval_check = self._validate_approval(
                    conn, approval_id, task_id, tool_name, arguments, resource, destination
                )
                if not approval_check["valid"]:
                    return self._build_denied_event(
                        conn, event_id, task_id, agent_id, tool_name, arguments,
                        resource, destination, timestamp,
                        reason=approval_check["reason"],
                    )
                # Consume the approval
                self._consume_approval(conn, approval_id)
                decision = type(decision)(allowed=True, requires_approval=False, reason="Approval validated and consumed")

            if not decision.allowed:
                return self._build_denied_event(
                    conn, event_id, task_id, agent_id, tool_name, arguments,
                    resource, destination, timestamp,
                    reason=decision.reason,
                )

            # --- Step 5: Execute ---
            tool = get_tool(tool_name)
            if tool is None:
                return self._build_denied_event(
                    conn, event_id, task_id, agent_id, tool_name, arguments,
                    resource, destination, timestamp,
                    reason=f"Tool '{tool_name}' not found in executor registry",
                )

            try:
                result = tool.execute(arguments)
                execution_status = "succeeded"
            except Exception as exc:
                result = f"Executor error: {exc}"
                execution_status = "failed"

            # Increment counter
            conn.execute(
                "INSERT INTO mock_executor_counters (tool_name, call_count) VALUES (?, 1) "
                "ON CONFLICT(tool_name) DO UPDATE SET call_count = call_count + 1",
                (tool_name,),
            )

            # Get current count
            count_row = conn.execute(
                "SELECT call_count FROM mock_executor_counters WHERE tool_name = ?", (tool_name,)
            ).fetchone()
            call_count = count_row["call_count"] if count_row else 1

            # --- Step 6: Persist event ---
            conn.execute(
                """INSERT INTO events
                   (event_id, task_id, agent_id, tool_name, event_type, authorization,
                    authorization_reason, execution_status, execution_result,
                    arguments, resource, destination, timestamp, details)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_id, task_id, agent_id, tool_name, "tool.executed",
                    "allowed", decision.reason, execution_status, result,
                    json.dumps(arguments), resource, destination, timestamp,
                    json.dumps({"mode": "demo", "approval_id": approval_id}),
                ),
            )
            conn.commit()

            return {
                "event_id": event_id,
                "task_id": task_id,
                "tool_name": tool_name,
                "authorization": "allowed",
                "authorization_reason": decision.reason,
                "execution_status": execution_status,
                "execution_result": result,
                "executor_call_count": call_count,
                "timestamp": timestamp,
            }

        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Approval helpers
    # ------------------------------------------------------------------

    def create_approval(
        self,
        task_id: str,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        resource: str = "",
        destination: str = "",
        reason: str = "",
        ttl_minutes: int = 15,
    ) -> dict[str, Any]:
        """Create a pending approval request."""
        conn = self._get_conn()
        try:
            approval_id = str(uuid4())
            now = _utcnow()
            expires_at = datetime.now(timezone.utc).timestamp() + (ttl_minutes * 60)
            expires_str = datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()
            args_hash = _hash_arguments(arguments)

            conn.execute(
                """INSERT INTO approvals
                   (approval_id, task_id, agent_id, tool_name, arguments_hash,
                    arguments, resource, destination, reason, status,
                    expires_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
                (
                    approval_id, task_id, agent_id, tool_name, args_hash,
                    json.dumps(arguments), resource, destination, reason,
                    expires_str, now,
                ),
            )
            conn.commit()

            return {
                "approval_id": approval_id,
                "task_id": task_id,
                "tool_name": tool_name,
                "arguments_hash": args_hash,
                "status": "pending",
                "expires_at": expires_str,
                "created_at": now,
            }
        finally:
            conn.close()

    def _validate_approval(
        self,
        conn: sqlite3.Connection,
        approval_id: str,
        task_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        resource: str,
        destination: str,
    ) -> dict[str, Any]:
        """Validate an approval server-side. Returns {valid: bool, reason: str}."""
        row = conn.execute(
            "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
        ).fetchone()
        if not row:
            return {"valid": False, "reason": "Approval not found"}

        # Check status
        status = row["status"]
        if status == "consumed":
            return {"valid": False, "reason": "Approval has already been consumed"}
        if status == "denied":
            return {"valid": False, "reason": "Approval was denied"}
        if status == "expired":
            return {"valid": False, "reason": "Approval has expired"}
        if status == "pending":
            return {"valid": False, "reason": "Approval is still pending — not yet decided"}

        if status != "approved":
            return {"valid": False, "reason": f"Approval status '{status}' is not valid for execution"}

        # Check expiry
        expires_at = row["expires_at"]
        if datetime.now(timezone.utc).isoformat() > expires_at:
            return {"valid": False, "reason": "Approval has expired"}

        # Check task match
        if row["task_id"] != task_id:
            return {"valid": False, "reason": "Approval task does not match execution task"}

        # Check tool match
        if row["tool_name"] != tool_name:
            return {"valid": False, "reason": "Approval tool does not match execution tool"}

        # Check arguments hash match
        actual_hash = _hash_arguments(arguments)
        if row["arguments_hash"] != actual_hash:
            return {"valid": False, "reason": "Approval arguments do not match execution arguments — action changed"}

        # Check resource/destination
        if row["resource"] != resource:
            return {"valid": False, "reason": "Approval resource does not match execution resource"}
        if row["destination"] != destination:
            return {"valid": False, "reason": "Approval destination does not match execution destination"}

        return {"valid": True, "reason": "Approval valid"}

    def _consume_approval(self, conn: sqlite3.Connection, approval_id: str) -> None:
        now = _utcnow()
        conn.execute(
            "UPDATE approvals SET status = 'consumed', consumed_at = ? WHERE approval_id = ?",
            (now, approval_id),
        )
        conn.commit()

    def decide_approval(self, approval_id: str, decision: str) -> dict[str, Any] | None:
        """Approve or deny a pending approval. Returns updated row or None."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
            ).fetchone()
            if not row:
                return None
            if row["status"] != "pending":
                return dict(row)

            new_status = "approved" if decision == "approve" else "denied"
            now = _utcnow()
            conn.execute(
                "UPDATE approvals SET status = ?, decided_at = ?, decided_by = ? WHERE approval_id = ?",
                (new_status, now, "system", approval_id),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
            ).fetchone()
            return dict(updated) if updated else None
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Event recording helper
    # ------------------------------------------------------------------

    def _build_denied_event(
        self,
        conn: sqlite3.Connection,
        event_id: str,
        task_id: str,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        resource: str,
        destination: str,
        timestamp: str,
        reason: str,
    ) -> dict[str, Any]:
        conn.execute(
            """INSERT INTO events
               (event_id, task_id, agent_id, tool_name, event_type, authorization,
                authorization_reason, execution_status, execution_result,
                arguments, resource, destination, timestamp, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'not_attempted', NULL, ?, ?, ?, ?, ?)""",
            (
                event_id, task_id, agent_id, tool_name, "tool.blocked",
                "denied", reason,
                json.dumps(arguments), resource, destination, timestamp,
                json.dumps({"mode": "demo"}),
            ),
        )
        conn.commit()
        return {
            "event_id": event_id,
            "task_id": task_id,
            "tool_name": tool_name,
            "authorization": "denied",
            "authorization_reason": reason,
            "execution_status": "not_attempted",
            "execution_result": None,
            "executor_call_count": 0,
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_overview(self) -> dict[str, Any]:
        conn = self._get_conn()
        try:
            active = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE status IN ('pending','running')"
            ).fetchone()[0]
            allowed = conn.execute(
                "SELECT COUNT(*) FROM events WHERE authorization = 'allowed'"
            ).fetchone()[0]
            blocked = conn.execute(
                "SELECT COUNT(*) FROM events WHERE authorization = 'denied'"
            ).fetchone()[0]
            pending_approvals = conn.execute(
                "SELECT COUNT(*) FROM approvals WHERE status = 'pending'"
            ).fetchone()[0]
            recent = conn.execute(
                "SELECT * FROM events ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
            return {
                "mode": "demo",
                "gateway_connected": True,
                "metrics": [
                    {"label": "Active Tasks", "value": active},
                    {"label": "Allowed", "value": allowed},
                    {"label": "Blocked", "value": blocked},
                    {"label": "Pending Approvals", "value": pending_approvals},
                ],
                "recent_events": [dict(r) for r in recent],
                "attention_items": (
                    ["DEMO ENVIRONMENT — Simulated protections only. Not connected to production AI agents."]
                ),
            }
        finally:
            conn.close()


# Singleton factory
_gateway: GatewayService | None = None


def get_gateway(sqlite_path: str) -> GatewayService:
    global _gateway
    if _gateway is None or _gateway.db_path != sqlite_path:
        _gateway = GatewayService(sqlite_path)
    return _gateway