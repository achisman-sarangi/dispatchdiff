from dataclasses import replace
from datetime import datetime, timedelta
from typing import cast

from app.domain.enums import DriverStatus, OperationalDisruptionType
from app.domain.errors import DisruptionDriverMismatchError
from app.domain.models import Driver, OperationalDisruption


def apply_disruption(driver: Driver, disruption: OperationalDisruption) -> Driver:
    if driver.id != disruption.driver_id:
        raise DisruptionDriverMismatchError(
            f"Disruption targets driver {disruption.driver_id}, not {driver.id}."
        )

    if disruption.type is OperationalDisruptionType.DRIVER_DETENTION:
        detention_minutes = cast(int, disruption.detention_minutes)
        return replace(
            driver,
            available_at=driver.available_at + timedelta(minutes=detention_minutes),
        )
    if disruption.type is OperationalDisruptionType.HOS_REDUCTION:
        hos_reduction_minutes = cast(int, disruption.hos_reduction_minutes)
        return replace(
            driver,
            hos_remaining_minutes=max(0, driver.hos_remaining_minutes - hos_reduction_minutes),
        )
    if disruption.type is OperationalDisruptionType.HOME_DEADLINE_CHANGE:
        new_home_deadline = cast(datetime, disruption.new_home_deadline)
        return replace(driver, home_deadline=new_home_deadline)
    return replace(driver, status=DriverStatus.UNAVAILABLE)
