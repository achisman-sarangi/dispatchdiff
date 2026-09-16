from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.domain.enums import (
    AssignmentChangeType,
    ConstraintViolationCode,
    DriverStatus,
    OperationalDisruptionType,
)
from app.domain.models import OperationalDisruption


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DriverResponse(ApiModel):
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


class LoadResponse(ApiModel):
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


class AssignmentResponse(ApiModel):
    driver_id: str
    load_id: str
    planned_pickup_at: datetime
    planned_delivery_at: datetime
    deadhead_minutes: int
    score: float


class FleetPlanResponse(ApiModel):
    id: str
    assignments: list[AssignmentResponse]
    created_at: datetime


class EvaluationSummaryResponse(ApiModel):
    total_loads: int
    assigned_loads: int
    unassigned_loads: int
    total_revenue_cents: int
    total_deadhead_minutes: int


class PlanBuildResponse(ApiModel):
    plan: FleetPlanResponse
    unassigned_load_ids: list[str]
    evaluation_summary: EvaluationSummaryResponse


class ConstraintViolationResponse(ApiModel):
    code: ConstraintViolationCode
    message: str


class EvaluateRequest(BaseModel):
    driver_id: str
    load_id: str


class EvaluateResponse(BaseModel):
    driver_id: str
    load_id: str
    feasible: bool
    violations: list[ConstraintViolationResponse]
    planned_pickup_at: datetime
    planned_delivery_at: datetime
    score: float | None


class OperationalDisruptionResponse(ApiModel):
    id: str
    type: OperationalDisruptionType
    driver_id: str
    occurred_at: datetime
    detention_minutes: int | None
    hos_reduction_minutes: int | None
    new_home_deadline: datetime | None
    reason: str


class OperationalDisruptionRequest(BaseModel):
    id: str
    type: OperationalDisruptionType
    driver_id: str
    occurred_at: datetime
    detention_minutes: int | None = None
    hos_reduction_minutes: int | None = None
    new_home_deadline: datetime | None = None
    reason: str

    @model_validator(mode="after")
    def validate_domain_rules(self) -> Self:
        self.to_domain()
        return self

    def to_domain(self) -> OperationalDisruption:
        return OperationalDisruption(**self.model_dump())


class ReplanRequest(BaseModel):
    disruption: OperationalDisruptionRequest


class AssignmentImpactResponse(ApiModel):
    driver_id: str
    load_id: str
    impacted: bool
    reasons: list[ConstraintViolationResponse]


class AssignmentChangeResponse(ApiModel):
    change_type: AssignmentChangeType
    driver_id: str
    load_id: str
    previous_assignment: AssignmentResponse | None
    proposed_assignment: AssignmentResponse | None
    reason_codes: list[ConstraintViolationCode]
    explanation: str


class PlanMetricsResponse(ApiModel):
    assigned_loads: int
    unassigned_loads: int
    committed_loads_unassigned: int
    total_revenue_cents: int
    total_deadhead_minutes: int
    hos_violations: int
    late_loads: int
    changed_assignments: int
    preserved_assignments: int


class PlanMetricDeltaResponse(ApiModel):
    revenue_cents_delta: int
    deadhead_minutes_delta: int
    assigned_loads_delta: int
    unassigned_loads_delta: int
    committed_loads_unassigned_delta: int
    hos_violations_delta: int
    late_loads_delta: int
    changed_assignments: int


class ReplanMetricsResponse(ApiModel):
    before_metrics: PlanMetricsResponse
    after_metrics: PlanMetricsResponse
    delta: PlanMetricDeltaResponse


class ReplanResponse(ApiModel):
    disruption: OperationalDisruptionResponse
    previous_plan: FleetPlanResponse
    proposed_plan: FleetPlanResponse
    impacted_assignments: list[AssignmentImpactResponse]
    preserved_assignments: list[AssignmentResponse]
    removed_assignments: list[AssignmentResponse]
    added_assignments: list[AssignmentResponse]
    assignment_changes: list[AssignmentChangeResponse]
    still_unassigned_load_ids: list[str]
    resolved_violations: list[ConstraintViolationResponse]
    remaining_violations: list[ConstraintViolationResponse]
    metrics: ReplanMetricsResponse
