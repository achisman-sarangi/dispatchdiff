from dataclasses import dataclass
from datetime import datetime

from app.disruptions.service import apply_disruption
from app.domain.errors import PlanReferenceError
from app.domain.models import Assignment, Driver, FleetPlan, Load, OperationalDisruption
from app.planning.feasibility import ConstraintViolation
from app.planning.service import PlanningService
from app.replanning.diff import AssignmentChange, build_assignment_changes
from app.replanning.impact import AssignmentImpact, evaluate_plan_impact
from app.replanning.metrics import (
    ReplanMetrics,
    calculate_metric_delta,
    calculate_plan_metrics,
)


@dataclass(frozen=True, slots=True)
class ReplanResult:
    disruption: OperationalDisruption
    previous_plan: FleetPlan
    proposed_plan: FleetPlan
    impacted_assignments: tuple[AssignmentImpact, ...]
    preserved_assignments: tuple[Assignment, ...]
    removed_assignments: tuple[Assignment, ...]
    added_assignments: tuple[Assignment, ...]
    assignment_changes: tuple[AssignmentChange, ...]
    still_unassigned_load_ids: tuple[str, ...]
    resolved_violations: tuple[ConstraintViolation, ...]
    remaining_violations: tuple[ConstraintViolation, ...]
    metrics: ReplanMetrics


class ReplanningService:
    def __init__(self, planning_service: PlanningService | None = None) -> None:
        self._planning_service = planning_service or PlanningService()

    def replan_after_disruption(
        self,
        drivers: list[Driver] | tuple[Driver, ...],
        loads: list[Load] | tuple[Load, ...],
        current_plan: FleetPlan,
        disruption: OperationalDisruption,
    ) -> ReplanResult:
        updated_drivers = self._apply_to_fleet(drivers, disruption)
        all_impacts = evaluate_plan_impact(current_plan, updated_drivers, loads)
        impacted = tuple(impact for impact in all_impacts if impact.impacted)
        impacted_keys = {(impact.driver_id, impact.load_id) for impact in impacted}
        preserved = tuple(
            assignment
            for assignment in current_plan.assignments
            if (assignment.driver_id, assignment.load_id) not in impacted_keys
        )
        removed = tuple(
            assignment
            for assignment in current_plan.assignments
            if (assignment.driver_id, assignment.load_id) in impacted_keys
        )
        reasons_by_load_id = {impact.load_id: impact.reasons for impact in impacted}

        added = self._build_replacements(updated_drivers, loads, current_plan, preserved, impacted)
        proposed_plan = FleetPlan(
            id=f"{current_plan.id}-after-{disruption.id}",
            assignments=preserved + added,
            created_at=disruption.occurred_at,
        )
        proposed_load_ids = {assignment.load_id for assignment in proposed_plan.assignments}
        still_unassigned = tuple(
            sorted(load.id for load in loads if load.id not in proposed_load_ids)
        )
        resolved = tuple(
            reason
            for impact in impacted
            if impact.load_id in proposed_load_ids
            for reason in impact.reasons
        )
        remaining = tuple(
            reason
            for impact in impacted
            if impact.load_id not in proposed_load_ids
            for reason in impact.reasons
        )
        changes = build_assignment_changes(
            preserved, removed, added, reasons_by_load_id, disruption
        )
        before = calculate_plan_metrics(
            current_plan,
            drivers,
            loads,
            preserved_assignments=len(current_plan.assignments),
        )
        after = calculate_plan_metrics(
            proposed_plan,
            updated_drivers,
            loads,
            changed_assignments=len(removed) + len(added),
            preserved_assignments=len(preserved),
        )
        return ReplanResult(
            disruption=disruption,
            previous_plan=current_plan,
            proposed_plan=proposed_plan,
            impacted_assignments=impacted,
            preserved_assignments=preserved,
            removed_assignments=removed,
            added_assignments=added,
            assignment_changes=changes,
            still_unassigned_load_ids=still_unassigned,
            resolved_violations=resolved,
            remaining_violations=remaining,
            metrics=ReplanMetrics(before, after, calculate_metric_delta(before, after)),
        )

    @staticmethod
    def _apply_to_fleet(
        drivers: list[Driver] | tuple[Driver, ...], disruption: OperationalDisruption
    ) -> tuple[Driver, ...]:
        if not any(driver.id == disruption.driver_id for driver in drivers):
            raise PlanReferenceError(f"Unknown disruption driver: {disruption.driver_id}.")
        return tuple(
            apply_disruption(driver, disruption) if driver.id == disruption.driver_id else driver
            for driver in drivers
        )

    def _build_replacements(
        self,
        drivers: tuple[Driver, ...],
        loads: list[Load] | tuple[Load, ...],
        current_plan: FleetPlan,
        preserved: tuple[Assignment, ...],
        impacted: tuple[AssignmentImpact, ...],
    ) -> tuple[Assignment, ...]:
        loads_by_id = {load.id: load for load in loads}
        current_load_ids = {assignment.load_id for assignment in current_plan.assignments}
        impacted_load_ids = {impact.load_id for impact in impacted}
        occupied_driver_ids = {assignment.driver_id for assignment in preserved}

        def priority(load: Load) -> tuple[int, datetime, str]:
            if load.id in impacted_load_ids:
                category = 0 if load.committed else 1
            else:
                category = 2 if load.committed else 3
            return category, load.pickup_end, load.id

        eligible_loads = [
            load
            for load in loads_by_id.values()
            if load.id in impacted_load_ids or load.id not in current_load_ids
        ]
        added: list[Assignment] = []
        for load in sorted(eligible_loads, key=priority):
            available_drivers = [
                driver for driver in drivers if driver.id not in occupied_driver_ids
            ]
            candidates = self._planning_service.rank_feasible_drivers(load, available_drivers)
            if not candidates:
                continue
            selected = candidates[0]
            added.append(
                Assignment(
                    driver_id=selected.driver.id,
                    load_id=load.id,
                    planned_pickup_at=selected.planned_pickup_at,
                    planned_delivery_at=selected.planned_delivery_at,
                    deadhead_minutes=load.estimated_deadhead_minutes,
                    score=selected.score,
                )
            )
            occupied_driver_ids.add(selected.driver.id)
        return tuple(added)
