import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def initialize_sqlite(sqlite_path: str) -> None:
    """Initialize SQLite tables idempotently. Seeds demo data only when missing."""
    db_path = Path(sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                description TEXT NOT NULL,
                scope TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                agent_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'disconnected',
                registered_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS policies (
                policy_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL UNIQUE,
                rules TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent_id TEXT,
                tool_name TEXT NOT NULL,
                arguments_hash TEXT NOT NULL,
                arguments TEXT NOT NULL DEFAULT '{}',
                resource TEXT NOT NULL DEFAULT '',
                destination TEXT NOT NULL DEFAULT '',
                reason TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                expires_at TEXT NOT NULL,
                consumed_at TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT,
                decided_by TEXT DEFAULT 'system',
                policy_hash TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                task_id TEXT,
                agent_id TEXT,
                tool_name TEXT,
                event_type TEXT NOT NULL,
                authorization TEXT NOT NULL DEFAULT 'pending',
                authorization_reason TEXT NOT NULL DEFAULT '',
                execution_status TEXT NOT NULL DEFAULT 'not_attempted',
                execution_result TEXT,
                arguments TEXT NOT NULL DEFAULT '{}',
                resource TEXT NOT NULL DEFAULT '',
                destination TEXT NOT NULL DEFAULT '',
                timestamp TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mock_executor_counters (
                tool_name TEXT PRIMARY KEY,
                call_count INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Migrate approvals tables created before policy binding existed
        cols = {r[1] for r in conn.execute("PRAGMA table_info(approvals)").fetchall()}
        if "policy_hash" not in cols:
            conn.execute("ALTER TABLE approvals ADD COLUMN policy_hash TEXT NOT NULL DEFAULT ''")
        # Exact action payload, held server-side only while the approval is live
        if "action_payload" not in cols:
            conn.execute("ALTER TABLE approvals ADD COLUMN action_payload TEXT")
        conn.commit()

        _seed_if_empty(conn)
        _seed_approval_demo_task(conn)


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Seed demo data only when the tasks table is empty."""
    cur = conn.execute("SELECT COUNT(*) FROM tasks")
    if cur.fetchone()[0] > 0:
        return

    now = _utcnow()
    task_id = "00000000-0000-0000-0000-000000000001"
    agent_id = "00000000-0000-0000-0000-000000000100"
    agent_id_2 = "00000000-0000-0000-0000-000000000101"

    conn.execute(
        "INSERT INTO tasks (task_id, created_at, updated_at, status, description, scope) VALUES (?, ?, ?, ?, ?, ?)",
        (
            task_id,
            now,
            now,
            "running",
            "Invoice Summary — DEMO",
            json.dumps({
                "allowed_tools": ["read_assigned_invoice", "generate_local_summary"],
                "resources": ["invoice-42"],
                "destination_allowlist": [],
                "block_external_destinations": True,
            }),
        ),
    )

    for aid, name, atype in [
        (agent_id, "Code Helper (demo)", "claude-code"),
        (agent_id_2, "Security Reviewer (demo)", "claude-code"),
    ]:
        conn.execute(
            "INSERT INTO agents (agent_id, name, agent_type, status, registered_at) VALUES (?, ?, ?, ?, ?)",
            (aid, name, atype, "connected", now),
        )

    conn.execute(
        "INSERT INTO policies (policy_id, task_id, rules, updated_at) VALUES (?, ?, ?, ?)",
        (
            "00000000-0000-0000-0000-000000000200",
            task_id,
            json.dumps([
                {"tool": "read_assigned_invoice", "action": "allow", "description": "Read the assigned invoice resource"},
                {"tool": "generate_local_summary", "action": "allow", "description": "Generate a local summary from invoice data"},
                {"tool": "send_external_email", "action": "deny", "description": "External email is not permitted for this task"},
                {"tool": "delete_file", "action": "deny", "description": "File deletion is not permitted for this task"},
            ]),
            now,
        ),
    )

    # Seed tool counters
    for tool in ["read_assigned_invoice", "generate_local_summary", "send_external_email", "delete_file"]:
        conn.execute(
            "INSERT OR IGNORE INTO mock_executor_counters (tool_name, call_count) VALUES (?, 0)",
            (tool,),
        )

    conn.commit()


APPROVAL_TASK_ID = "00000000-0000-0000-0000-000000000002"


def _seed_approval_demo_task(conn: sqlite3.Connection) -> None:
    """Seed the approval-flow demo task (idempotent, also for older databases)."""
    now = _utcnow()
    conn.execute(
        "INSERT OR IGNORE INTO tasks (task_id, created_at, updated_at, status, description, scope) VALUES (?, ?, ?, ?, ?, ?)",
        (
            APPROVAL_TASK_ID,
            now,
            now,
            "running",
            "Vendor Payment Confirmation — DEMO (human approval)",
            json.dumps({
                "allowed_tools": ["read_assigned_invoice", "send_external_email"],
                "resources": ["invoice-42"],
                "destination_allowlist": ["billing@acme-corp.example"],
                "block_external_destinations": True,
            }),
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO policies (policy_id, task_id, rules, updated_at) VALUES (?, ?, ?, ?)",
        (
            "00000000-0000-0000-0000-000000000201",
            APPROVAL_TASK_ID,
            json.dumps([
                {"tool": "read_assigned_invoice", "action": "allow", "description": "Read the assigned invoice resource"},
                {"tool": "send_external_email", "action": "require_approval", "description": "Emails to the allowlisted vendor need a one-time human approval"},
            ]),
            now,
        ),
    )
    conn.commit()


def get_connection(sqlite_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(sqlite_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn