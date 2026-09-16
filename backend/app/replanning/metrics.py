from dataclasses import dataclass

from app.domain.enums import ConstraintViolationCode
from app.domain.errors import PlanReferenceError
from app.domain.models import Driver, FleetPlan, Load
from app.planning.feasibility import evaluate_feasibility


@dataclass(frozen=True, slots=True)
class PlanMetrics:
    assigned_loads: int
    unassigned_loads: int
    committed_loads_unassigned: int
    total_revenue_cents: int
    total_deadhead_minutes: int
    hos_violations: int
    late_loads: int
    changed_assignments: int
    preserved_assignments: int


@dataclass(frozen=True, slots=True)
class PlanMetricDelta:
    revenue_cents_delta: int
    deadhead_minutes_delta: int
    assigned_loads_delta: int
    unassigned_loads_delta: int
    committed_loads_unassigned_delta: int
    hos_violations_delta: int
    late_loads_delta: int
    changed_assignments: int


@dataclass(frozen=True, slots=True)
class ReplanMetrics:
    before_metrics: PlanMetrics
    after_metrics: PlanMetrics
    delta: PlanMetricDelta


def calculate_plan_metrics(
    plan: FleetPlan,
    drivers: list[Driver] | tuple[Driver, ...],
    loads: list[Load] | tuple[Load, ...],
    *,
    changed_assignments: int = 0,
    preserved_assignments: int = 0,
) -> PlanMetrics:
    drivers_by_id = {driver.id: driver for driver in drivers}
    loads_by_id = {load.id: load for load in loads}
    assigned_load_ids = {assignment.load_id for assignment in plan.assignments}
    hos_violations = 0
    late_loads = 0
    total_revenue_cents = 0

    for assignment in plan.assignments:
        driver = drivers_by_id.get(assignment.driver_id)
        load = loads_by_id.get(assignment.load_id)
        if driver is None or load is None:
            missing = assignment.driver_id if driver is None else assignment.load_id
            raise PlanReferenceError(f"Unknown plan reference: {missing}.")
        violations = evaluate_feasibility(driver, load).result.violations
        if any(item.code is ConstraintViolationCode.HOS_INSUFFICIENT for item in violations):
            hos_violations += 1
        if assignment.planned_delivery_at > load.delivery_end:
            late_loads += 1
        total_revenue_cents += load.revenue_cents

    return PlanMetrics(
        assigned_loads=len(plan.assignments),
        unassigned_loads=len(loads_by_id) - len(assigned_load_ids),
        committed_loads_unassigned=sum(
            load.committed and load.id not in assigned_load_ids for load in loads
        ),
        total_revenue_cents=total_revenue_cents,
        total_deadhead_minutes=sum(item.deadhead_minutes for item in plan.assignments),
        hos_violations=hos_violations,
        late_loads=late_loads,
        changed_assignments=changed_assignments,
        preserved_assignments=preserved_assignments,
    )


def calculate_metric_delta(before: PlanMetrics, after: PlanMetrics) -> PlanMetricDelta:
    return PlanMetricDelta(
        revenue_cents_delta=after.total_revenue_cents - before.total_revenue_cents,
        deadhead_minutes_delta=after.total_deadhead_minutes - before.total_deadhead_minutes,
        assigned_loads_delta=after.assigned_loads - before.assigned_loads,
        unassigned_loads_delta=after.unassigned_loads - before.unassigned_loads,
        committed_loads_unassigned_delta=(
            after.committed_loads_unassigned - before.committed_loads_unassigned
        ),
        hos_violations_delta=after.hos_violations - before.hos_violations,
        late_loads_delta=after.late_loads - before.late_loads,
        changed_assignments=after.changed_assignments - before.changed_assignments,
    )
