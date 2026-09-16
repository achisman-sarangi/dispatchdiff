from dataclasses import replace
from datetime import timedelta

import pytest

from app.disruptions.service import apply_disruption
from app.domain.enums import DriverStatus, OperationalDisruptionType
from app.domain.errors import DisruptionDriverMismatchError
from app.domain.models import OperationalDisruption
from app.seed.demo_data import DEMO_DRIVERS, get_demo_disruption


def disruption(
    disruption_type: OperationalDisruptionType,
    *,
    detention_minutes: int | None = None,
    hos_reduction_minutes: int | None = None,
    new_home_deadline=None,
) -> OperationalDisruption:
    demo = get_demo_disruption()
    return OperationalDisruption(
        id="TEST-DISRUPTION",
        type=disruption_type,
        driver_id=DEMO_DRIVERS[0].id,
        occurred_at=demo.occurred_at,
        detention_minutes=detention_minutes,
        hos_reduction_minutes=hos_reduction_minutes,
        new_home_deadline=new_home_deadline,
        reason="Test disruption",
    )


def test_detention_moves_available_at_forward_without_mutation() -> None:
    original = DEMO_DRIVERS[0]
    updated = apply_disruption(original, get_demo_disruption())
    assert updated.available_at == original.available_at + timedelta(minutes=180)
    assert original.available_at == DEMO_DRIVERS[0].available_at
    assert updated is not original


def test_hos_reduction_decreases_hos_and_floors_at_zero() -> None:
    reduced = apply_disruption(
        DEMO_DRIVERS[0],
        disruption(OperationalDisruptionType.HOS_REDUCTION, hos_reduction_minutes=60),
    )
    floored = apply_disruption(
        DEMO_DRIVERS[0],
        disruption(OperationalDisruptionType.HOS_REDUCTION, hos_reduction_minutes=9999),
    )
    assert reduced.hos_remaining_minutes == DEMO_DRIVERS[0].hos_remaining_minutes - 60
    assert floored.hos_remaining_minutes == 0


def test_home_deadline_replacement_works() -> None:
    deadline = get_demo_disruption().occurred_at + timedelta(hours=8)
    updated = apply_disruption(
        DEMO_DRIVERS[0],
        disruption(
            OperationalDisruptionType.HOME_DEADLINE_CHANGE,
            new_home_deadline=deadline,
        ),
    )
    assert updated.home_deadline == deadline


def test_unavailable_disruption_updates_status() -> None:
    updated = apply_disruption(
        DEMO_DRIVERS[0], disruption(OperationalDisruptionType.DRIVER_UNAVAILABLE)
    )
    assert updated.status is DriverStatus.UNAVAILABLE


@pytest.mark.parametrize(
    ("kind", "kwargs"),
    [
        (OperationalDisruptionType.DRIVER_DETENTION, {}),
        (OperationalDisruptionType.DRIVER_DETENTION, {"detention_minutes": 0}),
        (OperationalDisruptionType.HOS_REDUCTION, {"hos_reduction_minutes": -1}),
        (
            OperationalDisruptionType.DRIVER_UNAVAILABLE,
            {"detention_minutes": 30},
        ),
    ],
)
def test_malformed_disruptions_are_rejected(kind, kwargs) -> None:
    with pytest.raises(ValueError):
        disruption(kind, **kwargs)


def test_driver_mismatch_is_rejected() -> None:
    with pytest.raises(DisruptionDriverMismatchError):
        apply_disruption(DEMO_DRIVERS[1], get_demo_disruption())


def test_original_driver_is_not_mutated_for_every_disruption_type() -> None:
    original = DEMO_DRIVERS[0]
    snapshot = replace(original)
    apply_disruption(original, get_demo_disruption())
    assert original == snapshot
