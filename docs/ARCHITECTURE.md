# ARCHITECTURE

## Components
- **backend/**: FastAPI gateway API and policy orchestration foundation.
- **mobile/**: Expo app for task, approvals, and event visibility.
- **dashboard/**: React+Vite office dashboard for policy and event review.
- **shared/**: JSON schema contracts and examples.

## Current runtime flow
1. Client checks backend health.
2. Backend responds with status metadata.
3. Contract files define request/event envelopes for future enforcement.

## Planned evolution
Add policy decision points, auditable event ledgering, and controlled tool execution adapters.
