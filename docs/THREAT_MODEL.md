# THREAT MODEL

## Assets
- Task intent and scope metadata
- Tool-call proposals
- Audit events and approvals

## Initial threat categories
- Unauthorized tool invocation
- Scope escalation across tasks
- Tampering with approval/event records
- Secret leakage via logs/config

## Initial mitigations in this scaffold
- Safe defaults for configuration
- No unrestricted shell/filesystem/email operations
- Explicit security limitations documentation
