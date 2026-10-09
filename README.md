# VAJRA AI

**Tagline:** _Let AI work. Never let it overstep._

VAJRA AI is an execution-time security gateway for AI agents. This repository currently provides the **initial monorepo scaffold** with runnable starter apps and shared contracts.

## Current Status

### Implemented in this scaffold
- FastAPI backend with `GET /health` and `/docs`
- Expo (React Native + TypeScript) mobile skeleton with Home/Tasks/Approvals/Events routes
- React + Vite + TypeScript dashboard with backend connectivity indicator
- Shared JSON schemas for task, tool-call proposal, and audit events
- CI workflow for backend tests/checks and frontend type/build checks

### Planned (not yet implemented)
- Full runtime policy enforcement engine
- Production-grade tool mediation and approval cryptography
- Full threat simulation / attack lab workflows

## Architecture Summary

- `backend/`: API and future gateway enforcement core
- `mobile/`: operator-facing mobile companion app
- `dashboard/`: office-kit web dashboard
- `shared/`: API/event contracts and examples
- `docs/`: product, architecture, threat, API, DB, and demo docs

## Repository Structure

```text
.github/  .vscode/  docs/  mobile/  dashboard/  backend/  shared/  scripts/
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm 10+

## Local Setup

```bash
bash scripts/setup.sh
```

PowerShell:

```powershell
./scripts/setup.ps1
```

## Run Commands

Backend:
```bash
cd backend
uvicorn app.main:app --reload
```

Dashboard:
```bash
cd dashboard
npm run dev
```

Dashboard backend URL override:
```bash
cd dashboard
VITE_BACKEND_BASE_URL=http://localhost:8000 npm run dev
```

Mobile:
```bash
cd mobile
npm run start
```

## Testing & Validation Commands

Backend tests:
```bash
cd backend && pytest -q
```

Backend syntax/import checks:
```bash
cd backend && python -m compileall app tests && python -c "from app.main import app; print(app.title)"
```

Dashboard checks:
```bash
cd dashboard && npm run typecheck && npm run build
```

Mobile TypeScript check:
```bash
cd mobile && npm run typecheck
```

## GitHub Pages Deployment (Dashboard)

The dashboard is deployed as a static site with GitHub Pages. The backend is **not** hosted by Pages and must be deployed separately.

Expected Pages URL for this repository:
- `https://nickroy07.github.io/VajraAi/`

Setup steps:
1. In GitHub, open **Settings → Pages** and set **Source** to **GitHub Actions**.
2. Ensure your backend is reachable from the browser and set `VITE_BACKEND_BASE_URL` for production (for example with repository Actions variables/secrets consumed by workflow updates, if needed).
3. Push to `main` or run the **Dashboard Pages** workflow manually (`workflow_dispatch`).

Notes:
- The dashboard build uses Vite base `/VajraAi/` for production builds and `/` for local development.
- Runtime API calls use `VITE_BACKEND_BASE_URL` (fallback: `VITE_API_BASE_URL`, then `http://localhost:8000`).
- This repository still contains demo/security limitations; it is not a fully production-ready security gateway yet.

## Branching Strategy

Recommended workflow:
1. Create feature branch from `develop`
2. Open PR into `develop`
3. Merge validated `develop` changes into `main` for stable/demo releases

Target branches:
- `main`
- `develop`
- `feature/backend-gateway`
- `feature/mobile-app`
- `feature/office-kit`
- `feature/security-tests`
- `feature/docs-demo`

If branch creation cannot be performed in your environment, run:

```bash
git fetch origin
git branch main origin/main || git branch main
git branch develop main
git branch feature/backend-gateway develop
git branch feature/mobile-app develop
git branch feature/office-kit develop
git branch feature/security-tests develop
git branch feature/docs-demo develop
```

Remote setup guidance (without pushing):
```bash
git remote -v
# confirm origin points to your repo before any push
```

## Security Scope and Limitations

This scaffold is **not** the complete security gateway. It does not yet enforce full policy decisions across all protected operations.
See `docs/SECURITY_LIMITATIONS.md` for details.
