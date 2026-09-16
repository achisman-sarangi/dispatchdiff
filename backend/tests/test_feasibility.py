from dataclasses import replace
from datetime import timedelta

from app.domain.enums import ConstraintViolationCode, DriverStatus
from app.planning.feasibility import evaluate_feasibility
from app.seed.demo_data import DEMO_DRIVERS, DEMO_LOADS


def codes(driver_index: int = 0, load_index: int = 0) -> set[ConstraintViolationCode]:
    evaluation = evaluate_feasibility(DEMO_DRIVERS[driver_index], DEMO_LOADS[load_index])
    return {violation.code for violation in evaluation.result.violations}


def test_feasible_assignment() -> None:
    evaluation = evaluate_feasibility(DEMO_DRIVERS[0], DEMO_LOADS[0])
    assert evaluation.result.feasible is True
    assert evaluation.result.violations == ()


def test_unavailable_driver() -> None:
    assert ConstraintViolationCode.DRIVER_NOT_AVAILABLE in codes(5, 1)


def test_equipment_mismatch() -> None:
    assert ConstraintViolationCode.EQUIPMENT_MISMATCH in codes(0, 1)


def test_missed_pickup_window() -> None:
    driver = replace(DEMO_DRIVERS[0], available_at=DEMO_LOADS[0].pickup_end)
    assert ConstraintViolationCode.PICKUP_WINDOW_MISSED in {
        item.code for item in evaluate_feasibility(driver, DEMO_LOADS[0]).result.violations
    }


def test_missed_delivery_window() -> None:
    early_delivery_end = DEMO_LOADS[0].pickup_start + timedelta(minutes=120)
    load = replace(
        DEMO_LOADS[0],
        delivery_start=early_delivery_end,
        delivery_end=early_delivery_end,
    )
    assert ConstraintViolationCode.DELIVERY_WINDOW_MISSED in {
        item.code for item in evaluate_feasibility(DEMO_DRIVERS[0], load).result.violations
    }


def test_insufficient_hos() -> None:
    driver = replace(DEMO_DRIVERS[0], hos_remaining_minutes=100)
    assert ConstraintViolationCode.HOS_INSUFFICIENT in {
        item.code for item in evaluate_feasibility(driver, DEMO_LOADS[0]).result.violations
    }


def test_home_time_violation() -> None:
    driver = replace(DEMO_DRIVERS[0], home_deadline=DEMO_LOADS[0].pickup_start)
    assert ConstraintViolationCode.HOME_TIME_VIOLATION in {
        item.code for item in evaluate_feasibility(driver, DEMO_LOADS[0]).result.violations
    }


def test_multiple_violations_are_returned() -> None:
    driver = replace(
        DEMO_DRIVERS[0],
        status=DriverStatus.UNAVAILABLE,
        equipment_type="FLATBED",
        available_at=DEMO_LOADS[0].pickup_end,
        hos_remaining_minutes=0,
        home_deadline=DEMO_LOADS[0].pickup_start,
    )
    found = {item.code for item in evaluate_feasibility(driver, DEMO_LOADS[0]).result.violations}
    assert {
        ConstraintViolationCode.DRIVER_NOT_AVAILABLE,
        ConstraintViolationCode.EQUIPMENT_MISMATCH,
        ConstraintViolationCode.PICKUP_WINDOW_MISSED,
        ConstraintViolationCode.HOS_INSUFFICIENT,
        ConstraintViolationCode.HOME_TIME_VIOLATION,
    } <= found
