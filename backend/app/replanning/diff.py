from dataclasses import dataclass

from app.domain.enums import AssignmentChangeType, ConstraintViolationCode
from app.domain.models import Assignment, OperationalDisruption
from app.planning.feasibility import ConstraintViolation


@dataclass(frozen=True, slots=True)
class AssignmentChange:
    change_type: AssignmentChangeType
    driver_id: str
    load_id: str
    previous_assignment: Assignment | None
    proposed_assignment: Assignment | None
    reason_codes: tuple[ConstraintViolationCode, ...]
    explanation: str


def _removal_explanation(assignment: Assignment, reasons: tuple[ConstraintViolation, ...]) -> str:
    labels = {
        ConstraintViolationCode.DRIVER_NOT_AVAILABLE: "is no longer available",
        ConstraintViolationCode.EQUIPMENT_MISMATCH: "no longer has compatible equipment",
        ConstraintViolationCode.PICKUP_WINDOW_MISSED: "can no longer meet the pickup window",
        ConstraintViolationCode.DELIVERY_WINDOW_MISSED: "can no longer meet the delivery window",
        ConstraintViolationCode.HOS_INSUFFICIENT: "no longer has sufficient HOS",
        ConstraintViolationCode.HOME_TIME_VIOLATION: "can no longer meet the home deadline",
    }
    cause = "; ".join(labels[reason.code] for reason in reasons)
    return f"Removed because Driver {assignment.driver_id} {cause}."


def _disruption_description(disruption: OperationalDisruption) -> str:
    if disruption.detention_minutes is not None:
        return f"a {disruption.detention_minutes}-minute detention"
    if disruption.hos_reduction_minutes is not None:
        return f"a {disruption.hos_reduction_minutes}-minute HOS reduction"
    if disruption.new_home_deadline is not None:
        return f"a home deadline change to {disruption.new_home_deadline.isoformat()}"
    return "the driver becoming unavailable"


def build_assignment_changes(
    preserved: tuple[Assignment, ...],
    removed: tuple[Assignment, ...],
    added: tuple[Assignment, ...],
    reasons_by_load_id: dict[str, tuple[ConstraintViolation, ...]],
    disruption: OperationalDisruption,
) -> tuple[AssignmentChange, ...]:
    changes: list[AssignmentChange] = []
    removed_by_load_id = {assignment.load_id: assignment for assignment in removed}

    for assignment in preserved:
        changes.append(
            AssignmentChange(
                AssignmentChangeType.PRESERVED,
                assignment.driver_id,
                assignment.load_id,
                assignment,
                assignment,
                (),
                "Assignment preserved because it remains feasible and was not affected "
                "by the disruption.",
            )
        )
    for assignment in removed:
        reasons = reasons_by_load_id[assignment.load_id]
        changes.append(
            AssignmentChange(
                AssignmentChangeType.REMOVED,
                assignment.driver_id,
                assignment.load_id,
                assignment,
                None,
                tuple(reason.code for reason in reasons),
                _removal_explanation(assignment, reasons),
            )
        )
    for assignment in added:
        previous = removed_by_load_id.get(assignment.load_id)
        reasons = reasons_by_load_id.get(assignment.load_id, ())
        if previous is None:
            explanation = (
                f"Load {assignment.load_id} assigned to Driver {assignment.driver_id} "
                "from the previously unassigned load pool."
            )
        else:
            codes = ", ".join(reason.code.value for reason in reasons)
            explanation = (
                f"Load {assignment.load_id} reassigned from Driver {previous.driver_id} "
                f"to Driver {assignment.driver_id} after {_disruption_description(disruption)} "
                f"caused {codes}."
            )
        changes.append(
            AssignmentChange(
                AssignmentChangeType.ADDED,
                assignment.driver_id,
                assignment.load_id,
                previous,
                assignment,
                tuple(reason.code for reason in reasons),
                explanation,
            )
        )
    return tuple(changes)
