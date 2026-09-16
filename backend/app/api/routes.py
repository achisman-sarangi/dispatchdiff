from fastapi import APIRouter, HTTPException, status

from app.domain.models import Driver, Load, OperationalDisruption
from app.planning.service import PlanBuildResult, PlanningService
from app.replanning.service import ReplanningService, ReplanResult
from app.schemas.responses import (
    DriverResponse,
    EvaluateRequest,
    EvaluateResponse,
    LoadResponse,
    OperationalDisruptionResponse,
    PlanBuildResponse,
    ReplanRequest,
    ReplanResponse,
)
from app.seed.demo_data import DEMO_DRIVERS, DEMO_LOADS, get_demo_disruption

router = APIRouter()
planning_service = PlanningService()
replanning_service = ReplanningService(planning_service)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/demo/drivers", response_model=list[DriverResponse])
def list_demo_drivers() -> tuple[Driver, ...]:
    return DEMO_DRIVERS


@router.get("/api/demo/loads", response_model=list[LoadResponse])
def list_demo_loads() -> tuple[Load, ...]:
    return DEMO_LOADS


@router.get("/api/demo/plan", response_model=PlanBuildResponse)
def build_demo_plan() -> PlanBuildResult:
    return planning_service.build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS)


@router.get("/api/demo/disruption", response_model=OperationalDisruptionResponse)
def get_canonical_demo_disruption() -> OperationalDisruption:
    return get_demo_disruption()


@router.post("/api/demo/replan", response_model=ReplanResponse)
def replan_demo() -> ReplanResult:
    current_plan = planning_service.build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS).plan
    return replanning_service.replan_after_disruption(
        DEMO_DRIVERS, DEMO_LOADS, current_plan, get_demo_disruption()
    )


@router.post("/api/replan", response_model=ReplanResponse)
def replan(request: ReplanRequest) -> ReplanResult:
    disruption = request.disruption.to_domain()
    if not any(driver.id == disruption.driver_id for driver in DEMO_DRIVERS):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {disruption.driver_id} not found.",
        )
    current_plan = planning_service.build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS).plan
    return replanning_service.replan_after_disruption(
        DEMO_DRIVERS, DEMO_LOADS, current_plan, disruption
    )


@router.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate_assignment(request: EvaluateRequest) -> EvaluateResponse:
    driver = next((item for item in DEMO_DRIVERS if item.id == request.driver_id), None)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {request.driver_id} not found.",
        )
    load = next((item for item in DEMO_LOADS if item.id == request.load_id), None)
    if load is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load {request.load_id} not found.",
        )
    evaluation = planning_service.evaluate_assignment(driver, load)
    return EvaluateResponse(
        driver_id=evaluation.driver_id,
        load_id=evaluation.load_id,
        feasible=evaluation.feasibility.feasible,
        violations=list(evaluation.feasibility.violations),
        planned_pickup_at=evaluation.planned_pickup_at,
        planned_delivery_at=evaluation.planned_delivery_at,
        score=evaluation.score,
    )
