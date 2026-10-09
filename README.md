# VAJRA AI

**Let AI work. Never let it overstep.**

VAJRA AI is an execution-time security gateway for AI agents, plus **Document Guard**, a heuristic scanner for documents an agent is about to read. This repository is a hackathon prototype: the policy enforcement is real backend code with regression tests, and every tool it protects is a **mock** (no real email is sent and no files are deleted).

## What it does

1. **Document Guard** (web + mobile). You paste text, upload a `.txt` file (web only), or load a clearly marked sample invoice. Deterministic backend rules flag prompt-injection phrases, external-sharing requests, email addresses, risky URLs, card-like numbers (Luhn-checked), phone numbers, credentials and hidden zero-width text. Results come back as findings with a severity of *Review*, *Elevated* or *High* and short, redacted evidence. These are **heuristic risk signals, not a malware verdict**. The document is processed in memory and is never stored or sent to an LLM.
2. **Protected demo agent.** "Test with protected agent" runs a deterministic demo agent that naively follows the document. If the text says to send the invoice somewhere, the agent proposes `send_external_email`; otherwise it proposes `generate_local_summary`. The proposal goes through the real gateway.
3. **Gateway** (`POST /api/v1/gateway/execute`). This is the only path to a mock executor. It checks, failing closed at each step: task exists and is runnable → agent registered → policy present → tool known → arguments match the tool schema → tool is in the task's `allowed_tools` → the resource (taken from the tool argument) is in scope → the destination (taken from the tool argument, e.g. email `to`) is valid and on the allowlist → policy rule → approval. Every outcome is persisted as an audit event **before** the response is returned. Denied actions never call the executor.
4. **Human approval.** When the policy says `require_approval`, the gateway creates a pending approval. The approval is bound to the task, agent, tool, a SHA-256 of the canonical arguments, the resource, the destination and the current policy fingerprint, and it expires after 10 minutes. You approve or reject it on the web or the phone. The agent then resubmits with `approval_id`, and the gateway re-validates everything and consumes the approval atomically, exactly once. Replayed, changed, expired, rejected or policy-changed approvals are denied.
5. **Attack Lab.** Deterministic scenarios run through the same gateway. The step-by-step trace is Agent Proposal → Policy → Decision → Mock Executor → Audit Event. Each result includes an executor-call delta read from the persisted counter before and after the call.

### What "document risk detected" vs. "action blocked" means
- **Document risk detected** is heuristic. It informs a human and never authorizes or blocks anything.
- **Action blocked by gateway** is enforced. The backend policy refused the action and the mock executor was not called (Δ 0).

## Limitations (read before demoing)
- **This does not intercept or control the normal ChatGPT, Claude or Gemini apps** (mobile or web), and it cannot. It protects only actions that an agent sends through this gateway. The only supported agent is the built-in deterministic demo agent.
- All tools are mocks. There is no real email, filesystem or third-party API access.
- Approval decisions are not authenticated (no login). Anyone who can reach the API can decide an approval.
- Document Guard uses regex and heuristics, so it has false positives and false negatives. It supports pasted text and `.txt` files; it does not parse PDFs or run OCR.
- The database is a single-node SQLite file. See `docs/SECURITY_LIMITATIONS.md`.

## Run it locally

Prerequisites: Python 3.11+, Node 20+.

**Backend** (FastAPI + SQLite, seeded with demo data on first start):
```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API docs: http://localhost:8000/docs
```

**Web dashboard:**
```bash
cd dashboard
npm ci
npm run dev            # http://localhost:5173, uses http://localhost:8000 by default in dev
# or point it at another backend:
VITE_BACKEND_BASE_URL=http://192.168.1.20:8000 npm run dev
```

**Mobile companion (Expo):**
```bash
cd mobile
npm ci
npm run start          # Android emulator defaults to http://10.0.2.2:8000
```

### Physical Android phone
1. Put the phone and laptop on the same Wi-Fi network.
2. Find the laptop's LAN IP address (`ipconfig` on Windows, `ip addr` or `ifconfig` on macOS/Linux), for example `192.168.1.20`.
3. Start the backend bound to all interfaces: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
4. Allow inbound TCP port 8000 through the laptop firewall. On Windows, accept the prompt for Python on *Private* networks or add an inbound rule. Check by opening `http://192.168.1.20:8000/health` in the phone's browser.
5. Start Expo with the URL:
   - bash: `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.20:8000 npm run start`
   - PowerShell: `$env:EXPO_PUBLIC_API_BASE_URL="http://192.168.1.20:8000"; npm run start`
6. Scan the QR code with Expo Go. Home shows "Server: http://192.168.1.20:8000" and Online.

## Deployment
- **GitHub Pages** hosts only the static dashboard (`.github/workflows/dashboard-pages.yml`, served at `https://nickroy07.github.io/VajraAi/`). It does **not** host the FastAPI backend. Set the repository variable `VITE_BACKEND_BASE_URL` to a deployed backend. If it is not set, the site shows "Backend not configured" instead of guessing at localhost.
- **Backend (optional):** `backend/Dockerfile` and `render.yaml` deploy the API as a Docker web service, for example on Render. SQLite is ephemeral there, so demo data resets on redeploy. No public backend URL exists until you deploy one.

## Tests & checks
```bash
cd backend && pytest -q && python -m compileall -q app tests && python -c "from app.main import app; print(app.title)"
cd dashboard && npm run typecheck && npm run build
cd mobile && npm run typecheck
```
`backend/tests/security/test_security_regressions.py` covers the fail-closed scope rules, lookalike domains, conflicting destinations, approval approve/reject/expiry/changed-arguments/replay/policy-change/agent-binding, verified executor deltas, redaction, and Document Guard.

## Repository layout
`backend/` FastAPI gateway · `dashboard/` React + Vite web app · `mobile/` Expo app · `shared/` JSON contracts · `docs/` product, threat model and demo script.

See `docs/DEMO_SCRIPT.md` for the 3-minute presenter sequence.
