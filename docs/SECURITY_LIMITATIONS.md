# Security Limitations

**Version:** 0.2.0 MVP Demo  
**Last updated:** 2026-10-09

## Summary
This is a **proof-of-concept demonstration** of an execution-time security gateway for AI-agent integrations. It is NOT a production-grade multi-tenant authorization system.

## Implemented
- ✅ Server-side policy evaluation with default-deny
- ✅ Task-scoped tool/resource/destination constraints
- ✅ Approval binding with SHA-256 argument fingerprinting
- ✅ One-time approval consumption (transaction-safe for single-instance SQLite)
- ✅ Approval expiry and re-validation on execution
- ✅ Separate authorization decision from execution outcome
- ✅ Audit event recording with structured JSON
- ✅ Deterministic mock tools (no real side effects)
- ✅ Attack Lab exercising real gateway enforcement
- ✅ Demo data seeding

## Simulated
- ⚠️ Mock tools produce deterministic simulated output only
- ⚠️ No real email, file operations, or external side effects
- ⚠️ SQLite is local single-instance (no replication, no distributed locks)

## Not Implemented
- ❌ Multi-tenant authentication / OAuth / SSO
- ❌ Production-grade cryptographic key management (HSM, secrets rotation)
- ❌ Distributed / high-availability deployment
- ❌ Real AI agent SDK integrations (Claude Code, Cursor, etc.)
- ❌ Immutable audit log / blockchain anchoring
- ❌ Rate limiting and DoS protection
- ❌ Network-level isolation or sandboxing of mock executors
- ❌ Compliance certifications (SOC 2, ISO 27001, etc.)

## Known Weaknesses (Demo Context)
1. **Single-instance SQLite:** Not suitable for concurrent multi-user access. WAL mode is enabled but there is no connection pooling.
2. **No auth:** CORS is open (*), no API keys or tokens required. Suitable for localhost development only.
3. **Mock executors in-process:** No sandbox isolation. A compromised tool implementation could access the host.
4. **Argument hashing uses SHA-256:** Adequate for demo but deferred to production-grade crypto for real deployments.
5. **Approval storage is plaintext:** No encryption at rest.

## Recommendations for Production
1. Replace SQLite with PostgreSQL + connection pooling
2. Add API key / JWT-based authentication
3. Sandbox mock executors in isolated processes/containers
4. Use HMAC or asymmetric signatures for approval binding
5. Add comprehensive audit logging with append-only guarantees
6. Implement proper RBAC and multi-tenancy