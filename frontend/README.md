# DispatchDiff Command Center

The Milestone 3 frontend is a dispatcher-facing command center for understanding and acting on operational fleet-plan exceptions. It displays the current seeded plan, injects the canonical detention through the backend, explains the targeted plan diff, compares operational metrics, and records an approve/reject decision locally.

## Local setup

Requirements: Node.js 20 or newer, npm, and the DispatchDiff backend running on port `8000`.

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and expects the backend at `http://localhost:8000` by default. Override the API origin when needed:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

On PowerShell:

```powershell
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm run dev
```

Start the backend separately:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## Demo flow

1. Review the current fleet plan and unassigned loads.
2. Review the pending 180-minute detention for `DRV-001`.
3. Select **Run Re-plan**.
4. Inspect the invalidated, preserved, removed, and added assignments.
5. Compare coverage/revenue gains with the increased deadhead tradeoff.
6. Approve the re-plan or keep the current plan.

Approval and rejection are local demonstration states only. They are not persisted to the backend.

## Architecture and verification

- `src/api`: exact backend contracts, response guards, and centralized fetch client
- `src/components`: small operational UI components
- `src/pages`: command-center orchestration and local decision state
- `src/styles`: responsive global visual system with no external UI framework

The frontend does not reproduce feasibility, scoring, prioritization, or re-planning rules. Those decisions come from the backend response.

```bash
npm run typecheck
npm test
npm run build
```
