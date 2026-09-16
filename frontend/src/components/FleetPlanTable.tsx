import { useState } from "react";

import type { Assignment, Driver, Load, PlanBuildResult } from "../api/types";
import { formatDateTime, routeLabel } from "../utils/format";

interface FleetPlanTableProps {
  planResult: PlanBuildResult;
  drivers: Driver[];
  loads: Load[];
}

export function FleetPlanTable({ planResult, drivers, loads }: FleetPlanTableProps) {
  const [openLoadsVisible, setOpenLoadsVisible] = useState(false);
  const driversById = new Map(drivers.map((driver) => [driver.id, driver]));
  const loadsById = new Map(loads.map((load) => [load.id, load]));
  const unassignedLoads = planResult.unassigned_load_ids
    .map((id) => loadsById.get(id))
    .filter((load): load is Load => load !== undefined);

  return (
    <div className="plan-table-wrap">
      <div className="table-scroll">
        <table>
          <thead>
            <tr><th>Driver</th><th>Load</th><th>Lane</th><th>Pickup</th><th>Delivery</th><th>Deadhead</th><th>Status</th></tr>
          </thead>
          <tbody>
            {planResult.plan.assignments.map((assignment) => (
              <PlanRow key={`${assignment.driver_id}-${assignment.load_id}`} assignment={assignment} driver={driversById.get(assignment.driver_id)} load={loadsById.get(assignment.load_id)} />
            ))}
          </tbody>
        </table>
      </div>
      <div className="open-loads-control">
        <div><strong>{unassignedLoads.length} Open Loads</strong><span>Available for assignment</span></div>
        <button type="button" className="text-button" aria-expanded={openLoadsVisible} onClick={() => setOpenLoadsVisible((visible) => !visible)}>
          {openLoadsVisible ? "Hide open loads" : "View open loads"}<span aria-hidden="true">⌄</span>
        </button>
      </div>
      {openLoadsVisible && <ul className="open-loads-list">{unassignedLoads.map((load) => <li key={load.id}><strong>{load.id}</strong><span>{routeLabel(load.origin_city, load.origin_state, load.destination_city, load.destination_state)}</span><span>{load.committed ? "Committed" : "Non-committed"}</span><time>Due {formatDateTime(load.pickup_end)}</time></li>)}</ul>}
    </div>
  );
}

function PlanRow({ assignment, driver, load }: { assignment: Assignment; driver?: Driver; load?: Load }) {
  return (
    <tr>
      <td><strong>{assignment.driver_id}</strong><small>{driver?.name}</small></td>
      <td>{assignment.load_id}</td>
      <td>{load ? routeLabel(load.origin_city, load.origin_state, load.destination_city, load.destination_state) : "Route unavailable"}</td>
      <td>{formatDateTime(assignment.planned_pickup_at)}</td>
      <td>{formatDateTime(assignment.planned_delivery_at)}</td>
      <td>{assignment.deadhead_minutes} min</td>
      <td><span className="badge assigned">Assigned</span></td>
    </tr>
  );
}
