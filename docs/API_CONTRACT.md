# API CONTRACT — VAJRA AI Gateway v0.2.0

## Conventions
- Base prefix: `/api/v1` (except `/health`)
- IDs use UUID strings
- Timestamps use ISO-8601 UTC
- Status fields use explicit enums
- Error responses use:
  ```json
  {
    "error": {
      "code": "string",
      "message": "string",
      "details": {}
    }
  }
  ```

## Endpoints

### `GET /health`
Returns backend health — does not claim enforcement is active unless tested.

**Response 200:**
```json
{
  "status": "ok",
  "service": "VAJRA AI Gateway",
  "timestamp": "2026-10-09T16:00:00.000000+00:00"
}
```

---

### `GET /api/v1/overview`
Returns demo-mode summary with counts derived from persisted rows.

**Response 200:**
```json
{
  "mode": "demo",
  "gateway_connected": true,
  "metrics": [
    {"label": "Active Tasks", "value": 1},
    {"label": "Allowed", "value": 0},
    {"label": "Blocked", "value": 0},
    {"label": "Pending Approvals", "value": 0}
  ],
  "recent_events": [],
  "attention_items": ["DEMO ENVIRONMENT — Simulated protections only. Not connected to production AI agents."]
}
```

---

### `GET /api/v1/tasks` | `POST /api/v1/tasks` | `GET /api/v1/tasks/{task_id}`
Task CRUD with scope (allowed_tools, resources, destination_allowlist, block_external_destinations).

**POST /api/v1/tasks request:**
```json
{
  "description": "Invoice Summary — DEMO",
  "status": "running",
  "scope": {
    "allowed_tools": ["read_assigned_invoice", "generate_local_summary"],
    "resources": ["invoice-42"],
    "destination_allowlist": [],
    "block_external_destinations": true
  }
}
```

**Response 201:**
```json
{
  "task_id": "uuid",
  "created_at": "2026-10-09T...",
  "updated_at": "2026-10-09T...",
  "status": "running",
  "description": "Invoice Summary — DEMO",
  "scope": { ... }
}
```

---

### `GET /api/v1/agents`
List registered agents.

**Response 200:**
```json
{
  "agents": [
    {
      "agent_id": "uuid",
      "name": "Code Helper (demo)",
      "agent_type": "claude-code",
      "status": "connected",
      "registered_at": "2026-10-09T..."
    }
  ],
  "count": 1
}
```

---

### `GET /api/v1/tasks/{task_id}/policy` | `PUT /api/v1/tasks/{task_id}/policy`
Inspect and update task policy. PUT auto-creates policy if missing.

**PUT request:**
```json
{
  "rules": [
    {"tool": "read_assigned_invoice", "action": "allow", "description": "Read invoices"},
    {"tool": "send_external_email", "action": "deny", "description": "External email blocked"}
  ]
}
```

---

### `GET /api/v1/approvals?status=pending` | `POST /api/v1/approvals/{approval_id}/decision`
List pending approvals and decide them.

**POST decision:**
```json
{"decision": "approve"}
```

---

### `POST /api/v1/gateway/execute`
The ONE authoritative gateway for protected tool execution. Re-validates policy and approvals server-side.

**Request:**
```json
{
  "task_id": "uuid",
  "agent_id": "uuid",
  "tool_name": "read_assigned_invoice",
  "arguments": {"invoice_id": "invoice-42"},
  "resource": "invoice-42",
  "destination": "",
  "approval_id": null
}
```

**Response (allowed):**
```json
{
  "event_id": "uuid",
  "task_id": "uuid",
  "tool_name": "read_assigned_invoice",
  "authorization": "allowed",
  "authorization_reason": "Read the assigned invoice resource",
  "execution_status": "succeeded",
  "execution_result": "[SIMULATED] Read invoice invoice-42: ...",
  "executor_call_count": 1,
  "timestamp": "2026-10-09T..."
}
```

**Response (denied):**
```json
{
  "event_id": "uuid",
  "task_id": "uuid",
  "tool_name": "send_external_email",
  "authorization": "denied",
  "authorization_reason": "External email is not permitted for this task",
  "execution_status": "not_attempted",
  "execution_result": null,
  "executor_call_count": 0,
  "timestamp": "2026-10-09T..."
}
```

---

### `GET /api/v1/events` | `GET /api/v1/events/{event_id}`
Filterable event listing. Query params: `authorization` (allowed|denied), `execution_status` (not_attempted|succeeded|failed), `task_id`, `tool_name`, `agent_id`, `limit`, `offset`.

**Response 200:**
```json
{
  "events": [
    {
      "event_id": "uuid",
      "task_id": "uuid",
      "agent_id": "uuid",
      "tool_name": "read_assigned_invoice",
      "event_type": "tool.executed",
      "authorization": "allowed",
      "authorization_reason": "Read the assigned invoice resource",
      "execution_status": "succeeded",
      "execution_result": "[SIMULATED] ...",
      "arguments": {"invoice_id": "invoice-42"},
      "resource": "invoice-42",
      "destination": "",
      "timestamp": "2026-10-09T...",
      "details": {"mode": "demo"}
    }
  ],
  "count": 1
}
```

---

### `POST /api/v1/attack-lab/run`
Run attack lab scenarios against the real gateway service.

**Request:**
```json
{
  "scenario_ids": ["authorized_invoice_read", "prompt_injection_email"]
}
```

**Response 200:**
```json
{
  "mode": "demo",
  "results": [
    {
      "scenario_id": "authorized_invoice_read",
      "scenario_label": "Authorized Invoice Read",
      "final_authorization": "allowed",
      "authorization_reason": "Read the assigned invoice resource",
      "execution_status": "succeeded",
      "executor_call_count": 1,
      "event_id": "uuid",
      "trace": [
        {"stage": "Agent Request", "status": "info", "detail": "..."},
        {"stage": "Policy Evaluation", "status": "info", "detail": "..."},
        {"stage": "Authorization", "status": "allowed", "detail": "..."},
        {"stage": "Mock Executor", "status": "succeeded", "detail": "..."},
        {"stage": "Audit Event", "status": "info", "detail": "..."}
      ]
    }
  ]
}
```

## Mock Tool Registry
| Tool | Behavior |
|---|---|
| `read_assigned_invoice` | Simulated invoice read (deterministic) |
| `generate_local_summary` | Simulated local text summary |
| `send_external_email` | Simulated email (call counter, no real send) |
| `delete_file` | Simulated file deletion (call counter, no real delete) |

Unknown tools are denied by default.

## Error Codes
- `400` — Invalid request body / missing required fields
- `404` — Resource not found (task, policy, approval, event)
- `409` — Conflict (duplicate task ID)
- `422` — Pydantic validation error
- `500` — Internal error

Error body:
```json
{
  "error": {
    "code": "http_error",
    "message": "Task not found",
    "details": {}
  }
}
```

## Implementation Status
- **Implemented:** All endpoints above with SQLite persistence, mock tool registry, policy engine, approval binding/consumption, event recording, attack lab scenarios, demo seeding.
- **Simulated:** Mock tools produce deterministic simulated output; no real email, file ops, or external side effects.
- **Not implemented:** Multi-tenant auth/OAuth, production cryptographic key management, distributed deployment, real AI agent SDK integrations, immutable audit log/blockchain.