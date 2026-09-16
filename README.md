# DispatchDiff

Explainable exception handling for fleet re-planning.

DispatchDiff demonstrates how fleet operators can understand and respond when real-world operational disruptions invalidate parts of an existing plan. It pairs a deterministic planning API with a dispatcher-facing command center that explains affected, preserved, and replacement assignments.

## Demo flow

1. Load the current fleet plan.
2. Inject a 180-minute driver detention.
3. Detect the invalidated assignment.
4. Preserve unaffected assignments.
5. Reassign affected work.
6. Compare operational tradeoffs.
7. Approve or reject the proposed re-plan.

## Architecture

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + deterministic planning/replanning logic
- Deployment: Vercel + Render

## Local development

Python 3.11+ and Node.js 20+ are required.

Start the backend:

```bash
cd backend
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Run verification:

```bash
cd backend
python -m pytest
ruff check .
ruff format --check .

cd ../frontend
npm test
npm run typecheck
npm run build
```

## Environment variables

- Frontend: `VITE_API_BASE_URL` — backend origin; defaults to `http://localhost:8000`.
- Backend: `FRONTEND_ORIGIN` — deployed frontend origin allowed by CORS. Localhost remains allowed.

Copy the provided `.env.example` files for local overrides. Real `.env` files are ignored.

## Deployment

### Render backend

Create a Blueprint from this repository using the root `render.yaml`, or configure a Python web service with:

- Root directory: `backend`
- Build command: `pip install .`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Environment variable: `FRONTEND_ORIGIN=https://<your-vercel-domain>`

### Vercel frontend

Import the same repository and configure:

- Root directory: `frontend`
- Framework: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_BASE_URL=https://<your-render-domain>`

Deploy the backend first, deploy the frontend with the backend URL, then set the final Vercel origin on Render and redeploy the backend.
