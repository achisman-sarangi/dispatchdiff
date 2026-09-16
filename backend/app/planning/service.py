from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.models import Assignment, Driver, FleetPlan, Load
from app.planning.feasibility import FeasibilityResult, evaluate_feasibility
from app.planning.scoring import calculate_assignment_score


@dataclass(frozen=True, slots=True)
class AssignmentEvaluation:
    driver_id: str
    load_id: str
    feasibility: FeasibilityResult
    planned_pickup_at: datetime
    planned_delivery_at: datetime
    score: float | None


@dataclass(frozen=True, slots=True)
class DriverCandidate:
    driver: Driver
    planned_pickup_at: datetime
    planned_delivery_at: datetime
    score: float


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    total_loads: int
    assigned_loads: int
    unassigned_loads: int
    total_revenue_cents: int
    total_deadhead_minutes: int


@dataclass(frozen=True, slots=True)
class PlanBuildResult:
    plan: FleetPlan
    unassigned_load_ids: tuple[str, ...]
    evaluation_summary: EvaluationSummary


class PlanningService:
    def evaluate_assignment(self, driver: Driver, load: Load) -> AssignmentEvaluation:
        feasibility = evaluate_feasibility(driver, load)
        score = (
            calculate_assignment_score(load, load.estimated_deadhead_minutes)
            if feasibility.result.feasible
            else None
        )
        return AssignmentEvaluation(
            driver_id=driver.id,
            load_id=load.id,
            feasibility=feasibility.result,
            planned_pickup_at=feasibility.planned_pickup_at,
            planned_delivery_at=feasibility.planned_delivery_at,
            score=score,
        )

    def rank_feasible_drivers(
        self, load: Load, drivers: list[Driver] | tuple[Driver, ...]
    ) -> list[DriverCandidate]:
        candidates: list[DriverCandidate] = []
        for driver in drivers:
            evaluation = self.evaluate_assignment(driver, load)
            if evaluation.feasibility.feasible and evaluation.score is not None:
                candidates.append(
                    DriverCandidate(
                        driver=driver,
                        planned_pickup_at=evaluation.planned_pickup_at,
                        planned_delivery_at=evaluation.planned_delivery_at,
                        score=evaluation.score,
                    )
                )
        return sorted(candidates, key=lambda item: (-item.score, item.driver.id))

    def build_greedy_plan(
        self,
        drivers: list[Driver] | tuple[Driver, ...],
        loads: list[Load] | tuple[Load, ...],
        *,
        plan_id: str = "plan-001",
        created_at: datetime = datetime(2025, 1, 1, tzinfo=UTC),
    ) -> PlanBuildResult:
        loads_by_id = {load.id: load for load in loads}
        used_driver_ids: set[str] = set()
        assignments: list[Assignment] = []
        unassigned_load_ids: list[str] = []

        for load in sorted(loads, key=lambda item: (item.pickup_end, item.id)):
            unused_drivers = [driver for driver in drivers if driver.id not in used_driver_ids]
            candidates = self.rank_feasible_drivers(load, unused_drivers)
            if not candidates:
                unassigned_load_ids.append(load.id)
                continue
            selected = candidates[0]
            assignments.append(
                Assignment(
                    driver_id=selected.driver.id,
                    load_id=load.id,
                    planned_pickup_at=selected.planned_pickup_at,
                    planned_delivery_at=selected.planned_delivery_at,
                    deadhead_minutes=load.estimated_deadhead_minutes,
                    score=selected.score,
                )
            )
            used_driver_ids.add(selected.driver.id)

        total_revenue_cents = sum(
            loads_by_id[assignment.load_id].revenue_cents for assignment in assignments
        )
        total_deadhead_minutes = sum(assignment.deadhead_minutes for assignment in assignments)
        summary = EvaluationSummary(
            total_loads=len(loads_by_id),
            assigned_loads=len(assignments),
            unassigned_loads=len(unassigned_load_ids),
            total_revenue_cents=total_revenue_cents,
            total_deadhead_minutes=total_deadhead_minutes,
        )
        return PlanBuildResult(
            plan=FleetPlan(plan_id, tuple(assignments), created_at),
            unassigned_load_ids=tuple(unassigned_load_ids),
            evaluation_summary=summary,
        )
