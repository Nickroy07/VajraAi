"""Mock tool registry — simulated behavior only. No real side effects.

Each tool declares which argument names it requires, which argument is the
resource it acts on, and which argument is its outbound destination. The policy
engine uses this metadata so authorization is based on the *actual* arguments
the executor would receive, never on caller-supplied labels alone.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required_args: tuple[str, ...]
    optional_args: tuple[str, ...] = ()
    resource_arg: str | None = None
    destination_arg: str | None = None
    run: Callable[[dict[str, Any]], str] = lambda _args: ""

    @property
    def allowed_args(self) -> set[str]:
        return set(self.required_args) | set(self.optional_args)

    def execute(self, arguments: dict[str, Any]) -> str:
        return self.run(arguments)


def _read_invoice(args: dict[str, Any]) -> str:
    return (
        f"[SIMULATED] Read invoice {args['invoice_id']}: amount $12,450.00 | "
        "vendor 'ACME Corp' | due 2026-11-15"
    )


def _local_summary(args: dict[str, Any]) -> str:
    return (
        f"[SIMULATED] Local summary for {args['invoice_id']}: ACME Corp invoice, "
        "$12,450.00 due 2026-11-15. Written to local workspace only."
    )


def _send_email(args: dict[str, Any]) -> str:
    subject = args.get("subject", "(no subject)")
    return f"[SIMULATED] Email to {args['to']} with subject '{subject}' — NOT ACTUALLY SENT"


def _delete_file(args: dict[str, Any]) -> str:
    return f"[SIMULATED] File '{args['path']}' — NOT ACTUALLY DELETED"


ALLOWLISTED_TOOLS: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in [
        ToolSpec(
            name="read_assigned_invoice",
            description="Read the invoice assigned to the task",
            required_args=("invoice_id",),
            resource_arg="invoice_id",
            run=_read_invoice,
        ),
        ToolSpec(
            name="generate_local_summary",
            description="Write a summary of an invoice to the local workspace",
            required_args=("invoice_id",),
            optional_args=("text",),
            resource_arg="invoice_id",
            run=_local_summary,
        ),
        ToolSpec(
            name="send_external_email",
            description="Send an email to a recipient outside the workspace",
            required_args=("to", "subject"),
            optional_args=("body", "attachment"),
            resource_arg="attachment",
            destination_arg="to",
            run=_send_email,
        ),
        ToolSpec(
            name="delete_file",
            description="Delete a file",
            required_args=("path",),
            resource_arg="path",
            run=_delete_file,
        ),
    ]
}


def is_known_tool(tool_name: str) -> bool:
    return tool_name in ALLOWLISTED_TOOLS


def get_tool(tool_name: str) -> ToolSpec | None:
    return ALLOWLISTED_TOOLS.get(tool_name)
