export type DriverStatus = "AVAILABLE" | "ASSIGNED" | "OFF_DUTY" | "UNAVAILABLE";
export type DisruptionType =
  | "DRIVER_DETENTION"
  | "HOS_REDUCTION"
  | "HOME_DEADLINE_CHANGE"
  | "DRIVER_UNAVAILABLE";
export type ChangeType = "PRESERVED" | "REMOVED" | "ADDED";
export type ConstraintViolationCode =
  | "DRIVER_NOT_AVAILABLE"
  | "EQUIPMENT_MISMATCH"
  | "PICKUP_WINDOW_MISSED"
  | "DELIVERY_WINDOW_MISSED"
  | "HOS_INSUFFICIENT"
  | "HOME_TIME_VIOLATION";

export interface Driver {
  id: string;
  name: string;
  current_city: string;
  current_state: string;
  available_at: string;
  hos_remaining_minutes: number;
  home_city: string;
  home_state: string;
  home_deadline: string | null;
  equipment_type: string;
  status: DriverStatus;
}

export interface Load {
  id: string;
  origin_city: string;
  origin_state: string;
  destination_city: string;
  destination_state: string;
  pickup_start: string;
  pickup_end: string;
  delivery_start: string;
  delivery_end: string;
  estimated_drive_minutes: number;
  estimated_deadhead_minutes: number;
  revenue_cents: number;
  required_equipment_type: string;
  committed: boolean;
}

export interface Assignment {
  driver_id: string;
  load_id: string;
  planned_pickup_at: string;
  planned_delivery_at: string;
  deadhead_minutes: number;
  score: number;
}

export interface FleetPlan {
  id: string;
  assignments: Assignment[];
  created_at: string;
}

export interface PlanSummary {
  total_loads: number;
  assigned_loads: number;
  unassigned_loads: number;
  total_revenue_cents: number;
  total_deadhead_minutes: number;
}

export interface PlanBuildResult {
  plan: FleetPlan;
  unassigned_load_ids: string[];
  evaluation_summary: PlanSummary;
}

export interface ConstraintViolation {
  code: ConstraintViolationCode;
  message: string;
}

export interface OperationalDisruption {
  id: string;
  type: DisruptionType;
  driver_id: string;
  occurred_at: string;
  detention_minutes: number | null;
  hos_reduction_minutes: number | null;
  new_home_deadline: string | null;
  reason: string;
}

export interface AssignmentImpact {
  driver_id: string;
  load_id: string;
  impacted: boolean;
  reasons: ConstraintViolation[];
}

export interface AssignmentChange {
  change_type: ChangeType;
  driver_id: string;
  load_id: string;
  previous_assignment: Assignment | null;
  proposed_assignment: Assignment | null;
  reason_codes: ConstraintViolationCode[];
  explanation: string;
}

export interface PlanMetrics {
  assigned_loads: number;
  unassigned_loads: number;
  committed_loads_unassigned: number;
  total_revenue_cents: number;
  total_deadhead_minutes: number;
  hos_violations: number;
  late_loads: number;
  changed_assignments: number;
  preserved_assignments: number;
}

export interface PlanMetricDelta {
  revenue_cents_delta: number;
  deadhead_minutes_delta: number;
  assigned_loads_delta: number;
  unassigned_loads_delta: number;
  committed_loads_unassigned_delta: number;
  hos_violations_delta: number;
  late_loads_delta: number;
  changed_assignments: number;
}

export interface ReplanResult {
  disruption: OperationalDisruption;
  previous_plan: FleetPlan;
  proposed_plan: FleetPlan;
  impacted_assignments: AssignmentImpact[];
  preserved_assignments: Assignment[];
  removed_assignments: Assignment[];
  added_assignments: Assignment[];
  assignment_changes: AssignmentChange[];
  still_unassigned_load_ids: string[];
  resolved_violations: ConstraintViolation[];
  remaining_violations: ConstraintViolation[];
  metrics: {
    before_metrics: PlanMetrics;
    after_metrics: PlanMetrics;
    delta: PlanMetricDelta;
  };
}
