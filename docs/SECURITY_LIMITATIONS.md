# SECURITY LIMITATIONS

This repository currently provides a scaffold and does **not** implement full execution-time security enforcement.

## Not yet implemented
- Production policy decision engine
- Real protected tool execution adapters
- Complete approval cryptographic guarantees
- Multi-tenant isolation controls

## Current safety posture
- Minimal backend with read-only health endpoint
- Placeholder local SQLite init only
- No unrestricted command/file/email features
