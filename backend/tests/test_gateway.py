"""Comprehensive tests for the VAJRA AI Gateway backend.

Run: cd backend && pytest -q
"""

import json
import tempfile
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Point SQLite to a temp file before importing app
os.environ["SQLITE_PATH"] = os.path.join(tempfile.gettempdir(), "vajra_test.db")

from app.main import app
from app.database.init_db import initialize_sqlite, get_connection
from app.services.gateway import GatewayService

SEEDED_TASK_ID = "00000000-0000-0000-0000-000000000001"
SEEDED_AGENT_ID = "00000000-0000-0000-0000-000000000100"


@pytest.fixture
def client():
    """Fresh TestClient with temporary SQLite."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["SQLITE_PATH"] = db_path
    initialize_sqlite(db_path)
    # Force new gateway instance
    from app.services.gateway import _gateway
    import app.services.gateway as gw_mod
    gw_mod._gateway = None

    with TestClient(app) as c:
        yield c

    try:
        os.unlink(db_path)
    except OSError:
        pass


def _reset_counters(db_path: str) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute("UPDATE mock_executor_counters SET call_count = 0")
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "timestamp" in body


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def test_overview_shows_demo_mode(client):
    r = client.get("/api/v1/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo"
    assert len(body["metrics"]) == 4
    labels = {m["label"] for m in body["metrics"]}
    assert "Active Tasks" in labels
    assert "Blocked" in labels


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def test_list_tasks_returns_seeded(client):
    r = client.get("/api/v1/tasks")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any(t["task_id"] == SEEDED_TASK_ID for t in body["tasks"])


def test_get_task_not_found(client):
    r = client.get("/api/v1/tasks/nonexistent")
    assert r.status_code == 404


def test_create_and_get_task(client):
    r = client.post("/api/v1/tasks", json={
        "description": "Test task",
        "status": "pending",
        "scope": {"allowed_tools": ["read_assigned_invoice"], "resources": ["res-1"]},
    })
    assert r.status_code == 201
    tid = r.json()["task_id"]
    r2 = client.get(f"/api/v1/tasks/{tid}")
    assert r2.status_code == 200
    assert r2.json()["description"] == "Test task"


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

def test_list_agents(client):
    r = client.get("/api/v1/agents")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 2


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

def test_get_policy(client):
    r = client.get(f"/api/v1/tasks/{SEEDED_TASK_ID}/policy")
    assert r.status_code == 200
    body = r.json()
    assert len(body["rules"]) >= 2


def test_update_policy(client):
    r = client.put(f"/api/v1/tasks/{SEEDED_TASK_ID}/policy", json={
        "rules": [
            {"tool": "read_assigned_invoice", "action": "allow", "description": "Allow reads"},
            {"tool": "send_external_email", "action": "deny", "description": "Deny email"},
        ]
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["rules"]) == 2


def test_policy_task_not_found(client):
    r = client.get("/api/v1/tasks/nonexistent/policy")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Gateway: Authorized Invoice Read (allowed → executor called once)
# ---------------------------------------------------------------------------

def test_gateway_authorized_invoice_read_allowed(client):
    _reset_counters(os.environ["SQLITE_PATH"])
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": SEEDED_TASK_ID,
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": "read_assigned_invoice",
        "arguments": {"invoice_id": "invoice-42"},
        "resource": "invoice-42",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["authorization"] == "allowed"
    assert body["execution_status"] == "succeeded"
    assert body["executor_call_count"] >= 1
    assert body["event_id"] is not None


# ---------------------------------------------------------------------------
# Gateway: External email denied (executor count stays zero)
# ---------------------------------------------------------------------------

def test_gateway_external_email_denied(client):
    _reset_counters(os.environ["SQLITE_PATH"])
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": SEEDED_TASK_ID,
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": "send_external_email",
        "arguments": {"to": "external@example.com", "subject": "Test"},
        "resource": "invoice-42",
        "destination": "external@example.com",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["authorization"] == "denied"
    assert body["execution_status"] == "not_attempted"
    assert body["executor_call_count"] == 0


# ---------------------------------------------------------------------------
# Gateway: File delete denied
# ---------------------------------------------------------------------------

def test_gateway_file_delete_denied(client):
    _reset_counters(os.environ["SQLITE_PATH"])
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": SEEDED_TASK_ID,
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": "delete_file",
        "arguments": {"path": "/etc/critical/config.yaml"},
        "resource": "/etc/critical/config.yaml",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["authorization"] == "denied"
    assert body["execution_status"] == "not_attempted"
    assert body["executor_call_count"] == 0


# ---------------------------------------------------------------------------
# Gateway: Unknown tool denied
# ---------------------------------------------------------------------------

def test_gateway_unknown_tool_denied(client):
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": SEEDED_TASK_ID,
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": "sudo_rm_rf",
        "arguments": {"path": "/"},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["authorization"] == "denied"
    assert "Unknown tool" in body["authorization_reason"]


# ---------------------------------------------------------------------------
# Gateway: Missing task denied
# ---------------------------------------------------------------------------

def test_gateway_missing_task_denied(client):
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": "nonexistent-task",
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": "read_assigned_invoice",
        "arguments": {},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["authorization"] == "denied"
    assert "Task not found" in body["authorization_reason"]


# ---------------------------------------------------------------------------
# Gateway: Out-of-scope resource denied
# ---------------------------------------------------------------------------

def test_gateway_out_of_scope_resource_denied(client):
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": SEEDED_TASK_ID,
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": "read_assigned_invoice",
        "arguments": {"invoice_id": "invoice-99"},
        "resource": "invoice-99",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["authorization"] == "denied"
    assert "not in the task's allowed resources" in body["authorization_reason"].lower()


# ---------------------------------------------------------------------------
# Approvals: create, approve, execute, reject changed/reused/expired
# ---------------------------------------------------------------------------

def _create_task_with_scope(client, allowed_tools: list[str], resources: list[str] | None = None):
    """Helper: create a task and policy for approval tests."""
    r = client.post("/api/v1/tasks", json={
        "description": "Approval test task",
        "status": "running",
        "scope": {
            "allowed_tools": allowed_tools,
            "resources": resources or ["/tmp/test.txt", "/tmp/test2.txt", "/tmp/original.txt"],
        },
    })
    assert r.status_code == 201
    tid = r.json()["task_id"]

    rules = []
    for t in allowed_tools:
        if t == "delete_file":
            rules.append({"tool": t, "action": "require_approval", "description": "Needs approval"})
        else:
            rules.append({"tool": t, "action": "allow", "description": f"Allow {t}"})
    client.put(f"/api/v1/tasks/{tid}/policy", json={"rules": rules})
    return tid


TEST_AGENT_ID = "00000000-0000-0000-0000-000000000100"


def test_approval_require_approval_flow(client):
    tid = _create_task_with_scope(client, ["read_assigned_invoice", "delete_file"])

    gw = GatewayService(os.environ["SQLITE_PATH"])
    approval = gw.create_approval(
        task_id=tid, agent_id=TEST_AGENT_ID,
        tool_name="delete_file",
        arguments={"path": "/tmp/test.txt"},
        resource="/tmp/test.txt",
        reason="Need to delete temp file",
    )
    result = gw.decide_approval(approval["approval_id"], "approve")
    assert result["status"] == "approved"

    _reset_counters(os.environ["SQLITE_PATH"])
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": tid, "agent_id": TEST_AGENT_ID,
        "tool_name": "delete_file",
        "arguments": {"path": "/tmp/test.txt"},
        "resource": "/tmp/test.txt",
        "approval_id": approval["approval_id"],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["authorization"] == "allowed", f"Expected allowed, got: {body}"
    assert body["execution_status"] == "succeeded"
    assert body["executor_call_count"] >= 1


def test_approval_reused_rejected(client):
    tid = _create_task_with_scope(client, ["read_assigned_invoice", "delete_file"])

    gw = GatewayService(os.environ["SQLITE_PATH"])
    approval = gw.create_approval(
        task_id=tid, agent_id=TEST_AGENT_ID,
        tool_name="delete_file",
        arguments={"path": "/tmp/test2.txt"},
        resource="/tmp/test2.txt",
    )
    gw.decide_approval(approval["approval_id"], "approve")

    _reset_counters(os.environ["SQLITE_PATH"])
    r1 = client.post("/api/v1/gateway/execute", json={
        "task_id": tid, "agent_id": TEST_AGENT_ID,
        "tool_name": "delete_file",
        "arguments": {"path": "/tmp/test2.txt"},
        "resource": "/tmp/test2.txt",
        "approval_id": approval["approval_id"],
    })
    assert r1.json()["authorization"] == "allowed"

    # Second execution with same approval → rejected (consumed)
    r2 = client.post("/api/v1/gateway/execute", json={
        "task_id": tid, "agent_id": TEST_AGENT_ID,
        "tool_name": "delete_file",
        "arguments": {"path": "/tmp/test2.txt"},
        "resource": "/tmp/test2.txt",
        "approval_id": approval["approval_id"],
    })
    assert r2.json()["authorization"] == "denied"
    assert "consumed" in r2.json()["authorization_reason"].lower()


def test_approval_changed_arguments_rejected(client):
    tid = _create_task_with_scope(client, ["read_assigned_invoice", "delete_file"],
                                  resources=["/tmp/original.txt", "/tmp/different.txt"])

    gw = GatewayService(os.environ["SQLITE_PATH"])
    approval = gw.create_approval(
        task_id=tid, agent_id=TEST_AGENT_ID,
        tool_name="delete_file",
        arguments={"path": "/tmp/original.txt"},
        resource="/tmp/original.txt",
    )
    gw.decide_approval(approval["approval_id"], "approve")

    # Execute with SAME resource but DIFFERENT argument path
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": tid, "agent_id": TEST_AGENT_ID,
        "tool_name": "delete_file",
        "arguments": {"path": "/tmp/different.txt"},
        "resource": "/tmp/different.txt",
        "approval_id": approval["approval_id"],
    })
    assert r.json()["authorization"] == "denied"
    reason = r.json()["authorization_reason"].lower()
    assert "argument" in reason or "match" in reason or "changed" in reason or "resource" in reason, \
        f"Expected arguments/resource mismatch in reason, got: {r.json()['authorization_reason']}"


# ---------------------------------------------------------------------------
# Events persist
# ---------------------------------------------------------------------------

def test_events_persist_after_gateway_call(client):
    _reset_counters(os.environ["SQLITE_PATH"])
    # Make an allowed call
    client.post("/api/v1/gateway/execute", json={
        "task_id": SEEDED_TASK_ID,
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": "read_assigned_invoice",
        "arguments": {"invoice_id": "invoice-42"},
        "resource": "invoice-42",
    })
    # Make a denied call
    client.post("/api/v1/gateway/execute", json={
        "task_id": SEEDED_TASK_ID,
        "agent_id": SEEDED_AGENT_ID,
        "tool_name": "send_external_email",
        "arguments": {"to": "bad@example.com"},
        "destination": "bad@example.com",
    })

    r = client.get("/api/v1/events")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 2

    # Filter by authorization
    r_allowed = client.get("/api/v1/events?authorization=allowed")
    assert r_allowed.json()["count"] >= 1

    r_denied = client.get("/api/v1/events?authorization=denied")
    assert r_denied.json()["count"] >= 1


def test_get_single_event(client):
    r_list = client.get("/api/v1/events?limit=1")
    if r_list.json()["count"] == 0:
        pytest.skip("No events seeded")
    event_id = r_list.json()["events"][0]["event_id"]
    r = client.get(f"/api/v1/events/{event_id}")
    assert r.status_code == 200
    assert r.json()["event_id"] == event_id


# ---------------------------------------------------------------------------
# Attack Lab scenarios
# ---------------------------------------------------------------------------

def test_attack_lab_authorized_invoice_read(client):
    _reset_counters(os.environ["SQLITE_PATH"])
    r = client.post("/api/v1/attack-lab/run", json={
        "scenario_ids": ["authorized_invoice_read"]
    })
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo"
    result = body["results"][0]
    assert result["scenario_id"] == "authorized_invoice_read"
    assert result["final_authorization"] == "allowed"
    assert result["execution_status"] == "succeeded"
    assert result["executor_call_count"] >= 1
    # Check trace stages
    stages = {s["stage"] for s in result["trace"]}
    assert "Authorization" in stages
    assert "Mock Executor" in stages


def test_attack_lab_prompt_injection_email_denied(client):
    _reset_counters(os.environ["SQLITE_PATH"])
    r = client.post("/api/v1/attack-lab/run", json={
        "scenario_ids": ["prompt_injection_email"]
    })
    assert r.status_code == 200
    result = r.json()["results"][0]
    assert result["scenario_id"] == "prompt_injection_email"
    assert result["final_authorization"] == "denied"
    assert result["execution_status"] == "not_attempted"
    assert result["executor_call_count"] == 0


def test_attack_lab_unauthorized_file_delete_denied(client):
    _reset_counters(os.environ["SQLITE_PATH"])
    r = client.post("/api/v1/attack-lab/run", json={
        "scenario_ids": ["unauthorized_file_delete"]
    })
    assert r.status_code == 200
    result = r.json()["results"][0]
    assert result["scenario_id"] == "unauthorized_file_delete"
    assert result["final_authorization"] == "denied"
    assert result["execution_status"] == "not_attempted"
    assert result["executor_call_count"] == 0


def test_attack_lab_all_three_scenarios(client):
    _reset_counters(os.environ["SQLITE_PATH"])
    r = client.post("/api/v1/attack-lab/run", json={
        "scenario_ids": [
            "authorized_invoice_read",
            "prompt_injection_email",
            "unauthorized_file_delete",
        ]
    })
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 3


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

def test_error_envelope_on_404(client):
    r = client.get("/api/v1/tasks/does-not-exist")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "http_error"
    assert "message" in body["error"]
    assert "details" in body["error"]


def test_validation_error_422(client):
    r = client.post("/api/v1/gateway/execute", json={
        "task_id": SEEDED_TASK_ID,
        # missing required fields
    })
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Approval list and decide via API
# ---------------------------------------------------------------------------

def test_approval_list_and_decide(client):
    gw = GatewayService(os.environ["SQLITE_PATH"])
    gw.create_approval(
        task_id=SEEDED_TASK_ID,
        agent_id=SEEDED_AGENT_ID,
        tool_name="delete_file",
        arguments={"path": "/tmp/approval_test.txt"},
        resource="/tmp/approval_test.txt",
        reason="Test approval",
    )

    r = client.get("/api/v1/approvals?status=pending")
    assert r.status_code == 200
    approvals = r.json()["approvals"]
    assert len(approvals) >= 1
    aid = approvals[0]["approval_id"]

    # Approve
    r2 = client.post(f"/api/v1/approvals/{aid}/decision", json={"decision": "approve"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "approved"


def test_approval_deny(client):
    gw = GatewayService(os.environ["SQLITE_PATH"])
    approval = gw.create_approval(
        task_id=SEEDED_TASK_ID,
        agent_id=SEEDED_AGENT_ID,
        tool_name="delete_file",
        arguments={"path": "/tmp/deny_test.txt"},
        resource="/tmp/deny_test.txt",
        reason="Test deny",
    )

    r = client.post(f"/api/v1/approvals/{approval['approval_id']}/decision", json={"decision": "deny"})
    assert r.status_code == 200
    assert r.json()["status"] == "denied"