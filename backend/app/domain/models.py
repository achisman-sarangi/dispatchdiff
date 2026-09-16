from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import DriverStatus, OperationalDisruptionType


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class Driver:
    id: str
    name: str
    current_city: str
    current_state: str
    available_at: datetime
    hos_remaining_minutes: int
    home_city: str
    home_state: str
    home_deadline: datetime | None
    equipment_type: str
    status: DriverStatus

    def __post_init__(self) -> None:
        _require_aware(self.available_at, "available_at")
        if self.home_deadline is not None:
            _require_aware(self.home_deadline, "home_deadline")
        if self.hos_remaining_minutes < 0:
            raise ValueError("hos_remaining_minutes cannot be negative")


@dataclass(frozen=True, slots=True)
class Load:
    id: str
    origin_city: str
    origin_state: str
    destination_city: str
    destination_state: str
    pickup_start: datetime
    pickup_end: datetime
    delivery_start: datetime
    delivery_end: datetime
    estimated_drive_minutes: int
    estimated_deadhead_minutes: int
    revenue_cents: int
    required_equipment_type: str
    committed: bool

    def __post_init__(self) -> None:
        for name in ("pickup_start", "pickup_end", "delivery_start", "delivery_end"):
            _require_aware(getattr(self, name), name)
        if self.pickup_start > self.pickup_end:
            raise ValueError("pickup_start cannot be after pickup_end")
        if self.delivery_start > self.delivery_end:
            raise ValueError("delivery_start cannot be after delivery_end")
        if self.estimated_drive_minutes < 0 or self.estimated_deadhead_minutes < 0:
            raise ValueError("estimated travel minutes cannot be negative")
        if self.revenue_cents < 0:
            raise ValueError("revenue_cents cannot be negative")


@dataclass(frozen=True, slots=True)
class Assignment:
    driver_id: str
    load_id: str
    planned_pickup_at: datetime
    planned_delivery_at: datetime
    deadhead_minutes: int
    score: float


@dataclass(frozen=True, slots=True)
class FleetPlan:
    id: str
    assignments: tuple[Assignment, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class OperationalDisruption:
    id: str
    type: OperationalDisruptionType
    driver_id: str
    occurred_at: datetime
    detention_minutes: int | None
    hos_reduction_minutes: int | None
    new_home_deadline: datetime | None
    reason: str

    def __post_init__(self) -> None:
        _require_aware(self.occurred_at, "occurred_at")
        if self.new_home_deadline is not None:
            _require_aware(self.new_home_deadline, "new_home_deadline")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")

        supplied = {
            "detention_minutes": self.detention_minutes,
            "hos_reduction_minutes": self.hos_reduction_minutes,
            "new_home_deadline": self.new_home_deadline,
        }
        required_field = {
            OperationalDisruptionType.DRIVER_DETENTION: "detention_minutes",
            OperationalDisruptionType.HOS_REDUCTION: "hos_reduction_minutes",
            OperationalDisruptionType.HOME_DEADLINE_CHANGE: "new_home_deadline",
            OperationalDisruptionType.DRIVER_UNAVAILABLE: None,
        }[self.type]
        unexpected = [
            name for name, value in supplied.items() if value is not None and name != required_field
        ]
        if unexpected:
            raise ValueError(f"{self.type.value} does not accept: {', '.join(sorted(unexpected))}")
        if required_field is None:
            return
        required_value = supplied[required_field]
        if required_value is None:
            raise ValueError(f"{required_field} is required for {self.type.value}")
        if isinstance(required_value, int) and required_value <= 0:
            raise ValueError(f"{required_field} must be greater than zero")
