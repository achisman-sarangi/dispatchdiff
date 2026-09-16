import type {
  Assignment,
  Driver,
  Load,
  OperationalDisruption,
  PlanBuildResult,
  ReplanResult,
} from "../api/types";

export const drivers: Driver[] = [
  { id: "DRV-001", name: "Maya Torres", current_city: "Atlanta", current_state: "GA", available_at: "2025-03-10T07:00:00-04:00", hos_remaining_minutes: 660, home_city: "Atlanta", home_state: "GA", home_deadline: null, equipment_type: "DRY_VAN", status: "AVAILABLE" },
  { id: "DRV-002", name: "Eli Brooks", current_city: "Savannah", current_state: "GA", available_at: "2025-03-10T07:00:00-04:00", hos_remaining_minutes: 480, home_city: "Charlotte", home_state: "NC", home_deadline: null, equipment_type: "REEFER", status: "AVAILABLE" },
];

export const loads: Load[] = [
  { id: "LOAD-001", origin_city: "Atlanta", origin_state: "GA", destination_city: "Charlotte", destination_state: "NC", pickup_start: "2025-03-10T08:00:00-04:00", pickup_end: "2025-03-10T10:00:00-04:00", delivery_start: "2025-03-10T12:00:00-04:00", delivery_end: "2025-03-10T15:00:00-04:00", estimated_drive_minutes: 240, estimated_deadhead_minutes: 30, revenue_cents: 185000, required_equipment_type: "DRY_VAN", committed: true },
  { id: "LOAD-002", origin_city: "Savannah", origin_state: "GA", destination_city: "Orlando", destination_state: "FL", pickup_start: "2025-03-10T09:00:00-04:00", pickup_end: "2025-03-10T11:00:00-04:00", delivery_start: "2025-03-10T14:00:00-04:00", delivery_end: "2025-03-10T18:00:00-04:00", estimated_drive_minutes: 270, estimated_deadhead_minutes: 45, revenue_cents: 220000, required_equipment_type: "REEFER", committed: false },
  { id: "LOAD-007", origin_city: "Orlando", origin_state: "FL", destination_city: "Miami", destination_state: "FL", pickup_start: "2025-03-10T15:00:00-04:00", pickup_end: "2025-03-10T17:00:00-04:00", delivery_start: "2025-03-10T19:00:00-04:00", delivery_end: "2025-03-10T23:00:00-04:00", estimated_drive_minutes: 300, estimated_deadhead_minutes: 30, revenue_cents: 190000, required_equipment_type: "DRY_VAN", committed: false },
];

const original: Assignment = { driver_id: "DRV-001", load_id: "LOAD-001", planned_pickup_at: "2025-03-10T08:00:00-04:00", planned_delivery_at: "2025-03-10T12:00:00-04:00", deadhead_minutes: 30, score: 1812.5 };
const preserved: Assignment = { driver_id: "DRV-002", load_id: "LOAD-002", planned_pickup_at: "2025-03-10T09:00:00-04:00", planned_delivery_at: "2025-03-10T13:30:00-04:00", deadhead_minutes: 45, score: 2143.75 };
const replacement: Assignment = { ...original, driver_id: "DRV-007" };
const added: Assignment = { driver_id: "DRV-001", load_id: "LOAD-007", planned_pickup_at: "2025-03-10T15:00:00-04:00", planned_delivery_at: "2025-03-10T20:00:00-04:00", deadhead_minutes: 30, score: 1862.5 };

export const plan: PlanBuildResult = {
  plan: { id: "plan-001", assignments: [original, preserved], created_at: "2025-01-01T00:00:00Z" },
  unassigned_load_ids: ["LOAD-007"],
  evaluation_summary: { total_loads: 3, assigned_loads: 5, unassigned_loads: 7, total_revenue_cents: 880000, total_deadhead_minutes: 160 },
};

export const disruption: OperationalDisruption = {
  id: "DISR-001", type: "DRIVER_DETENTION", driver_id: "DRV-001", occurred_at: "2025-03-10T07:00:00-04:00", detention_minutes: 180, hos_reduction_minutes: null, new_home_deadline: null, reason: "Customer detention at previous stop",
};

export const replan: ReplanResult = {
  disruption,
  previous_plan: plan.plan,
  proposed_plan: { id: "plan-001-after-DISR-001", assignments: [preserved, replacement, added], created_at: disruption.occurred_at },
  impacted_assignments: [{ driver_id: "DRV-001", load_id: "LOAD-001", impacted: true, reasons: [{ code: "PICKUP_WINDOW_MISSED", message: "Earliest pickup is after the pickup window end." }] }],
  preserved_assignments: [preserved, { ...preserved, driver_id: "DRV-003", load_id: "LOAD-003" }, { ...preserved, driver_id: "DRV-004", load_id: "LOAD-008" }, { ...preserved, driver_id: "DRV-005", load_id: "LOAD-005" }],
  removed_assignments: [original],
  added_assignments: [replacement, added],
  assignment_changes: [
    { change_type: "PRESERVED", driver_id: "DRV-002", load_id: "LOAD-002", previous_assignment: preserved, proposed_assignment: preserved, reason_codes: [], explanation: "Assignment preserved because it remains feasible and was not affected by the disruption." },
    { change_type: "REMOVED", driver_id: "DRV-001", load_id: "LOAD-001", previous_assignment: original, proposed_assignment: null, reason_codes: ["PICKUP_WINDOW_MISSED"], explanation: "Removed because Driver DRV-001 can no longer meet the pickup window." },
    { change_type: "ADDED", driver_id: "DRV-007", load_id: "LOAD-001", previous_assignment: original, proposed_assignment: replacement, reason_codes: ["PICKUP_WINDOW_MISSED"], explanation: "Load LOAD-001 reassigned from Driver DRV-001 to Driver DRV-007 after a 180-minute detention caused PICKUP_WINDOW_MISSED." },
    { change_type: "ADDED", driver_id: "DRV-001", load_id: "LOAD-007", previous_assignment: null, proposed_assignment: added, reason_codes: [], explanation: "Load LOAD-007 assigned to Driver DRV-001 from the previously unassigned load pool." },
  ],
  still_unassigned_load_ids: [],
  resolved_violations: [{ code: "PICKUP_WINDOW_MISSED", message: "Pickup missed" }],
  remaining_violations: [],
  metrics: {
    before_metrics: { assigned_loads: 5, unassigned_loads: 7, committed_loads_unassigned: 0, total_revenue_cents: 880000, total_deadhead_minutes: 160, hos_violations: 0, late_loads: 0, changed_assignments: 0, preserved_assignments: 5 },
    after_metrics: { assigned_loads: 6, unassigned_loads: 6, committed_loads_unassigned: 0, total_revenue_cents: 1070000, total_deadhead_minutes: 190, hos_violations: 0, late_loads: 0, changed_assignments: 3, preserved_assignments: 4 },
    delta: { revenue_cents_delta: 190000, deadhead_minutes_delta: 30, assigned_loads_delta: 1, unassigned_loads_delta: -1, committed_loads_unassigned_delta: 0, hos_violations_delta: 0, late_loads_delta: 0, changed_assignments: 3 },
  },
};
