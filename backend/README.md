# DispatchDiff — Milestone 1

DispatchDiff is a Fleetline-inspired trucking operations prototype. It helps a dispatcher understand whether assignments remain operationally feasible, how operational disruptions affect an existing plan, and why assignments change. It is adjacent to, not a replacement for, a fleet optimizer.

Milestone 1 provides a deterministic backend foundation: typed drivers, loads, assignments and plans; structured feasibility violations; the specified revenue/deadhead score; a one-load-per-driver greedy planner; fixed demo data; and a FastAPI interface.

Milestone 2 adds typed operational disruptions, immutable fleet-state updates, existing-plan impact detection, preservation-first re-planning, structured assignment changes, deterministic explanations, and before/after operational metrics.

It deliberately does **not** include a frontend, authentication, persistence, queues, LLM calls, natural-language parsing, geospatial routing, disruption handling, re-planning, plan diffs, or OR-Tools.

## Architecture

- `app/domain`: framework-independent fleet entities and enums
- `app/planning`: pure feasibility/scoring rules and initial planning orchestration
- `app/disruptions`: immutable operational disruption application
- `app/replanning`: impact detection, targeted reassignment, plan diffs, and metrics
- `app/seed`: deterministic eight-driver, twelve-load demo scenario
- `app/schemas`: Pydantic v2 HTTP contracts
- `app/api`: thin FastAPI route handlers

The initial greedy planner orders loads by pickup-window end, ranks currently unused feasible drivers by score (then driver ID), and selects the first candidate. Home-time feasibility is deliberately simplified: delivery must occur by the driver's home deadline, without modeling the return trip yet.

The Milestone 2 workflow is:

```text
existing plan -> disruption -> impact detection -> targeted reassignment -> explainable diff
```

Unaffected assignments are preserved exactly. Impacted committed loads are recovered first, followed by impacted non-committed loads and previously unassigned loads. This intentionally simple, deterministic preservation-first strategy demonstrates the dispatcher workflow. DispatchDiff is not attempting to reproduce Fleetline's global optimization algorithms.

## Run

Python 3.11 or newer is required.

```bash
cd backend
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Run all checks:

```bash
ruff check .
pytest
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Process health |
| GET | `/api/demo/drivers` | Eight seeded drivers |
| GET | `/api/demo/loads` | Twelve seeded loads |
| GET | `/api/demo/plan` | Build the deterministic greedy plan |
| GET | `/api/demo/disruption` | Canonical 180-minute detention |
| POST | `/api/evaluate` | Evaluate seeded `driver_id` and `load_id` |
| POST | `/api/replan` | Apply a submitted disruption to the seeded plan |
| POST | `/api/demo/replan` | Run the canonical preservation-first demo |

Milestone 3 will add the dispatcher command-center UI. Explicit dispatcher approval and more advanced planning remain future work.
