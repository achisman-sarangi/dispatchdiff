from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.enums import ConstraintViolationCode, DriverStatus
from app.domain.models import Driver, Load


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    code: ConstraintViolationCode
    message: str


@dataclass(frozen=True, slots=True)
class FeasibilityResult:
    feasible: bool
    violations: tuple[ConstraintViolation, ...]


@dataclass(frozen=True, slots=True)
class FeasibilityEvaluation:
    result: FeasibilityResult
    planned_pickup_at: datetime
    planned_delivery_at: datetime


def evaluate_feasibility(driver: Driver, load: Load) -> FeasibilityEvaluation:
    arrival_at_origin = driver.available_at + timedelta(minutes=load.estimated_deadhead_minutes)
    planned_pickup_at = max(arrival_at_origin, load.pickup_start)
    planned_delivery_at = planned_pickup_at + timedelta(minutes=load.estimated_drive_minutes)
    violations: list[ConstraintViolation] = []

    if driver.status is not DriverStatus.AVAILABLE:
        violations.append(
            ConstraintViolation(
                ConstraintViolationCode.DRIVER_NOT_AVAILABLE,
                f"Driver {driver.id} has status {driver.status.value}, not AVAILABLE.",
            )
        )
    if driver.equipment_type != load.required_equipment_type:
        violations.append(
            ConstraintViolation(
                ConstraintViolationCode.EQUIPMENT_MISMATCH,
                f"Driver equipment {driver.equipment_type} does not match required "
                f"equipment {load.required_equipment_type}.",
            )
        )
    if planned_pickup_at > load.pickup_end:
        violations.append(
            ConstraintViolation(
                ConstraintViolationCode.PICKUP_WINDOW_MISSED,
                f"Earliest pickup {planned_pickup_at.isoformat()} is after pickup window "
                f"end {load.pickup_end.isoformat()}.",
            )
        )
    if planned_delivery_at > load.delivery_end:
        violations.append(
            ConstraintViolation(
                ConstraintViolationCode.DELIVERY_WINDOW_MISSED,
                f"Planned delivery {planned_delivery_at.isoformat()} is after delivery "
                f"window end {load.delivery_end.isoformat()}.",
            )
        )

    required_minutes = load.estimated_deadhead_minutes + load.estimated_drive_minutes
    if required_minutes > driver.hos_remaining_minutes:
        violations.append(
            ConstraintViolation(
                ConstraintViolationCode.HOS_INSUFFICIENT,
                f"Assignment requires {required_minutes} HOS minutes; driver has "
                f"{driver.hos_remaining_minutes} remaining.",
            )
        )

    # Milestone 1 intentionally treats delivery by the deadline as sufficient;
    # later planning will account for travel from destination to the driver's home.
    if driver.home_deadline is not None and planned_delivery_at > driver.home_deadline:
        violations.append(
            ConstraintViolation(
                ConstraintViolationCode.HOME_TIME_VIOLATION,
                f"Planned delivery {planned_delivery_at.isoformat()} is after driver home "
                f"deadline {driver.home_deadline.isoformat()}.",
            )
        )

    return FeasibilityEvaluation(
        result=FeasibilityResult(feasible=not violations, violations=tuple(violations)),
        planned_pickup_at=planned_pickup_at,
        planned_delivery_at=planned_delivery_at,
    )
