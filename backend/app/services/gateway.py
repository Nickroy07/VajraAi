"""The ONE authoritative gateway service — all protected execution goes through here."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.services.policy_engine import canonical_json, evaluate, policy_fingerprint
from app.tools.registry import get_tool, is_known_tool

APPROVAL_TTL_MINUTES = 10
EXECUTABLE_TASK_STATUSES = {"pending", "running"}
# Free-text arguments are summarized, never stored verbatim in events/approvals.
_FREE_TEXT_ARGS = {"body", "text", "content"}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_arguments(arguments: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(arguments).encode()).hexdigest()


def safe_arguments(arguments: Any) -> dict[str, Any]:
    """Redacted copy of arguments for persistence and display."""
    if not isinstance(arguments, dict):
        return {"_invalid": f"<{type(arguments).__name__}>"}
    safe: dict[str, Any] = {}
    for key, value in list(arguments.items())[:20]:
        key = str(key)[:64]
        if not isinstance(value, str):
            safe[key] = f"<{type(value).__name__}>"
        elif key in _FREE_TEXT_ARGS:
            safe[key] = f"[{len(value)} chars, sha256:{hashlib.sha256(value.encode()).hexdigest()[:10]}]"
        else:
            safe[key] = value if len(value) <= 160 else value[:159] + "…"
    return safe


def _parse_ts(value: str) -> datetime | None:
    try:
        ts = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


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
        source: str = "api",
    ) -> dict[str, Any]:
        """Authorize and (if allowed) execute a tool action.

        Every outcome — allowed, denied, or pending approval — is persisted as an
        event before returning. The executor is only reached on the allowed path.
        """
        ctx = {
            "event_id": str(uuid4()),
            "timestamp": _utcnow(),
            "task_id": task_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "resource": resource,
            "destination": destination,
            "source": source,
            "approval_id": approval_id,
        }

        conn = self._get_conn()
        try:
            task_row = conn.execute(
                "SELECT task_id, scope, status FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if not task_row:
                return self._deny(conn, ctx, "Task not found")
            if task_row["status"] not in EXECUTABLE_TASK_STATUSES:
                return self._deny(conn, ctx, f"Task is '{task_row['status']}' and cannot run actions")

            agent_row = conn.execute(
                "SELECT status FROM agents WHERE agent_id = ?", (agent_id,)
            ).fetchone()
            if not agent_row:
                return self._deny(conn, ctx, "Agent is not registered")
            if agent_row["status"] != "connected":
                return self._deny(conn, ctx, "Agent is not connected")

            policy_row = conn.execute(
                "SELECT rules FROM policies WHERE task_id = ?", (task_id,)
            ).fetchone()
            if not policy_row:
                return self._deny(conn, ctx, "No policy found for this task")

            try:
                task_scope = json.loads(task_row["scope"])
                policy_rules = json.loads(policy_row["rules"])
                if not isinstance(task_scope, dict) or not isinstance(policy_rules, list):
                    raise ValueError
            except ValueError:
                return self._deny(conn, ctx, "Task scope or policy is malformed")

            if not is_known_tool(tool_name):
                return self._deny(conn, ctx, f"Unknown tool '{tool_name}' is not in the allowlisted registry")

            decision = evaluate(task_scope, policy_rules, tool_name, arguments, resource, destination)
            ctx["resource"], ctx["destination"] = decision.resource or resource, decision.destination or destination
            fingerprint = policy_fingerprint(task_scope, policy_rules)

            if decision.requires_approval:
                if not approval_id:
                    return self._request_approval(conn, ctx, decision.reason, fingerprint)
                check = self._validate_approval(conn, ctx, fingerprint)
                if not check["valid"]:
                    return self._deny(conn, ctx, check["reason"])
                # Atomic single use: only one request can flip approved → consumed.
                consumed = conn.execute(
                    "UPDATE approvals SET status = 'consumed', consumed_at = ?, action_payload = NULL "
                    "WHERE approval_id = ? AND status = 'approved' AND expires_at > ?",
                    (_utcnow(), approval_id, _utcnow()),
                ).rowcount
                conn.commit()
                if consumed != 1:
                    return self._deny(conn, ctx, "Approval has already been consumed or has expired")
                reason = f"Human approval {approval_id[:8]} validated for this exact action and consumed"
            elif not decision.allowed:
                return self._deny(conn, ctx, decision.reason)
            else:
                if approval_id:
                    return self._deny(conn, ctx, "An approval was supplied for an action that does not require one")
                reason = decision.reason

            tool = get_tool(tool_name)
            if tool is None:
                return self._deny(conn, ctx, f"Tool '{tool_name}' not found in executor registry")
            return self._run_executor(conn, ctx, tool, reason)
        finally:
            conn.close()

    def _run_executor(self, conn: sqlite3.Connection, ctx: dict[str, Any], tool, reason: str) -> dict[str, Any]:
        # The counter is incremented in the same place the executor is invoked,
        # so it measures real mock-executor calls.
        conn.execute(
            "INSERT INTO mock_executor_counters (tool_name, call_count) VALUES (?, 1) "
            "ON CONFLICT(tool_name) DO UPDATE SET call_count = call_count + 1",
            (ctx["tool_name"],),
        )
        try:
            result = tool.execute(ctx["arguments"])
            execution_status = "succeeded"
        except Exception as exc:  # pragma: no cover - mock tools do not raise
            result = f"Executor error: {exc.__class__.__name__}"
            execution_status = "failed"
        self._record(conn, ctx, "tool.executed", "allowed", reason, execution_status, result)
        return self._response(ctx, "allowed", reason, execution_status, result, executor_calls=1)

    # ------------------------------------------------------------------
    # Approval helpers
    # ------------------------------------------------------------------

    def _request_approval(self, conn: sqlite3.Connection, ctx: dict[str, Any], reason: str, fingerprint: str) -> dict[str, Any]:
        approval = self._insert_approval(conn, ctx, reason, fingerprint, APPROVAL_TTL_MINUTES)
        ctx["approval_id"] = approval["approval_id"]
        message = f"{reason}. Pending approval {approval['approval_id'][:8]} expires {approval['expires_at']}"
        self._record(conn, ctx, "approval.requested", "pending", message, "not_attempted", None)
        resp = self._response(ctx, "pending_approval", message, "not_attempted", None, executor_calls=0)
        resp["approval_id"] = approval["approval_id"]
        return resp

    def _insert_approval(self, conn, ctx, reason, fingerprint, ttl_minutes) -> dict[str, Any]:
        approval_id = str(uuid4())
        now = datetime.now(timezone.utc)
        expires_str = (now + timedelta(minutes=ttl_minutes)).isoformat()
        conn.execute(
            """INSERT INTO approvals
               (approval_id, task_id, agent_id, tool_name, arguments_hash,
                arguments, resource, destination, reason, status,
                expires_at, created_at, policy_hash, action_payload)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
            (
                approval_id, ctx["task_id"], ctx["agent_id"], ctx["tool_name"],
                _hash_arguments(ctx["arguments"]), json.dumps(safe_arguments(ctx["arguments"])),
                ctx["resource"], ctx["destination"], reason, expires_str, now.isoformat(), fingerprint,
                canonical_json(ctx["arguments"]),
            ),
        )
        conn.commit()
        return {"approval_id": approval_id, "expires_at": expires_str, "created_at": now.isoformat()}

    def create_approval(
        self,
        task_id: str,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        resource: str = "",
        destination: str = "",
        reason: str = "",
        ttl_minutes: int = APPROVAL_TTL_MINUTES,
    ) -> dict[str, Any]:
        """Create a pending approval bound to the task's current policy (used by tests/tools)."""
        conn = self._get_conn()
        try:
            task_row = conn.execute("SELECT scope FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            policy_row = conn.execute("SELECT rules FROM policies WHERE task_id = ?", (task_id,)).fetchone()
            fingerprint = ""
            if task_row and policy_row:
                fingerprint = policy_fingerprint(json.loads(task_row["scope"]), json.loads(policy_row["rules"]))
            ctx = {
                "task_id": task_id, "agent_id": agent_id, "tool_name": tool_name,
                "arguments": arguments, "resource": resource, "destination": destination,
            }
            approval = self._insert_approval(conn, ctx, reason, fingerprint, ttl_minutes)
            return {
                **approval,
                "task_id": task_id,
                "tool_name": tool_name,
                "arguments_hash": _hash_arguments(arguments),
                "status": "pending",
            }
        finally:
            conn.close()

    def _validate_approval(self, conn: sqlite3.Connection, ctx: dict[str, Any], fingerprint: str) -> dict[str, Any]:
        """Validate an approval server-side against the exact request and current policy."""
        row = conn.execute(
            "SELECT * FROM approvals WHERE approval_id = ?", (ctx["approval_id"],)
        ).fetchone()
        if not row:
            return {"valid": False, "reason": "Approval not found"}

        expires_at = _parse_ts(row["expires_at"])
        if row["status"] in ("pending", "approved") and (expires_at is None or datetime.now(timezone.utc) >= expires_at):
            conn.execute("UPDATE approvals SET status = 'expired', action_payload = NULL WHERE approval_id = ?", (row["approval_id"],))
            conn.commit()
            return {"valid": False, "reason": "Approval has expired"}

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

        if row["task_id"] != ctx["task_id"]:
            return {"valid": False, "reason": "Approval task does not match execution task"}
        if (row["agent_id"] or "") != ctx["agent_id"]:
            return {"valid": False, "reason": "Approval agent does not match requesting agent"}
        if row["tool_name"] != ctx["tool_name"]:
            return {"valid": False, "reason": "Approval tool does not match execution tool"}
        if row["arguments_hash"] != _hash_arguments(ctx["arguments"]):
            return {"valid": False, "reason": "Approval arguments do not match execution arguments — action changed"}
        if row["resource"] != ctx["resource"]:
            return {"valid": False, "reason": "Approval resource does not match execution resource"}
        if row["destination"] != ctx["destination"]:
            return {"valid": False, "reason": "Approval destination does not match execution destination"}
        if row["policy_hash"] != fingerprint:
            return {"valid": False, "reason": "Task policy changed since this approval was granted"}
        return {"valid": True, "reason": "Approval valid"}

    def expire_stale_approvals(self, conn: sqlite3.Connection) -> None:
        now = datetime.now(timezone.utc)
        rows = conn.execute(
            "SELECT approval_id, expires_at FROM approvals WHERE status IN ('pending','approved')"
        ).fetchall()
        for r in rows:
            ts = _parse_ts(r["expires_at"])
            if ts is None or now >= ts:
                conn.execute("UPDATE approvals SET status = 'expired', action_payload = NULL WHERE approval_id = ?", (r["approval_id"],))
        conn.commit()

    def decide_approval(self, approval_id: str, decision: str, decided_by: str = "operator") -> dict[str, Any] | None:
        """Approve or deny a pending approval. Returns updated row or None."""
        conn = self._get_conn()
        try:
            self.expire_stale_approvals(conn)
            row = conn.execute(
                "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
            ).fetchone()
            if not row:
                return None
            if row["status"] != "pending":
                return dict(row)

            if decision not in ("approve", "deny"):
                return dict(row)
            new_status = "approved" if decision == "approve" else "denied"
            conn.execute(
                "UPDATE approvals SET status = ?, decided_at = ?, decided_by = ?, "
                "action_payload = CASE WHEN ? = 'denied' THEN NULL ELSE action_payload END "
                "WHERE approval_id = ? AND status = 'pending'",
                (new_status, _utcnow(), decided_by, new_status, approval_id),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)
            ).fetchone()
            return dict(updated) if updated else None
        finally:
            conn.close()

    def approved_action_request(self, approval_id: str) -> dict[str, Any] | None:
        """Rebuild the exact gateway request bound to an approval from server-side state.

        Clients never supply the payload, so an approver cannot alter the action. The
        gateway re-validates everything (status, expiry, hash, policy) on execution.
        """
        conn = self._get_conn()
        try:
            self.expire_stale_approvals(conn)
            row = conn.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)).fetchone()
        finally:
            conn.close()
        if not row:
            return None
        try:
            arguments = json.loads(row["action_payload"]) if row["action_payload"] else json.loads(row["arguments"])
        except ValueError:
            arguments = {}
        return {
            "task_id": row["task_id"],
            "agent_id": row["agent_id"] or "",
            "tool_name": row["tool_name"],
            "arguments": arguments,
            "resource": row["resource"],
            "destination": row["destination"],
            "approval_id": approval_id,
        }

    # ------------------------------------------------------------------
    # Event recording helpers
    # ------------------------------------------------------------------

    def _record(self, conn, ctx, event_type, authorization, reason, execution_status, result) -> None:
        conn.execute(
            """INSERT INTO events
               (event_id, task_id, agent_id, tool_name, event_type, authorization,
                authorization_reason, execution_status, execution_result,
                arguments, resource, destination, timestamp, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ctx["event_id"], ctx["task_id"], ctx["agent_id"], str(ctx["tool_name"])[:100], event_type,
                authorization, reason, execution_status, result,
                json.dumps(safe_arguments(ctx["arguments"])), str(ctx["resource"])[:300], str(ctx["destination"])[:300],
                ctx["timestamp"],
                json.dumps({"mode": "demo", "source": ctx["source"], "approval_id": ctx.get("approval_id")}),
            ),
        )
        conn.commit()

    def _deny(self, conn: sqlite3.Connection, ctx: dict[str, Any], reason: str) -> dict[str, Any]:
        self._record(conn, ctx, "tool.blocked", "denied", reason, "not_attempted", None)
        return self._response(ctx, "denied", reason, "not_attempted", None, executor_calls=0)

    @staticmethod
    def _response(ctx, authorization, reason, execution_status, result, executor_calls) -> dict[str, Any]:
        return {
            "event_id": ctx["event_id"],
            "task_id": ctx["task_id"],
            "tool_name": ctx["tool_name"],
            "authorization": authorization,
            "authorization_reason": reason,
            "execution_status": execution_status,
            "execution_result": result,
            "executor_call_count": executor_calls,
            "resource": ctx["resource"],
            "destination": ctx["destination"],
            "approval_id": ctx.get("approval_id"),
            "timestamp": ctx["timestamp"],
        }

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_executor_count(self, tool_name: str) -> int:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT call_count FROM mock_executor_counters WHERE tool_name = ?", (tool_name,)
            ).fetchone()
            return row["call_count"] if row else 0
        finally:
            conn.close()

    def get_overview(self) -> dict[str, Any]:
        conn = self._get_conn()
        try:
            self.expire_stale_approvals(conn)
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
            active_task = conn.execute(
                "SELECT task_id, description, status FROM tasks WHERE status IN ('pending','running') "
                "ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            last_lab = conn.execute(
                "SELECT * FROM events WHERE json_extract(details, '$.source') = 'attack_lab' "
                "ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            executor_total = conn.execute(
                "SELECT COALESCE(SUM(call_count), 0) FROM mock_executor_counters"
            ).fetchone()[0]

            def _event(r: sqlite3.Row) -> dict[str, Any]:
                d = dict(r)
                d["arguments"] = json.loads(d.get("arguments") or "{}")
                d["details"] = json.loads(d.get("details") or "{}")
                return d

            return {
                "mode": "demo",
                "gateway_connected": True,
                "metrics": [
                    {"label": "Active Tasks", "value": active},
                    {"label": "Allowed", "value": allowed},
                    {"label": "Blocked", "value": blocked},
                    {"label": "Pending Approvals", "value": pending_approvals},
                ],
                "recent_events": [_event(r) for r in recent],
                "active_task": dict(active_task) if active_task else None,
                "last_attack_lab_event": _event(last_lab) if last_lab else None,
                "executor_calls_total": executor_total,
                "attention_items": (
                    ["DEMO ENVIRONMENT — mock tools only. Protection applies to actions sent through this gateway, not to third-party AI apps."]
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
