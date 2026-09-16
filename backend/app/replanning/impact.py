from dataclasses import dataclass

from app.domain.errors import PlanReferenceError
from app.domain.models import Driver, FleetPlan, Load
from app.planning.feasibility import ConstraintViolation, evaluate_feasibility


@dataclass(frozen=True, slots=True)
class AssignmentImpact:
    driver_id: str
    load_id: str
    impacted: bool
    reasons: tuple[ConstraintViolation, ...]


def evaluate_plan_impact(
    plan: FleetPlan,
    drivers: list[Driver] | tuple[Driver, ...],
    loads: list[Load] | tuple[Load, ...],
) -> tuple[AssignmentImpact, ...]:
    drivers_by_id = {driver.id: driver for driver in drivers}
    loads_by_id = {load.id: load for load in loads}
    impacts: list[AssignmentImpact] = []

    for assignment in plan.assignments:
        driver = drivers_by_id.get(assignment.driver_id)
        if driver is None:
            raise PlanReferenceError(f"Unknown driver in plan: {assignment.driver_id}.")
        load = loads_by_id.get(assignment.load_id)
        if load is None:
            raise PlanReferenceError(f"Unknown load in plan: {assignment.load_id}.")
        result = evaluate_feasibility(driver, load).result
        impacts.append(
            AssignmentImpact(
                driver_id=assignment.driver_id,
                load_id=assignment.load_id,
                impacted=not result.feasible,
                reasons=result.violations,
            )
        )
    return tuple(impacts)
